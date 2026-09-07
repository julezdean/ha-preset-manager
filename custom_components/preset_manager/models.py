"""Immutable data structures describing modes, parameters and presets.

Everything in this module is plain data. The objects are rebuilt from the config
entry / subentry on every setup, which keeps the runtime state and the persisted
configuration in sync by construction.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from typing import Any, Self

from homeassistant.util import slugify

from .const import (
    CONF_BLUEPRINT,
    CONF_CONDITIONS,
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
    CONF_SOURCE_ENTITY,
    CONF_STEP,
    CONF_TYPE,
    CONF_UNIT,
)
from .parameter_types import (
    DEFAULT_MAX,
    DEFAULT_MAX_LENGTH,
    DEFAULT_MIN,
    DEFAULT_STEP,
    MODE_BOX,
    MODE_TEXT,
    TYPE_NUMBER,
    TYPE_TEXT,
)


def make_key(name: str, existing: Iterable[str]) -> str:
    """Return a stable, unique slug for ``name``.

    Keys are generated once and never change again - renaming a mode or a
    parameter keeps the key (and therefore the unique_id of every entity and the
    stored values) untouched.
    """
    base = slugify(name) or "item"
    taken = set(existing)
    if base not in taken:
        return base
    index = 2
    while f"{base}_{index}" in taken:
        index += 1
    return f"{base}_{index}"


@dataclass(frozen=True, kw_only=True, slots=True)
class ModeDef:
    """One mode of a preset mode, such as "Night".

    The position in the list of a preset mode is both its priority (the
    first mode whose conditions match becomes active) and the order of the
    options of the select entity.
    """

    key: str
    name: str
    icon: str | None = None
    #: Conditions selecting this mode; empty means "never automatically".
    conditions: tuple[dict[str, Any], ...] = ()

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Create a mode definition from stored data."""
        return cls(
            key=data[CONF_KEY],
            name=data[CONF_NAME],
            icon=data.get(CONF_ICON),
            conditions=tuple(data.get(CONF_CONDITIONS) or ()),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the storage representation."""
        data: dict[str, Any] = {CONF_KEY: self.key, CONF_NAME: self.name}
        if self.icon:
            data[CONF_ICON] = self.icon
        if self.conditions:
            data[CONF_CONDITIONS] = [dict(item) for item in self.conditions]
        return data


@dataclass(frozen=True, kw_only=True, slots=True)
class ParameterDef:
    """A single configurable parameter of a preset.

    The fields mirror the options of the Home Assistant input helper the type
    stands for; every type only uses the subset listed in its
    :attr:`~.parameter_types.ParameterType.fields`.
    """

    key: str
    name: str
    type: str = TYPE_NUMBER
    #: Number: value range and step size.
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None
    unit: str | None = None
    device_class: str | None = None
    #: Number: box/slider, text: text/password.
    display_mode: str | None = None
    #: Text: length limits and validation pattern.
    min_length: int | None = None
    max_length: int | None = None
    pattern: str | None = None
    #: Select: the available options.
    options: tuple[str, ...] = ()
    default: Any = None
    icon: str | None = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Create a parameter definition from stored data."""
        return cls(
            key=data[CONF_KEY],
            name=data[CONF_NAME],
            type=data.get(CONF_TYPE, TYPE_NUMBER),
            minimum=data.get(CONF_MIN),
            maximum=data.get(CONF_MAX),
            step=data.get(CONF_STEP),
            unit=data.get(CONF_UNIT),
            device_class=data.get(CONF_DEVICE_CLASS),
            display_mode=data.get(CONF_DISPLAY_MODE),
            min_length=data.get(CONF_MIN_LENGTH),
            max_length=data.get(CONF_MAX_LENGTH),
            pattern=data.get(CONF_PATTERN),
            options=tuple(data.get(CONF_OPTIONS) or ()),
            default=data.get(CONF_DEFAULT),
            icon=data.get(CONF_ICON),
        )

    def to_dict(self) -> dict[str, Any]:
        """Return the storage representation."""
        data: dict[str, Any] = {
            CONF_KEY: self.key,
            CONF_NAME: self.name,
            CONF_TYPE: self.type,
        }
        for conf_key, value in (
            (CONF_MIN, self.minimum),
            (CONF_MAX, self.maximum),
            (CONF_STEP, self.step),
            (CONF_UNIT, self.unit),
            (CONF_DEVICE_CLASS, self.device_class),
            (CONF_DISPLAY_MODE, self.display_mode),
            (CONF_MIN_LENGTH, self.min_length),
            (CONF_MAX_LENGTH, self.max_length),
            (CONF_PATTERN, self.pattern),
            (CONF_DEFAULT, self.default),
            (CONF_ICON, self.icon),
        ):
            if value is not None:
                data[conf_key] = value
        if self.options:
            data[CONF_OPTIONS] = list(self.options)
        return data

    def with_type_defaults(self) -> ParameterDef:
        """Fill the fields the type needs but the user left empty.

        Fields that do not belong to the type are cleared, so a parameter never
        carries leftovers from a type it does not have.
        """
        if self.type == TYPE_NUMBER:
            return replace(
                self,
                minimum=DEFAULT_MIN if self.minimum is None else self.minimum,
                maximum=DEFAULT_MAX if self.maximum is None else self.maximum,
                step=DEFAULT_STEP if self.step is None else self.step,
                display_mode=self.display_mode or MODE_BOX,
                min_length=None,
                max_length=None,
                pattern=None,
            )
        if self.type == TYPE_TEXT:
            return replace(
                self,
                minimum=None,
                maximum=None,
                step=None,
                unit=None,
                device_class=None,
                max_length=(
                    DEFAULT_MAX_LENGTH if self.max_length is None else self.max_length
                ),
                display_mode=self.display_mode or MODE_TEXT,
            )
        return replace(
            self,
            minimum=None,
            maximum=None,
            step=None,
            unit=None,
            device_class=None,
            display_mode=None,
            min_length=None,
            max_length=None,
            pattern=None,
        )

    @property
    def display_precision(self) -> int | None:
        """Return a sensible display precision derived from the step size."""
        if self.step is None:
            return None
        return 0 if float(self.step).is_integer() else 1


@dataclass(frozen=True, kw_only=True, slots=True)
class PresetConfig:
    """Configuration of one preset (= one config subentry)."""

    subentry_id: str
    name: str
    parameters: tuple[ParameterDef, ...] = ()
    #: Entry id of the blueprint the preset follows, or ``None``.
    blueprint: str | None = None

    @classmethod
    def from_subentry(
        cls, subentry_id: str, title: str, data: Mapping[str, Any]
    ) -> Self:
        """Create a preset configuration from a config subentry.

        A preset always covers every mode of the preset mode it belongs to -
        there is no subset and therefore no fallback strategy to configure.

        The parameters of a preset following a blueprint are not stored on
        the subentry; ``blueprints.async_resolve_preset_data`` fills them in
        before this is called.
        """
        return cls(
            subentry_id=subentry_id,
            name=title,
            parameters=tuple(
                ParameterDef.from_dict(item).with_type_defaults()
                for item in data.get(CONF_PARAMETERS, [])
            ),
            blueprint=data.get(CONF_BLUEPRINT) or None,
        )

    @property
    def is_locked(self) -> bool:
        """Return whether the parameters are owned by a blueprint."""
        return self.blueprint is not None

    def parameter(self, key: str) -> ParameterDef | None:
        """Return the parameter with ``key`` if it exists."""
        return next((item for item in self.parameters if item.key == key), None)


@dataclass(frozen=True, kw_only=True, slots=True)
class PresetModeConfig:
    """Configuration of one preset mode (= one config entry)."""

    entry_id: str
    name: str
    modes: tuple[ModeDef, ...] = ()
    #: Entity whose state names the active mode, or ``None``.
    source_entity: str | None = None

    @classmethod
    def from_entry(cls, entry_id: str, title: str, data: Mapping[str, Any]) -> Self:
        """Create a preset mode configuration from a config entry."""
        return cls(
            entry_id=entry_id,
            name=title,
            modes=tuple(ModeDef.from_dict(item) for item in data.get(CONF_MODES, [])),
            source_entity=data.get(CONF_SOURCE_ENTITY) or None,
        )

    @property
    def is_external(self) -> bool:
        """Return whether the mode comes from another entity."""
        return self.source_entity is not None

    @property
    def has_conditions(self) -> bool:
        """Return whether any mode can be selected automatically.

        An external preset_mode never evaluates its conditions - they stay stored so
        that clearing the entity brings them back untouched.
        """
        return not self.is_external and any(mode.conditions for mode in self.modes)

    def mode(self, key: str | None) -> ModeDef | None:
        """Return the mode with ``key``."""
        if key is None:
            return None
        return next((item for item in self.modes if item.key == key), None)


def parameters_to_data(parameters: Iterable[ParameterDef]) -> list[dict[str, Any]]:
    """Serialise parameters for storage in a config subentry."""
    return [parameter.to_dict() for parameter in parameters]


def modes_to_data(modes: Iterable[ModeDef]) -> list[dict[str, Any]]:
    """Serialise modes for storage in the config entry options."""
    return [mode.to_dict() for mode in modes]
