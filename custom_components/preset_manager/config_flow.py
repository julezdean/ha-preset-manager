"""Config, options and subentry flows for the Preset Mode.

One config entry is one preset mode: a set of modes plus the conditions
that decide which of them is active. Its modes are edited in the options flow,
and every preset - a device or scenario with its parameters - is a subentry of
the preset mode it follows.

A config entry can also be a *blueprint*: a list of parameter definitions
and nothing else, followed by any number of presets. Both edit that
list with the same steps, which is what ``ParameterListFlow`` is for; they only
differ in where the finished list goes.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from contextlib import nullcontext
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryFlow,
    OptionsFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from . import blueprints
from . import conditions as condition_helper
from .const import (
    BLUEPRINT_NONE,
    CONF_BLUEPRINT,
    CONF_CONDITIONS,
    CONF_DEFAULT,
    CONF_DEVICE_CLASS,
    CONF_DISPLAY_MODE,
    CONF_ENTRY_TYPE,
    CONF_ICON,
    CONF_KEY,
    CONF_MAX,
    CONF_MAX_LENGTH,
    CONF_MIN,
    CONF_MIN_LENGTH,
    CONF_MODES,
    CONF_NAME,
    CONF_OPTIONS,
    CONF_PARAMETERS,
    CONF_PATTERN,
    CONF_PRESET_MODE,
    CONF_SOURCE_ENTITY,
    CONF_STEP,
    CONF_TYPE,
    CONF_UNIT,
    DEFAULT_MODE_NAMES,
    DEFAULT_PRESET_MODE_NAME,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_TYPE_BLUEPRINT,
    ENTRY_TYPE_PRESET_MODE,
    ENTRY_VERSION,
    SUBENTRY_TYPE_PRESET,
)
from .models import (
    ModeDef,
    ParameterDef,
    PresetModeConfig,
    make_key,
    modes_to_data,
    parameters_to_data,
)
from .parameter_types import (
    DEFAULT_MAX,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MIN,
    DEFAULT_STEP,
    MODE_BOX,
    MODE_TEXT,
    NUMBER_MODES,
    TEXT_MODES,
    TYPE_BOOLEAN,
    TYPE_DATE,
    TYPE_DATETIME,
    TYPE_NUMBER,
    TYPE_TIME,
    ParameterValueError,
    allowed_units,
    device_class_keys,
    get_parameter_type,
    parameter_type_keys,
)
from .store import async_get_store

_LOGGER = logging.getLogger(__name__)

CONF_PARAMETER = "parameter"

#: Domains offered when picking the entity a preset mode follows. Any entity would
#: do - we only read its state - but an unfiltered picker is unusable.
SOURCE_ENTITY_DOMAINS = ["sensor", "select", "input_select", "input_text", "text"]

_NUMBER_BOX = selector.NumberSelector(
    selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, step="any")
)
_LENGTH_BOX = selector.NumberSelector(
    selector.NumberSelectorConfig(mode=selector.NumberSelectorMode.BOX, min=0, step=1)
)
#: Selector used for the default value of a type; text is the fallback.
_DEFAULT_SELECTORS: dict[str, Any] = {
    TYPE_BOOLEAN: selector.BooleanSelector,
    TYPE_DATETIME: selector.DateTimeSelector,
    TYPE_DATE: selector.DateSelector,
    TYPE_TIME: selector.TimeSelector,
}


# Shared helpers ---------------------------------------------------------------


def _preset_modes(hass: HomeAssistant) -> list[ConfigEntry]:
    """Return every preset mode, i.e. every entry that is not a set."""
    return blueprints.async_preset_modes(hass)


def _blueprint_selector(sets: list[ConfigEntry]) -> selector.SelectSelector:
    """Return the selector listing the blueprints, plus "none".

    "None" is an option of its own rather than an empty field: an empty optional
    field is not submitted at all, and a preset would have no way of saying that
    it wants to leave its set.
    """
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=BLUEPRINT_NONE, label="-"),
                *(
                    selector.SelectOptionDict(value=item.entry_id, label=item.title)
                    for item in sets
                ),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _mode_options(modes: list[ModeDef]) -> list[selector.SelectOptionDict]:
    """Return selector options for a list of modes."""
    return [
        selector.SelectOptionDict(value=mode.key, label=mode.name) for mode in modes
    ]


def _parameter_options(
    parameters: tuple[ParameterDef, ...],
) -> list[selector.SelectOptionDict]:
    """Return selector options for a list of parameters."""
    return [
        selector.SelectOptionDict(value=parameter.key, label=parameter.name)
        for parameter in parameters
    ]


def _modes_chips_schema(default: list[str] | None = None) -> vol.Schema:
    """Return the schema asking for a list of mode names."""
    return vol.Schema(
        {
            vol.Required(CONF_NAME): selector.TextSelector(),
            vol.Required(
                CONF_MODES,
                description={"suggested_value": default or DEFAULT_MODE_NAMES},
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=DEFAULT_MODE_NAMES,
                    multiple=True,
                    custom_value=True,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
        }
    )


def _modes_schema(modes: list[ModeDef]) -> vol.Schema:
    """Return the schema of the whole mode list.

    An object selector with ``multiple`` renders a sortable list: one row per
    mode with a drag handle, an edit button and a delete button. The order of
    the rows is both the priority of the conditions and the order of the options
    of the select entity.
    """
    return vol.Schema(
        {
            vol.Optional(
                CONF_MODES,
                description={"suggested_value": [mode.to_dict() for mode in modes]},
            ): selector.ObjectSelector(
                {
                    "multiple": True,
                    "label_field": CONF_NAME,
                    # Nested selectors have to be plain dicts: the object
                    # selector runs them through the selector factory, which
                    # rejects Selector instances.
                    "fields": {
                        CONF_NAME: {
                            "required": True,
                            "selector": {"text": {}},
                        },
                        CONF_CONDITIONS: {
                            "required": False,
                            "selector": {"condition": {}},
                        },
                        CONF_ICON: {
                            "required": False,
                            "selector": {"icon": {}},
                        },
                        # Carries the identity of a mode across renames; all
                        # stored values hang off it, so it must not be edited.
                        CONF_KEY: {
                            "required": False,
                            "selector": {"text": {"read_only": True}},
                        },
                    },
                }
            )
        }
    )


def _modes_from_input(
    user_input: Mapping[str, Any], existing: list[ModeDef]
) -> tuple[list[ModeDef] | None, str | None]:
    """Build the mode list from the submitted rows.

    Rows keep their key, so renaming a mode keeps its stored values. A row
    without a known key is a new mode and gets a fresh one.
    """
    rows = user_input.get(CONF_MODES) or []
    known = {mode.key for mode in existing}
    names = [str(row.get(CONF_NAME, "")).strip() for row in rows]
    if not rows or not all(names):
        return None, "no_modes"
    if len({name.casefold() for name in names}) != len(names):
        return None, "duplicate_mode"

    retained = [row.get(CONF_KEY) for row in rows if row.get(CONF_KEY) in known]
    if len(retained) != len(set(retained)):
        # The key field is read_only in the rendered form, but the form can be
        # edited in YAML, where it is not - and two rows carrying the same key
        # would share their stored values and collide in their unique ids.
        return None, "duplicate_mode_key"

    # Every key a row keeps is taken from the start, wherever that row sits.
    # Collecting them while walking the list would let a new row above a
    # renamed one be given the very key that row is about to keep.
    taken = set(retained)

    modes: list[ModeDef] = []
    for row, name in zip(rows, names, strict=True):
        key = row.get(CONF_KEY)
        if not key or key not in known:
            key = make_key(name, taken)
            taken.add(key)
        modes.append(
            ModeDef(
                key=key,
                name=name,
                icon=row.get(CONF_ICON) or None,
                conditions=tuple(
                    condition_helper.to_storage(row.get(CONF_CONDITIONS) or [])
                ),
            )
        )
    return modes, None


def _parameter_details_schema(
    type_key: str, defaults: Mapping[str, Any] | None = None
) -> vol.Schema:
    """Build the (type dependent) detail schema of a parameter."""
    parameter_type = get_parameter_type(type_key)
    defaults = defaults or {}
    fields: dict[Any, Any] = {}

    def add(conf_key: str, field: Any, *, fallback: Any = None) -> None:
        """Add an optional field pre-filled with its current value."""
        suggested = defaults.get(conf_key)
        if suggested is None:
            suggested = fallback
        fields[vol.Optional(conf_key, description={"suggested_value": suggested})] = (
            field
        )

    if parameter_type.has_field(CONF_MIN):
        add(CONF_MIN, _NUMBER_BOX, fallback=DEFAULT_MIN)
        add(CONF_MAX, _NUMBER_BOX, fallback=DEFAULT_MAX)
        add(CONF_STEP, _NUMBER_BOX, fallback=DEFAULT_STEP)

    if parameter_type.has_field(CONF_UNIT):
        add(CONF_UNIT, selector.TextSelector())

    if parameter_type.has_field(CONF_DEVICE_CLASS):
        add(
            CONF_DEVICE_CLASS,
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=device_class_keys(),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="device_class",
                    sort=True,
                )
            ),
        )

    if parameter_type.has_field(CONF_MIN_LENGTH):
        add(CONF_MIN_LENGTH, _LENGTH_BOX, fallback=0)
        add(CONF_MAX_LENGTH, _LENGTH_BOX, fallback=DEFAULT_MAX_LENGTH)
        add(CONF_PATTERN, selector.TextSelector())

    if parameter_type.has_field(CONF_DISPLAY_MODE):
        display_modes = NUMBER_MODES if type_key == TYPE_NUMBER else TEXT_MODES
        add(
            CONF_DISPLAY_MODE,
            selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=list(display_modes),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="display_mode",
                )
            ),
            fallback=MODE_BOX if type_key == TYPE_NUMBER else MODE_TEXT,
        )

    if parameter_type.has_field(CONF_OPTIONS):
        fields[
            vol.Required(
                CONF_OPTIONS,
                description={"suggested_value": defaults.get(CONF_OPTIONS, [])},
            )
        ] = selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[],
                multiple=True,
                custom_value=True,
                mode=selector.SelectSelectorMode.LIST,
            )
        )

    # The icon is not asked for here: it is a field of the parameter list.
    add(CONF_DEFAULT, _default_selector(type_key))

    return vol.Schema(fields)


def _default_selector(type_key: str) -> Any:
    """Return the selector used for the default value of a type."""
    if type_key == TYPE_NUMBER:
        return _NUMBER_BOX
    if factory := _DEFAULT_SELECTORS.get(type_key):
        return factory()
    return selector.TextSelector()


def _unit_options(details: Mapping[str, Any] | None) -> str:
    """Return the units the chosen device class accepts, for the error message."""
    units = allowed_units((details or {}).get(CONF_DEVICE_CLASS))
    return ", ".join(sorted(item for item in units if item)) if units else ""


def _build_parameter(
    key: str, name: str, type_key: str, details: Mapping[str, Any]
) -> ParameterDef:
    """Create a parameter definition from the flow input."""
    return ParameterDef(
        key=key,
        name=name,
        type=type_key,
        minimum=details.get(CONF_MIN),
        maximum=details.get(CONF_MAX),
        step=details.get(CONF_STEP),
        unit=details.get(CONF_UNIT) or None,
        device_class=details.get(CONF_DEVICE_CLASS) or None,
        display_mode=details.get(CONF_DISPLAY_MODE) or None,
        min_length=_as_int(details.get(CONF_MIN_LENGTH)),
        max_length=_as_int(details.get(CONF_MAX_LENGTH)),
        pattern=details.get(CONF_PATTERN) or None,
        options=tuple(details.get(CONF_OPTIONS) or ()),
        default=details.get(CONF_DEFAULT),
        icon=details.get(CONF_ICON) or None,
    ).with_type_defaults()


def _as_int(value: Any) -> int | None:
    """Return ``value`` as an int; the number selector hands out floats."""
    return None if value is None else int(value)


def _validate_parameter(parameter: ParameterDef) -> str | None:
    """Return an error key when the parameter definition is inconsistent."""
    parameter_type = get_parameter_type(parameter.type)
    if parameter_type.has_field(CONF_OPTIONS) and not parameter.options:
        return "no_options"
    if (
        parameter.minimum is not None
        and parameter.maximum is not None
        and parameter.minimum >= parameter.maximum
    ):
        return "invalid_range"
    if (
        parameter.min_length is not None
        and parameter.max_length is not None
        and parameter.min_length > parameter.max_length
    ):
        return "invalid_range"
    units = allowed_units(parameter.device_class)
    if units is not None and (parameter.unit or "") not in units:
        return "invalid_unit" if any(units) else "unit_not_allowed"
    if parameter.default is not None:
        try:
            parameter_type.coerce(parameter.default, parameter)
        except ParameterValueError:
            return "invalid_default"
    return None


def _parameter_row(parameter: ParameterDef) -> dict[str, Any]:
    """Return one row of the parameter list.

    Empty fields are left out: the object selector validates every field it is
    given against its own selector, and ``None`` is not a string.
    """
    row: dict[str, Any] = {
        CONF_KEY: parameter.key,
        CONF_NAME: parameter.name,
        CONF_TYPE: parameter.type,
    }
    if parameter.icon:
        row[CONF_ICON] = parameter.icon
    return row


def _parameters_schema(
    parameters: list[ParameterDef], *, allow_details: bool
) -> vol.Schema:
    """Return the schema of the whole parameter list.

    Like the mode list this is an object selector with ``multiple``: one row
    per parameter with a drag handle, an edit button and a delete button. The
    row only carries what every type has - the type specific details are asked
    for in :meth:`PresetSubentryFlowHandler.async_step_parameter_details`, which
    the flow enters for every new or retyped row and for the parameter picked in
    the optional field below the list.
    """
    schema = vol.Schema(
        {
            vol.Optional(
                CONF_PARAMETERS,
                description={
                    "suggested_value": [_parameter_row(item) for item in parameters]
                },
            ): selector.ObjectSelector(
                {
                    "multiple": True,
                    "label_field": CONF_NAME,
                    # Nested selectors have to be plain dicts: the object
                    # selector runs them through the selector factory, which
                    # rejects Selector instances.
                    "fields": {
                        CONF_NAME: {
                            "required": True,
                            "selector": {"text": {}},
                        },
                        CONF_TYPE: {
                            "required": True,
                            "selector": {
                                "select": {
                                    "options": parameter_type_keys(),
                                    "mode": "dropdown",
                                    "translation_key": "parameter_type",
                                }
                            },
                        },
                        CONF_ICON: {
                            "required": False,
                            "selector": {"icon": {}},
                        },
                        # Carries the identity of a parameter across renames;
                        # all stored values hang off it, so it must not change.
                        CONF_KEY: {
                            "required": False,
                            "selector": {"text": {"read_only": True}},
                        },
                    },
                }
            )
        }
    )
    if not allow_details:
        return schema
    return schema.extend(
        {
            vol.Optional(CONF_PARAMETER): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=_parameter_options(tuple(parameters)),
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            )
        }
    )


def _parameters_from_input(
    user_input: Mapping[str, Any], existing: list[ParameterDef]
) -> tuple[list[ParameterDef] | None, set[str], str | None]:
    """Build the parameter list from the submitted rows.

    Returns the parameters, the keys whose type specific details still have to
    be asked for, and an error key. A row keeps its key, so renaming a parameter
    keeps its entities and its stored values. A row whose type changed is
    rebuilt from scratch - the old range, options or pattern belong to the old
    type and would not fit the new one.
    """
    rows = user_input.get(CONF_PARAMETERS) or []
    known = {parameter.key: parameter for parameter in existing}
    names = [str(row.get(CONF_NAME, "")).strip() for row in rows]
    if not rows or not all(names):
        return None, set(), "no_parameters"
    if len({name.casefold() for name in names}) != len(names):
        return None, set(), "duplicate_parameter"

    retained = [row.get(CONF_KEY) for row in rows if row.get(CONF_KEY) in known]
    if len(retained) != len(set(retained)):
        # Same reason as for the modes: read_only only binds the rendered
        # form, and a duplicated row would share values and unique ids.
        return None, set(), "duplicate_parameter_key"

    # Keys that rows keep are taken before the first new key is made up.
    taken = set(retained)

    parameters: list[ParameterDef] = []
    incomplete: set[str] = set()
    for row, name in zip(rows, names, strict=True):
        key = row.get(CONF_KEY)
        current = known.get(key) if key else None
        if current is None:
            key = make_key(name, taken)
            taken.add(key)
        type_key = row.get(CONF_TYPE) or TYPE_NUMBER
        icon = row.get(CONF_ICON) or None
        if current is not None and current.type == type_key:
            parameters.append(replace(current, name=name, icon=icon))
            continue
        parameters.append(
            ParameterDef(
                key=str(key), name=name, type=type_key, icon=icon
            ).with_type_defaults()
        )
        incomplete.add(str(key))
    return parameters, incomplete, None


def _parameter_defaults(parameter: ParameterDef) -> dict[str, Any]:
    """Return the current details of a parameter as form defaults."""
    return {
        CONF_MIN: parameter.minimum,
        CONF_MAX: parameter.maximum,
        CONF_STEP: parameter.step,
        CONF_UNIT: parameter.unit,
        CONF_DEVICE_CLASS: parameter.device_class,
        CONF_DISPLAY_MODE: parameter.display_mode,
        CONF_MIN_LENGTH: parameter.min_length,
        CONF_MAX_LENGTH: parameter.max_length,
        CONF_PATTERN: parameter.pattern,
        CONF_OPTIONS: list(parameter.options),
        CONF_DEFAULT: parameter.default,
    }


def _modes_from_names(
    names: list[str],
) -> tuple[list[ModeDef] | None, str | None]:
    """Turn a list of names into mode definitions."""
    cleaned = [name.strip() for name in names if name.strip()]
    if not cleaned:
        return None, "no_modes"
    if len({name.casefold() for name in cleaned}) != len(cleaned):
        return None, "duplicate_mode"
    modes: list[ModeDef] = []
    for name in cleaned:
        key = make_key(name, [item.key for item in modes])
        modes.append(ModeDef(key=key, name=name))
    return modes, None


# Parameter editor -------------------------------------------------------------


class ParameterListFlow:
    """The parameter editor, shared by a preset and by a blueprint.

    Both own the same thing - one list of parameter definitions - and edit it
    the same way: a sortable list of rows carrying what every type has, plus one
    detail step per row whose type is new or changed. Only the two ends differ,
    which is what :meth:`_load_parameters` and :meth:`_async_parameters_done`
    are for.

    The steps return whatever the flow they are mixed into returns
    (``ConfigFlowResult`` for an entry, ``SubentryFlowResult`` for a preset);
    the mixin itself has no flow base class of its own to name one of them.
    """

    def __init__(self) -> None:
        """Initialise the editor state."""
        super().__init__()
        #: The parameter list being edited; loaded once per flow.
        self._parameters: list[ParameterDef] = []
        self._loaded = False
        #: Keys still waiting for their type specific details.
        self._pending: list[str] = []
        #: Keys whose type changed, so their stored values no longer fit.
        self._retyped: set[str] = set()

    def _load_parameters(self) -> list[ParameterDef]:
        """Return the parameters the flow starts out with."""
        return []

    async def _async_parameters_done(self) -> Any:
        """Write the finished parameter list back."""
        raise NotImplementedError

    def _existing_parameters(self) -> list[ParameterDef]:
        """Return the parameter list being edited.

        It is loaded once and then carried through every step, so nothing is
        written back before the whole flow is through: a ``select`` without
        options would otherwise be persisted half finished.
        """
        if not self._loaded:
            self._loaded = True
            self._parameters = self._load_parameters()
        return self._parameters

    async def async_step_manage_parameters(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Add, rename, reorder and delete parameters in one list."""
        current = self._existing_parameters()
        errors: dict[str, str] = {}
        if user_input is not None:
            parameters, incomplete, error = _parameters_from_input(user_input, current)
            if error:
                errors[CONF_PARAMETERS] = error
            else:
                assert parameters is not None
                # A retyped parameter keeps its key, so its stored values would
                # survive a change they no longer fit.
                self._retyped |= {
                    item.key for item in current if item.key in incomplete
                }
                self._parameters = parameters
                self._pending = [
                    item.key for item in parameters if item.key in incomplete
                ]
                chosen = user_input.get(CONF_PARAMETER)
                if (
                    chosen
                    and chosen not in self._pending
                    and any(item.key == chosen for item in parameters)
                ):
                    self._pending.append(chosen)
                return await self._async_next_parameter()

        return self.async_show_form(  # type: ignore[attr-defined]
            step_id="manage_parameters",
            data_schema=_parameters_schema(current, allow_details=bool(current)),
            errors=errors,
        )

    async def _async_next_parameter(self) -> Any:
        """Ask for the details of the next queued parameter, or finish."""
        if self._pending:
            return await self.async_step_parameter_details()
        return await self._async_parameters_done()

    @property
    def _pending_parameter(self) -> ParameterDef:
        """Return the parameter whose details are being asked for."""
        key = self._pending[0]
        return next(item for item in self._parameters if item.key == key)

    async def async_step_parameter_details(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Ask for the type specific details of one parameter."""
        current = self._pending_parameter
        errors: dict[str, str] = {}
        if user_input is not None:
            parameter = _build_parameter(
                current.key,
                current.name,
                current.type,
                # The icon belongs to the row, not to this form.
                {**user_input, CONF_ICON: current.icon},
            )
            if error := _validate_parameter(parameter):
                errors["base"] = error
            else:
                self._parameters = [
                    parameter if item.key == current.key else item
                    for item in self._parameters
                ]
                self._pending.pop(0)
                return await self._async_next_parameter()

        # On an error the form is redisplayed with what was entered, so a single
        # wrong field does not throw away everything else.
        defaults = _parameter_defaults(current)
        if user_input is not None:
            defaults.update(user_input)
        return self.async_show_form(  # type: ignore[attr-defined]
            step_id="parameter_details",
            data_schema=_parameter_details_schema(current.type, defaults),
            errors=errors,
            description_placeholders={
                "parameter": current.name,
                "units": _unit_options(defaults),
            },
        )


# Config flow ------------------------------------------------------------------


class PresetModeConfigFlow(ParameterListFlow, ConfigFlow, domain=DOMAIN):
    """Creates one preset mode - or one blueprint - per config entry."""

    VERSION = ENTRY_VERSION
    MINOR_VERSION = ENTRY_MINOR_VERSION

    def __init__(self) -> None:
        """Initialise the flow."""
        super().__init__()
        #: Name of the blueprint being created.
        self._name: str = ""

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the supported subentry types."""
        if blueprints.is_blueprint(config_entry):
            # A blueprint holds parameters, not presets.
            return {}
        return {SUBENTRY_TYPE_PRESET: PresetSubentryFlowHandler}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Return the options flow of a preset mode or of a blueprint."""
        if blueprints.is_blueprint(config_entry):
            return BlueprintOptionsFlow()
        return PresetModeOptionsFlow()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which of the two kinds of entry is being created."""
        return self.async_show_menu(
            step_id="user", menu_options=["preset_mode", "blueprint"]
        )

    async def async_step_preset_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the name and the modes of the preset mode."""
        errors: dict[str, str] = {}
        if user_input is not None:
            modes, error = _modes_from_names(user_input[CONF_MODES])
            if error:
                errors[CONF_MODES] = error
            else:
                assert modes is not None
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip(),
                    data={
                        CONF_ENTRY_TYPE: ENTRY_TYPE_PRESET_MODE,
                        CONF_MODES: modes_to_data(modes),
                    },
                )

        return self.async_show_form(
            step_id="preset_mode",
            data_schema=self.add_suggested_values_to_schema(
                _modes_chips_schema(), {CONF_NAME: DEFAULT_PRESET_MODE_NAME}
            ),
            errors=errors,
        )

    async def async_step_blueprint(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the name of the blueprint, then for its parameters."""
        if user_input is not None:
            self._name = user_input[CONF_NAME].strip()
            return await self.async_step_manage_parameters()

        return self.async_show_form(
            step_id="blueprint",
            data_schema=vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()}),
        )

    async def _async_parameters_done(self) -> ConfigFlowResult:
        """Create the blueprint from the finished list."""
        return self.async_create_entry(
            title=self._name,
            data={
                CONF_ENTRY_TYPE: ENTRY_TYPE_BLUEPRINT,
                CONF_PARAMETERS: parameters_to_data(self._parameters),
            },
        )


# Options flow -----------------------------------------------------------------


class PresetModeOptionsFlow(OptionsFlow):
    """Manages the modes and the settings of one preset mode.

    The modes live in the *data* of the config entry, not in its options: an
    option is something the user tweaks about an existing thing, while the
    modes are what the entry actually is.
    """

    @property
    def _current(self) -> PresetModeConfig:
        """Return the preset mode that is being configured."""
        entry = self.config_entry
        return PresetModeConfig.from_entry(entry.entry_id, entry.title, entry.data)

    def _save(
        self,
        updates: Mapping[str, Any] | None = None,
        *,
        title: str | None = None,
    ) -> ConfigFlowResult:
        """Write changes back to the config entry."""
        entry = self.config_entry
        data = dict(entry.data)
        data.update(updates or {})
        self.hass.config_entries.async_update_entry(
            entry, data=data, title=title if title is not None else entry.title
        )
        return self.async_create_entry(data={})

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Show the management menu of a preset mode."""
        return self.async_show_menu(
            step_id="init",
            menu_options=["manage_modes", "preset_mode_settings"],
        )

    async def async_step_manage_modes(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add, rename, reorder and delete modes, and set their conditions."""
        current = self._current
        errors: dict[str, str] = {}
        if user_input is not None:
            modes, error = _modes_from_input(user_input, list(current.modes))
            if error:
                errors[CONF_MODES] = error
            else:
                assert modes is not None
                return self._save({CONF_MODES: modes_to_data(modes)})

        return self.async_show_form(
            step_id="manage_modes",
            data_schema=_modes_schema(list(current.modes)),
            errors=errors,
        )

    async def async_step_preset_mode_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Change the name and the entity the preset mode follows."""
        current = self._current
        if user_input is not None:
            return self._save(
                {CONF_SOURCE_ENTITY: user_input.get(CONF_SOURCE_ENTITY) or None},
                title=user_input[CONF_NAME].strip(),
            )

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, description={"suggested_value": current.name}
                ): selector.TextSelector(),
                vol.Optional(
                    CONF_SOURCE_ENTITY,
                    description={"suggested_value": current.source_entity},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SOURCE_ENTITY_DOMAINS)
                ),
            }
        )
        return self.async_show_form(step_id="preset_mode_settings", data_schema=schema)


# Blueprint options flow ---------------------------------------------------


class BlueprintOptionsFlow(ParameterListFlow, OptionsFlow):
    """Edits the parameters of one blueprint.

    Everything a set has is its parameters, so the options flow is the parameter
    editor and nothing else - a menu with one entry would only add a click. The
    name is the title of the config entry and is renamed where every entry is.
    """

    def _load_parameters(self) -> list[ParameterDef]:
        """Return the parameters stored on the set."""
        return [
            ParameterDef.from_dict(item)
            for item in self.config_entry.data.get(CONF_PARAMETERS, [])
        ]

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Open the parameter list right away."""
        return await self.async_step_manage_parameters(user_input)

    async def _async_parameters_done(self) -> ConfigFlowResult:
        """Write the parameters back and let every bound preset follow.

        Writing the entry fires its update listener, which reloads the preset_modes
        of the presets following this set; they read the new list on the way up.
        """
        entry = self.config_entry
        blueprints.async_forget_parameters(self.hass, entry.entry_id, self._retyped)
        self.hass.config_entries.async_update_entry(
            entry,
            data={
                **entry.data,
                CONF_PARAMETERS: parameters_to_data(self._parameters),
            },
        )
        return self.async_create_entry(data={})


# Instance subentry ------------------------------------------------------------


class PresetSubentryFlowHandler(ParameterListFlow, ConfigSubentryFlow):
    """Creates and reconfigures a single preset."""

    def __init__(self) -> None:
        """Initialise the subentry flow."""
        super().__init__()
        self._name: str = ""
        #: Blueprint the new preset is to follow, if any.
        self._blueprint: str | None = None

    @property
    def _entry(self) -> ConfigEntry:
        return self._get_entry()

    @property
    def _bound_to(self) -> str | None:
        """Return the blueprint this preset follows, if any."""
        if self.source != "reconfigure":
            return self._blueprint
        return self._get_reconfigure_subentry().data.get(CONF_BLUEPRINT)

    # Creation ----------------------------------------------------------------

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the name of the new preset, and for a blueprint.

        The preset mode is not asked for: the preset is created inside the
        preset mode it is added to. A blueprint is only offered when there is
        one; picking it skips the parameter editor for good.
        """
        available = blueprints.async_blueprints(self.hass)
        if user_input is not None:
            self._name = user_input[CONF_NAME].strip()
            chosen = user_input.get(CONF_BLUEPRINT)
            if chosen and chosen != BLUEPRINT_NONE:
                self._blueprint = chosen
                return await self._async_parameters_done()
            return await self.async_step_manage_parameters()

        schema = vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()})
        if available:
            schema = schema.extend(
                {
                    vol.Optional(
                        CONF_BLUEPRINT,
                        description={"suggested_value": BLUEPRINT_NONE},
                    ): _blueprint_selector(available)
                }
            )
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            description_placeholders={"preset_mode": self._entry.title},
        )

    # Parameters --------------------------------------------------------------

    def _load_parameters(self) -> list[ParameterDef]:
        """Return the parameters the preset starts out with.

        On a reconfiguration that is the stored list; while creating a preset it
        is empty.
        """
        if self.source != "reconfigure":
            return []
        subentry = self._get_reconfigure_subentry()
        return [
            ParameterDef.from_dict(item)
            for item in subentry.data.get(CONF_PARAMETERS, [])
        ]

    async def async_step_manage_parameters(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add, rename, reorder and delete parameters in one list."""
        if self._bound_to is not None:
            # The parameters belong to the set; editing them here would be a
            # change the next update of that set silently took back.
            return self.async_abort(reason="blueprint_locked")
        return await super().async_step_manage_parameters(user_input)

    async def _async_parameters_done(self) -> SubentryFlowResult:
        """Write the finished preset back."""
        if self.source != "reconfigure":
            return self.async_create_entry(title=self._name, data=self._preset_data())
        if self._retyped and (store := async_get_store(self.hass)) is not None:
            subentry = self._get_reconfigure_subentry()
            for key in self._retyped:
                store.remove_parameter(subentry.subentry_id, key)
        return self._async_save_reconfigure(parameters=self._parameters)

    def _preset_data(self) -> dict[str, Any]:
        """Return the subentry data of a new preset.

        A preset following a blueprint stores the set and nothing else - its
        parameters are read from there on every setup, so a copy could only ever
        be a copy that goes stale.
        """
        if self._blueprint is not None:
            return {CONF_BLUEPRINT: self._blueprint}
        return {CONF_PARAMETERS: parameters_to_data(self._parameters)}

    # Reconfiguration ---------------------------------------------------------

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show the reconfiguration menu of a preset.

        A preset following a blueprint has no parameter editor of its own -
        the entry that would open it is the one that leads out of the set.
        """
        options = ["manage_parameters"]
        if self._bound_to is not None:
            options = []
        if self._bound_to is not None or blueprints.async_blueprints(self.hass):
            options.append("blueprint")
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=[*options, "rename_preset", "assign_preset_mode"],
        )

    async def async_step_blueprint(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Attach the preset to a blueprint, or detach it from one.

        Attaching replaces the parameters of the preset with those of the set;
        detaching keeps the ones it currently has, as its own. Values survive
        wherever a parameter key survives - the rest is dropped on the reload,
        the same way a deleted parameter is.
        """
        subentry = self._get_reconfigure_subentry()
        current = subentry.data.get(CONF_BLUEPRINT) or BLUEPRINT_NONE
        if user_input is not None:
            chosen = user_input[CONF_BLUEPRINT]
            if chosen == current:
                return self.async_abort(reason="reconfigure_successful")
            data = {
                key: value
                for key, value in subentry.data.items()
                if key not in (CONF_PARAMETERS, CONF_BLUEPRINT)
            }
            if chosen == BLUEPRINT_NONE:
                resolved = blueprints.async_resolve_preset_data(
                    self.hass, subentry.data
                )
                data[CONF_PARAMETERS] = list(resolved.get(CONF_PARAMETERS, []))
            else:
                data[CONF_BLUEPRINT] = chosen
            return self.async_update_and_abort(self._entry, subentry, data=data)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_BLUEPRINT, description={"suggested_value": current}
                ): _blueprint_selector(blueprints.async_blueprints(self.hass))
            }
        )
        return self.async_show_form(step_id="blueprint", data_schema=schema)

    def _async_save_reconfigure(
        self,
        *,
        parameters: list[ParameterDef] | None = None,
        title: str | None = None,
        **updates: Any,
    ) -> SubentryFlowResult:
        """Write the changed preset configuration back to the subentry."""
        subentry = self._get_reconfigure_subentry()
        data = dict(subentry.data)
        data.update(updates)
        if parameters is not None:
            data[CONF_PARAMETERS] = parameters_to_data(parameters)
        return self.async_update_and_abort(
            self._entry,
            subentry,
            data=data,
            title=title if title is not None else subentry.title,
        )

    async def async_step_rename_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Rename the preset."""
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            return self._async_save_reconfigure(title=user_input[CONF_NAME].strip())

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, description={"suggested_value": subentry.title}
                ): selector.TextSelector()
            }
        )
        return self.async_show_form(step_id="rename_preset", data_schema=schema)

    async def async_step_assign_preset_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Attach the preset to another preset mode."""
        subentry = self._get_reconfigure_subentry()
        entry = self._entry
        if user_input is not None:
            target_id = user_input[CONF_PRESET_MODE]
            if target_id == entry.entry_id:
                return self.async_abort(reason="reconfigure_successful")
            return self._async_move_preset(
                subentry, target_id, title=subentry.title, data=subentry.data
            )

        schema = vol.Schema(
            {
                vol.Required(CONF_PRESET_MODE, default=entry.entry_id): (
                    selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=item.entry_id, label=item.title
                                )
                                for item in _preset_modes(self.hass)
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                )
            }
        )
        return self.async_show_form(step_id="assign_preset_mode", data_schema=schema)

    @callback
    def _async_move_preset(
        self,
        subentry: ConfigSubentry,
        target_entry_id: str,
        *,
        title: str,
        data: Mapping[str, Any],
    ) -> SubentryFlowResult:
        """Move a preset to another preset mode.

        The subentry is recreated under the *same* subentry id, which is what
        every entity unique id, every device identifier and every stored value
        is keyed by. Home Assistant restores the entity ids of the briefly
        removed entities from its registry, so the move keeps the history and
        the configured values of the preset.
        """
        target = self.hass.config_entries.async_get_entry(target_entry_id)
        if target is None:
            return self.async_abort(reason="unknown_preset_mode")
        moved = ConfigSubentry(
            data=MappingProxyType(dict(data)),
            subentry_id=subentry.subentry_id,
            subentry_type=subentry.subentry_type,
            title=title,
            unique_id=subentry.unique_id,
        )
        store = async_get_store(self.hass)
        with (
            nullcontext()
            if store is None
            else store.protect_preset(subentry.subentry_id)
        ):
            self.hass.config_entries.async_remove_subentry(
                self._entry, subentry.subentry_id
            )
            self.hass.config_entries.async_add_subentry(target, moved)
        return self.async_abort(reason="preset_moved")
