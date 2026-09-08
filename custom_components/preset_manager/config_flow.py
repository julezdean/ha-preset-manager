"""Config and subentry flows of the Preset Manager.

Every object is a subentry of the hub that holds its kind (see ``hubs``), so
there is one subentry flow per kind and no options flow at all: a hub holds
nothing to configure, and everything an object has is edited in its own
reconfigure flow.

The config flow is the way in: it asks which kind of object to create, and the
hub of that kind appears with the first one. A preset and a blueprint edit the
same thing - one list of parameter definitions - which is what
``ParameterListFlow`` is for; they only differ in where the finished list goes.
"""

from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import replace
from types import MappingProxyType
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    SOURCE_RECONFIGURE,
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    ConfigSubentry,
    ConfigSubentryData,
    ConfigSubentryFlow,
    SubentryFlowResult,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.util.ulid import ulid_now

from . import conditions as condition_helper
from . import following, hubs
from .const import (
    BLUEPRINT_NONE,
    CONF_BLUEPRINT,
    CONF_CONDITIONS,
    CONF_COPY_NAME,
    CONF_DEFAULT,
    CONF_DEVICE_CLASS,
    CONF_DISPLAY_MODE,
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
    CONF_PRESETS,
    CONF_SOURCE_ENTITY,
    CONF_STEP,
    CONF_TYPE,
    CONF_UNIT,
    DEFAULT_MODE_NAMES,
    DEFAULT_PRESET_MODE_NAME,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_VERSION,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
    HUB_SUBENTRY_TYPES,
    HUB_TITLES,
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

#: Value of a reference selector standing for "follows nothing".
REFERENCE_NONE = BLUEPRINT_NONE

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


def _chosen(value: str | None) -> str | None:
    """Return what was picked, or ``None`` for "nothing"."""
    return None if value in (None, "", REFERENCE_NONE) else value


def _reference_selector(
    objects: Mapping[str, ConfigSubentry],
) -> selector.SelectSelector:
    """Return the selector listing objects to follow, plus "none".

    "None" is an option of its own rather than an empty field: an empty
    optional field is not submitted at all, and a preset would have no way of
    saying that it wants to leave what it follows.
    """
    return selector.SelectSelector(
        selector.SelectSelectorConfig(
            options=[
                selector.SelectOptionDict(value=REFERENCE_NONE, label="-"),
                *(
                    selector.SelectOptionDict(value=key, label=item.title)
                    for key, item in objects.items()
                ),
            ],
            mode=selector.SelectSelectorMode.DROPDOWN,
        )
    )


def _preset_schema(hass: HomeAssistant) -> vol.Schema:
    """Return the schema asking for a new preset and what it follows."""
    schema = vol.Schema(
        {
            vol.Required(CONF_NAME): selector.TextSelector(),
            vol.Optional(
                CONF_PRESET_MODE, description={"suggested_value": REFERENCE_NONE}
            ): _reference_selector(hubs.async_preset_modes(hass)),
        }
    )
    if blueprints := hubs.async_blueprints(hass):
        # Offered only when there is one; picking it skips the parameters.
        schema = schema.extend(
            {
                vol.Optional(
                    CONF_BLUEPRINT, description={"suggested_value": REFERENCE_NONE}
                ): _reference_selector(blueprints)
            }
        )
    return schema


def _preset_data(
    preset_mode: str | None,
    blueprint: str | None,
    parameters: list[ParameterDef],
) -> dict[str, Any]:
    """Return the subentry data of a new preset.

    A preset following a blueprint stores the reference and nothing else - its
    parameters are read from there on every setup, so a copy could only ever
    drift. Its modes are not stored either: they come from its preset mode.
    """
    data: dict[str, Any] = {}
    if preset_mode is not None:
        data[CONF_PRESET_MODE] = preset_mode
    if blueprint is not None:
        data[CONF_BLUEPRINT] = blueprint
    else:
        data[CONF_PARAMETERS] = parameters_to_data(parameters)
    return data


def _modes_of(hass: HomeAssistant, preset_mode_id: str | None) -> list[dict[str, Any]]:
    """Return the modes of a preset mode, for a preset about to leave it."""
    subentry = hubs.async_object(hass, HUB_PRESET_MODES, preset_mode_id)
    if subentry is None:
        return []
    return [dict(item) for item in subentry.data.get(CONF_MODES, [])]


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


class PresetManagerConfigFlow(ParameterListFlow, ConfigFlow, domain=DOMAIN):
    """Creates objects, and the hub that holds them the first time round.

    The user never creates a hub: they add a preset mode, a preset or a
    blueprint, and the hub of that kind appears with it. Once it is there the
    same object can also be added from the hub itself, which is the path Home
    Assistant offers on the integration page.
    """

    VERSION = ENTRY_VERSION
    MINOR_VERSION = ENTRY_MINOR_VERSION

    def __init__(self) -> None:
        """Initialise the flow."""
        super().__init__()
        #: Which kind of object is being created, once the user picked one.
        self._kind: str = ""
        #: Name of the object being created.
        self._name: str = ""
        #: The preset mode and the blueprint a new preset follows.
        self._preset_mode: str | None = None
        self._blueprint: str | None = None

    @classmethod
    @callback
    def async_get_supported_subentry_types(
        cls, config_entry: ConfigEntry
    ) -> dict[str, type[ConfigSubentryFlow]]:
        """Return the one subentry type the hub holds."""
        handlers: dict[str, type[ConfigSubentryFlow]] = {
            HUB_PRESET_MODES: PresetModeSubentryFlowHandler,
            HUB_PRESETS: PresetSubentryFlowHandler,
            HUB_BLUEPRINTS: BlueprintSubentryFlowHandler,
        }
        kind = hubs.hub_kind(config_entry)
        if kind is None:
            return {}
        return {HUB_SUBENTRY_TYPES[kind]: handlers[kind]}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask which kind of object is being created."""
        return self.async_show_menu(
            step_id="user", menu_options=["preset_mode", "preset", "blueprint"]
        )

    # One object per kind ------------------------------------------------------

    async def async_step_preset_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the name and the modes of a preset mode."""
        errors: dict[str, str] = {}
        if user_input is not None:
            modes, error = _modes_from_names(user_input[CONF_MODES])
            if error:
                errors[CONF_MODES] = error
            else:
                assert modes is not None
                return await self._async_add(
                    HUB_PRESET_MODES,
                    user_input[CONF_NAME].strip(),
                    {CONF_MODES: modes_to_data(modes)},
                )

        return self.async_show_form(
            step_id="preset_mode",
            data_schema=self.add_suggested_values_to_schema(
                _modes_chips_schema(), {CONF_NAME: DEFAULT_PRESET_MODE_NAME}
            ),
            errors=errors,
        )

    async def async_step_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the name of a preset and what it follows."""
        if user_input is not None:
            self._kind = HUB_PRESETS
            self._name = user_input[CONF_NAME].strip()
            self._preset_mode = _chosen(user_input.get(CONF_PRESET_MODE))
            self._blueprint = _chosen(user_input.get(CONF_BLUEPRINT))
            if self._blueprint is not None:
                return await self._async_parameters_done()
            return await self.async_step_manage_parameters()

        return self.async_show_form(
            step_id="preset", data_schema=_preset_schema(self.hass)
        )

    async def async_step_blueprint(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for the name of a blueprint, then for its parameters."""
        if user_input is not None:
            self._kind = HUB_BLUEPRINTS
            self._name = user_input[CONF_NAME].strip()
            return await self.async_step_manage_parameters()

        return self.async_show_form(
            step_id="blueprint",
            data_schema=vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()}),
        )

    async def _async_parameters_done(self) -> ConfigFlowResult:
        """Create the preset or the blueprint from the finished list."""
        if self._kind == HUB_PRESETS:
            return await self._async_add(
                HUB_PRESETS,
                self._name,
                _preset_data(self._preset_mode, self._blueprint, self._parameters),
            )
        return await self._async_add(
            HUB_BLUEPRINTS,
            self._name,
            {CONF_PARAMETERS: parameters_to_data(self._parameters)},
        )

    async def _async_add(
        self, kind: str, title: str, data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Put a new object into its hub, creating the hub with it if needed."""
        hub = hubs.async_hub(self.hass, kind)
        if hub is None:
            await self.async_set_unique_id(kind)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=HUB_TITLES[kind],
                data={},
                subentries=[
                    ConfigSubentryData(
                        data=data,
                        subentry_type=HUB_SUBENTRY_TYPES[kind],
                        title=title,
                        unique_id=None,
                    )
                ],
            )

        self.hass.config_entries.async_add_subentry(
            hub,
            ConfigSubentry(
                data=MappingProxyType(data),
                subentry_type=HUB_SUBENTRY_TYPES[kind],
                title=title,
                unique_id=None,
            ),
        )
        return self.async_abort(reason=f"{kind}_added")


# Subentry flows ---------------------------------------------------------------


class RenameFlow(ConfigSubentryFlow):
    """Renames one object, whatever kind it is.

    Its own menu entry everywhere rather than a field on the settings of the
    kind that happens to have settings: renaming is the one thing every object
    can do, and looking for it in a different place per kind is the kind of
    inconsistency a user only notices by not finding it.
    """

    async def async_step_rename(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for a new name and write it back."""
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            return self.async_update_and_abort(
                self._get_entry(), subentry, title=user_input[CONF_NAME].strip()
            )

        return self.async_show_form(
            step_id="rename",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, description={"suggested_value": subentry.title}
                    ): selector.TextSelector()
                }
            ),
        )


class AssignPresetsFlow(ConfigSubentryFlow):
    """Edits from the other side which presets follow this object.

    The reference lives on the preset either way - this writes the same key
    that the preset's own menu writes, only for several presets at once. It is
    the only place that answers "what follows this?" without opening every
    preset in turn.
    """

    #: The key on the preset that this object is referenced by.
    reference: str

    @callback
    def _async_follow(self, preset: ConfigSubentry, subentry_id: str) -> None:
        """Let one preset follow this object."""
        following.async_follow(self.hass, preset, self.reference, subentry_id)

    @callback
    def _async_unfollow(self, preset: ConfigSubentry) -> None:
        """Let one preset stop following this object."""
        raise NotImplementedError

    def _label(self, preset: ConfigSubentry) -> str:
        """Return the label of one preset in the picker."""
        raise NotImplementedError

    async def async_step_assign_presets(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add presets to this object and take others off it."""
        subentry = self._get_reconfigure_subentry()
        presets = hubs.async_presets(self.hass)
        mine = {
            preset_id
            for preset_id, preset in presets.items()
            if preset.data.get(self.reference) == subentry.subentry_id
        }

        if user_input is not None:
            chosen = set(user_input.get(CONF_PRESETS) or ())
            for preset_id in chosen - mine:
                self._async_follow(presets[preset_id], subentry.subentry_id)
            for preset_id in mine - chosen:
                self._async_unfollow(presets[preset_id])
            return self.async_abort(reason="reconfigure_successful")

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_PRESETS, description={"suggested_value": sorted(mine)}
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=[
                            selector.SelectOptionDict(
                                value=preset_id, label=self._label(preset)
                            )
                            for preset_id, preset in presets.items()
                        ],
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN,
                        sort=True,
                    )
                )
            }
        )
        return self.async_show_form(
            step_id="assign_presets",
            data_schema=schema,
            description_placeholders={"name": subentry.title},
        )


def _followed_title(
    hass: HomeAssistant, preset: ConfigSubentry, key: str, kind: str
) -> str | None:
    """Return the title of what a preset follows, if it follows anything."""
    subentry = hubs.async_object(hass, kind, preset.data.get(key))
    return None if subentry is None else subentry.title


class DuplicateFlow(RenameFlow):
    """Copies one object, whatever kind it is.

    Everything an object is stands in its subentry data, so a copy is that
    data under a new id - which is also why the copy is offered where the
    object is, rather than as a variant of the "add" flow: there is nothing
    left to ask for but the name.
    """

    def _duplicate_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return the data of the copy."""
        return data

    @callback
    def _async_duplicated(self, source_id: str, copy_id: str) -> None:
        """React to the copy having been created."""

    async def async_step_duplicate(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the name of the copy, then create it."""
        subentry = self._get_reconfigure_subentry()
        if user_input is not None:
            copy_id = ulid_now()
            # Everything the copy brings along is written before it exists:
            # adding the subentry sets its entities up, and they read what is
            # in the store at that moment.
            self._async_duplicated(subentry.subentry_id, copy_id)
            self.hass.config_entries.async_add_subentry(
                self._get_entry(),
                ConfigSubentry(
                    data=MappingProxyType(self._duplicate_data(dict(subentry.data))),
                    subentry_id=copy_id,
                    subentry_type=subentry.subentry_type,
                    title=user_input[CONF_COPY_NAME].strip(),
                    unique_id=None,
                ),
            )
            return self.async_abort(reason="duplicated")

        return self.async_show_form(
            step_id="duplicate",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COPY_NAME,
                        description={"suggested_value": f"{subentry.title} 2"},
                    ): selector.TextSelector()
                }
            ),
            description_placeholders={"name": subentry.title},
        )


class PresetModeSubentryFlowHandler(AssignPresetsFlow, DuplicateFlow):
    """Creates and edits one preset mode.

    Its modes live in the *data* of the subentry, not in options: an option is
    something the user tweaks about an existing thing, while the modes are what
    the preset mode actually is.
    """

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the name and the modes of a new preset mode."""
        errors: dict[str, str] = {}
        if user_input is not None:
            modes, error = _modes_from_names(user_input[CONF_MODES])
            if error:
                errors[CONF_MODES] = error
            else:
                assert modes is not None
                return self.async_create_entry(
                    title=user_input[CONF_NAME].strip(),
                    data={CONF_MODES: modes_to_data(modes)},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                _modes_chips_schema(), {CONF_NAME: DEFAULT_PRESET_MODE_NAME}
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show what can be changed about a preset mode."""
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=[
                "manage_modes",
                "rename",
                "assign_presets",
                "preset_mode_settings",
                "duplicate",
            ],
        )

    reference = CONF_PRESET_MODE

    @callback
    def _async_unfollow(self, preset: ConfigSubentry) -> None:
        """Take a preset off this preset mode, with its modes.

        It keeps them so that its editors keep existing - one entity per mode
        and parameter - and a repair issue asks for a new preset mode.
        """
        following.async_unfollow_preset_mode(
            self.hass, preset, modes_to_data(self._current.modes)
        )

    def _label(self, preset: ConfigSubentry) -> str:
        """Name the preset mode a preset already follows, if it is another."""
        title = _followed_title(self.hass, preset, CONF_PRESET_MODE, HUB_PRESET_MODES)
        if title is None or preset.data.get(CONF_PRESET_MODE) == (
            self._get_reconfigure_subentry().subentry_id
        ):
            return preset.title
        return f"{preset.title} ({title})"

    def _duplicate_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """Return the data of the copy, without the entity it follows.

        Two preset modes reading the same entity would always hold the same
        mode, which is one preset mode with two names. The copy is manual
        until it is given a source of its own.
        """
        return {key: value for key, value in data.items() if key != CONF_SOURCE_ENTITY}

    @property
    def _current(self) -> PresetModeConfig:
        """Return the preset mode being configured."""
        subentry = self._get_reconfigure_subentry()
        return PresetModeConfig.from_subentry(
            subentry.subentry_id, subentry.title, subentry.data
        )

    def _save(
        self,
        updates: Mapping[str, Any] | None = None,
        *,
        title: str | None = None,
    ) -> SubentryFlowResult:
        """Write changes back to the subentry."""
        subentry = self._get_reconfigure_subentry()
        data = dict(subentry.data)
        data.update(updates or {})
        return self.async_update_and_abort(
            self._get_entry(),
            subentry,
            data=data,
            title=title if title is not None else subentry.title,
        )

    async def async_step_manage_modes(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
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
    ) -> SubentryFlowResult:
        """Change the entity the preset mode follows."""
        current = self._current
        if user_input is not None:
            return self._save(
                {CONF_SOURCE_ENTITY: user_input.get(CONF_SOURCE_ENTITY) or None}
            )

        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_SOURCE_ENTITY,
                    description={"suggested_value": current.source_entity},
                ): selector.EntitySelector(
                    selector.EntitySelectorConfig(domain=SOURCE_ENTITY_DOMAINS)
                )
            }
        )
        return self.async_show_form(step_id="preset_mode_settings", data_schema=schema)


class BlueprintSubentryFlowHandler(ParameterListFlow, AssignPresetsFlow, DuplicateFlow):
    """Creates and edits one blueprint."""

    def __init__(self) -> None:
        """Initialise the flow."""
        super().__init__()
        self._name: str = ""

    def _load_parameters(self) -> list[ParameterDef]:
        """Return the parameters the blueprint starts out with."""
        if self.source != SOURCE_RECONFIGURE:
            return []
        subentry = self._get_reconfigure_subentry()
        return [
            ParameterDef.from_dict(item)
            for item in subentry.data.get(CONF_PARAMETERS, [])
        ]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the name of a new blueprint, then for its parameters."""
        if user_input is not None:
            self._name = user_input[CONF_NAME].strip()
            return await self.async_step_manage_parameters()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_NAME): selector.TextSelector()}),
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show what can be done with a blueprint."""
        return self.async_show_menu(
            step_id="reconfigure",
            menu_options=["manage_parameters", "rename", "assign_presets", "duplicate"],
        )

    reference = CONF_BLUEPRINT

    @callback
    def _async_unfollow(self, preset: ConfigSubentry) -> None:
        """Take a preset off this blueprint, with its parameters as its own."""
        subentry = self._get_reconfigure_subentry()
        following.async_unfollow_blueprint(
            self.hass, preset, subentry.data.get(CONF_PARAMETERS, [])
        )

    def _label(self, preset: ConfigSubentry) -> str:
        """Name the blueprint a preset already follows, if it is another."""
        title = _followed_title(self.hass, preset, CONF_BLUEPRINT, HUB_BLUEPRINTS)
        if title is None or preset.data.get(CONF_BLUEPRINT) == (
            self._get_reconfigure_subentry().subentry_id
        ):
            return preset.title
        return f"{preset.title} ({title})"

    async def _async_parameters_done(self) -> SubentryFlowResult:
        """Write the finished parameter list back."""
        data = {CONF_PARAMETERS: parameters_to_data(self._parameters)}
        if self.source != SOURCE_RECONFIGURE:
            return self.async_create_entry(title=self._name, data=data)

        subentry = self._get_reconfigure_subentry()
        # A retyped parameter keeps its key, so the values stored for it under
        # every preset following this blueprint no longer fit.
        following.async_forget_parameters(
            self.hass, subentry.subentry_id, self._retyped
        )
        return self.async_update_and_abort(self._get_entry(), subentry, data=data)


class PresetSubentryFlowHandler(ParameterListFlow, DuplicateFlow):
    """Creates and edits one preset."""

    def __init__(self) -> None:
        """Initialise the flow."""
        super().__init__()
        self._name: str = ""
        self._preset_mode: str | None = None
        self._blueprint: str | None = None

    @property
    def _bound_to(self) -> str | None:
        """Return the blueprint the preset follows, if any."""
        if self.source != SOURCE_RECONFIGURE:
            return self._blueprint
        return self._get_reconfigure_subentry().data.get(CONF_BLUEPRINT) or None

    def _load_parameters(self) -> list[ParameterDef]:
        """Return the parameters the preset starts out with."""
        if self.source != SOURCE_RECONFIGURE:
            return []
        subentry = self._get_reconfigure_subentry()
        return [
            ParameterDef.from_dict(item)
            for item in subentry.data.get(CONF_PARAMETERS, [])
        ]

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Ask for the name of the preset and for what it follows.

        A preset mode is offered but not required: a preset without one keeps
        everything except its active mode, and can be assigned one later.
        """
        if user_input is not None:
            self._name = user_input[CONF_NAME].strip()
            self._preset_mode = _chosen(user_input.get(CONF_PRESET_MODE))
            self._blueprint = _chosen(user_input.get(CONF_BLUEPRINT))
            if self._blueprint is not None:
                # Picking a blueprint skips the parameter editor for good.
                return await self._async_parameters_done()
            return await self.async_step_manage_parameters()

        return self.async_show_form(
            step_id="user", data_schema=_preset_schema(self.hass)
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Show what can be changed about a preset."""
        options = [] if self._bound_to is not None else ["manage_parameters"]
        options.append("rename")
        options.append("assign_preset_mode")
        if self._bound_to is not None or hubs.async_blueprints(self.hass):
            options.append("assign_blueprint")
        options.append("duplicate")
        return self.async_show_menu(step_id="reconfigure", menu_options=options)

    @callback
    def _async_duplicated(self, source_id: str, copy_id: str) -> None:
        """Hand the copy the values of the preset it was made from.

        Without them the copy is the empty shell of a preset - and filling one
        in is the work that made a copy worth having.
        """
        if (store := async_get_store(self.hass)) is not None:
            store.copy_preset(source_id, copy_id)

    async def async_step_assign_preset_mode(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Let the preset follow another preset mode, or none.

        The modes it kept from a deleted preset mode go with the assignment:
        from then on they come from the new one, and a snapshot left lying
        around would only be read again if that one disappeared as well.
        """
        subentry = self._get_reconfigure_subentry()
        current = subentry.data.get(CONF_PRESET_MODE)
        if user_input is not None:
            chosen = _chosen(user_input.get(CONF_PRESET_MODE))
            if chosen == current:
                return self.async_abort(reason="reconfigure_successful")
            data = {
                key: value
                for key, value in subentry.data.items()
                if key not in (CONF_PRESET_MODE, CONF_MODES)
            }
            if chosen is not None:
                data[CONF_PRESET_MODE] = chosen
            else:
                # Keeping the modes is what keeps the editors of the preset.
                data[CONF_MODES] = _modes_of(self.hass, current)
            return self.async_update_and_abort(self._get_entry(), subentry, data=data)

        return self.async_show_form(
            step_id="assign_preset_mode",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_PRESET_MODE,
                        description={"suggested_value": current or REFERENCE_NONE},
                    ): _reference_selector(hubs.async_preset_modes(self.hass))
                }
            ),
        )

    async def async_step_assign_blueprint(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Let the preset follow a blueprint, or none.

        Leaving a blueprint keeps its parameters as the preset's own, so the
        preset is editable again without losing anything.
        """
        subentry = self._get_reconfigure_subentry()
        current = subentry.data.get(CONF_BLUEPRINT)
        if user_input is not None:
            chosen = _chosen(user_input.get(CONF_BLUEPRINT))
            if chosen == current:
                return self.async_abort(reason="reconfigure_successful")
            data = {
                key: value
                for key, value in subentry.data.items()
                if key not in (CONF_PARAMETERS, CONF_BLUEPRINT)
            }
            if chosen is not None:
                data[CONF_BLUEPRINT] = chosen
            else:
                resolved = hubs.async_resolve_preset_data(self.hass, subentry.data)
                data[CONF_PARAMETERS] = list(resolved.get(CONF_PARAMETERS, []))
            return self.async_update_and_abort(self._get_entry(), subentry, data=data)

        return self.async_show_form(
            step_id="assign_blueprint",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BLUEPRINT,
                        description={"suggested_value": current or REFERENCE_NONE},
                    ): _reference_selector(hubs.async_blueprints(self.hass))
                }
            ),
        )

    async def async_step_manage_parameters(
        self, user_input: dict[str, Any] | None = None
    ) -> SubentryFlowResult:
        """Add, rename, reorder and delete parameters in one list."""
        if self._bound_to is not None:
            # The parameters belong to the blueprint; editing them here would
            # be a change the next update of that blueprint silently took back.
            return self.async_abort(reason="blueprint_locked")
        return await super().async_step_manage_parameters(user_input)

    async def _async_parameters_done(self) -> SubentryFlowResult:
        """Write the finished preset back."""
        if self.source != SOURCE_RECONFIGURE:
            return self.async_create_entry(
                title=self._name,
                data=_preset_data(self._preset_mode, self._blueprint, self._parameters),
            )

        subentry = self._get_reconfigure_subentry()
        if self._retyped and (store := async_get_store(self.hass)) is not None:
            for key in self._retyped:
                store.remove_parameter(subentry.subentry_id, key)
        return self._save(parameters=self._parameters)

    def _save(
        self,
        *,
        parameters: list[ParameterDef] | None = None,
        title: str | None = None,
    ) -> SubentryFlowResult:
        """Write the changed preset configuration back to the subentry."""
        subentry = self._get_reconfigure_subentry()
        data = dict(subentry.data)
        if parameters is not None:
            data[CONF_PARAMETERS] = parameters_to_data(parameters)
        return self.async_update_and_abort(
            self._get_entry(),
            subentry,
            data=data,
            title=title if title is not None else subentry.title,
        )
