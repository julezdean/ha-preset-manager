"""Registry of parameter types.

Every parameter type mirrors one of the Home Assistant input helpers, so a
parameter is configured with the same raw building blocks a helper offers
instead of a pre-baked semantic type. The registry describes which Home
Assistant platform edits a parameter, which platform publishes the resolved
value, how a raw value is validated and which extra configuration fields the
config flow has to ask for.

Adding a type is a matter of instantiating :class:`ParameterType` and passing it
to :func:`register_parameter_type` - no other module has to be touched.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Any, Final

from homeassistant.components.number import DEVICE_CLASS_UNITS, NumberDeviceClass
from homeassistant.components.sensor import (
    DEVICE_CLASS_STATE_CLASSES,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.const import Platform
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DEVICE_CLASS,
    CONF_DISPLAY_MODE,
    CONF_MAX,
    CONF_MAX_LENGTH,
    CONF_MIN,
    CONF_MIN_LENGTH,
    CONF_OPTIONS,
    CONF_PATTERN,
    CONF_STEP,
    CONF_UNIT,
)

if TYPE_CHECKING:
    from .models import ParameterDef

#: input_number
TYPE_NUMBER: Final = "number"
#: input_boolean
TYPE_BOOLEAN: Final = "boolean"
#: input_text
TYPE_TEXT: Final = "text"
#: input_select
TYPE_SELECT: Final = "select"
#: input_datetime with date and time
TYPE_DATETIME: Final = "datetime"
#: input_datetime with date only
TYPE_DATE: Final = "date"
#: input_datetime with time only
TYPE_TIME: Final = "time"

#: Types whose value is a point in time.
TEMPORAL_TYPES: Final = frozenset({TYPE_DATETIME, TYPE_DATE, TYPE_TIME})

# Display modes -----------------------------------------------------------------

MODE_BOX: Final = "box"
MODE_SLIDER: Final = "slider"
MODE_TEXT: Final = "text"
MODE_PASSWORD: Final = "password"

NUMBER_MODES: Final = (MODE_BOX, MODE_SLIDER)
TEXT_MODES: Final = (MODE_TEXT, MODE_PASSWORD)

# Fallbacks used when a field is left empty ---------------------------------------

DEFAULT_MIN: Final = 0.0
DEFAULT_MAX: Final = 100.0
DEFAULT_STEP: Final = 1.0
DEFAULT_MAX_LENGTH: Final = 255


class ParameterValueError(ValueError):
    """Raised when a value does not fit the parameter definition."""


@dataclass(frozen=True, kw_only=True, slots=True)
class ParameterType:
    """Describes a supported parameter type."""

    key: str
    #: Platform used for the per-mode *editor* entity (``None`` = read only).
    editor_platform: Platform | None
    #: Platform used for the resolved ("currently active") value entity.
    value_platform: Platform
    #: ``True`` when values are stored as floats.
    numeric: bool = False
    #: Names of the type dependent fields the config flow asks for.
    fields: frozenset[str] = frozenset()
    _coerce: Callable[[Any, ParameterDef], Any] = field(repr=False)

    def has_field(self, name: str) -> bool:
        """Return whether this type is configured with ``name``."""
        return name in self.fields

    def coerce(self, value: Any, parameter: ParameterDef) -> Any:
        """Validate and normalise ``value`` for ``parameter``.

        Raises:
            ParameterValueError: if the value cannot be used.

        """
        return self._coerce(value, parameter)


def _coerce_number(value: Any, parameter: ParameterDef) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as err:
        raise ParameterValueError(f"{value!r} is not a number") from err
    if parameter.minimum is not None and number < parameter.minimum:
        raise ParameterValueError(f"{number} is below the minimum {parameter.minimum}")
    if parameter.maximum is not None and number > parameter.maximum:
        raise ParameterValueError(f"{number} is above the maximum {parameter.maximum}")
    return number


def _coerce_boolean(value: Any, parameter: ParameterDef) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in ("true", "on", "yes", "1"):
            return True
        if lowered in ("false", "off", "no", "0"):
            return False
    raise ParameterValueError(f"{value!r} is not a boolean")


def _coerce_text(value: Any, parameter: ParameterDef) -> str:
    if value is None:
        raise ParameterValueError("text value must not be None")
    text = str(value)
    if parameter.min_length is not None and len(text) < parameter.min_length:
        raise ParameterValueError(f"shorter than {parameter.min_length} characters")
    if parameter.max_length is not None and len(text) > parameter.max_length:
        raise ParameterValueError(f"longer than {parameter.max_length} characters")
    if parameter.pattern and not re.fullmatch(parameter.pattern, text):
        raise ParameterValueError(f"{text!r} does not match {parameter.pattern!r}")
    return text


def _coerce_select(value: Any, parameter: ParameterDef) -> str:
    text = str(value)
    if parameter.options and text not in parameter.options:
        raise ParameterValueError(
            f"{text!r} is not one of {', '.join(parameter.options)}"
        )
    return text


def _coerce_datetime(value: Any, parameter: ParameterDef) -> str:
    """Return an ISO string of an aware datetime."""
    if isinstance(value, datetime):
        parsed: datetime | None = value
    else:
        parsed = dt_util.parse_datetime(str(value))
    if parsed is None:
        raise ParameterValueError(f"{value!r} is not a date and time")
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt_util.get_default_time_zone())
    return parsed.isoformat()


def _coerce_date(value: Any, parameter: ParameterDef) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    parsed = dt_util.parse_date(str(value))
    if parsed is None:
        raise ParameterValueError(f"{value!r} is not a date")
    return parsed.isoformat()


def _coerce_time(value: Any, parameter: ParameterDef) -> str:
    if isinstance(value, datetime):
        return value.time().isoformat()
    if isinstance(value, time):
        return value.isoformat()
    parsed = dt_util.parse_time(str(value))
    if parsed is None:
        raise ParameterValueError(f"{value!r} is not a time")
    return parsed.isoformat()


PARAMETER_TYPES: dict[str, ParameterType] = {}


def register_parameter_type(parameter_type: ParameterType) -> None:
    """Register a parameter type (idempotent for the same key)."""
    PARAMETER_TYPES[parameter_type.key] = parameter_type


def get_parameter_type(key: str) -> ParameterType:
    """Return the parameter type for ``key``.

    Falls back to the generic number type so a config entry written by a newer
    version of the integration never breaks the whole setup.
    """
    return PARAMETER_TYPES.get(key, PARAMETER_TYPES[TYPE_NUMBER])


def parameter_type_keys() -> list[str]:
    """Return all registered type keys in registration order."""
    return list(PARAMETER_TYPES)


for _parameter_type in (
    ParameterType(
        key=TYPE_NUMBER,
        editor_platform=Platform.NUMBER,
        value_platform=Platform.SENSOR,
        numeric=True,
        fields=frozenset(
            {
                CONF_MIN,
                CONF_MAX,
                CONF_STEP,
                CONF_UNIT,
                CONF_DEVICE_CLASS,
                CONF_DISPLAY_MODE,
            }
        ),
        _coerce=_coerce_number,
    ),
    ParameterType(
        key=TYPE_BOOLEAN,
        editor_platform=Platform.SWITCH,
        value_platform=Platform.BINARY_SENSOR,
        _coerce=_coerce_boolean,
    ),
    ParameterType(
        key=TYPE_TEXT,
        editor_platform=Platform.TEXT,
        value_platform=Platform.SENSOR,
        fields=frozenset(
            {CONF_MIN_LENGTH, CONF_MAX_LENGTH, CONF_PATTERN, CONF_DISPLAY_MODE}
        ),
        _coerce=_coerce_text,
    ),
    ParameterType(
        key=TYPE_SELECT,
        editor_platform=Platform.SELECT,
        value_platform=Platform.SENSOR,
        fields=frozenset({CONF_OPTIONS}),
        _coerce=_coerce_select,
    ),
    ParameterType(
        key=TYPE_DATETIME,
        editor_platform=Platform.DATETIME,
        value_platform=Platform.SENSOR,
        _coerce=_coerce_datetime,
    ),
    ParameterType(
        key=TYPE_DATE,
        editor_platform=Platform.DATE,
        value_platform=Platform.SENSOR,
        _coerce=_coerce_date,
    ),
    ParameterType(
        key=TYPE_TIME,
        editor_platform=Platform.TIME,
        value_platform=Platform.SENSOR,
        _coerce=_coerce_time,
    ),
):
    register_parameter_type(_parameter_type)


def coerce_value(value: Any, parameter: ParameterDef) -> Any:
    """Coerce ``value`` using the type of ``parameter``."""
    return get_parameter_type(parameter.type).coerce(value, parameter)


def editor_platforms() -> Mapping[str, Platform | None]:
    """Return a mapping of type key -> editor platform."""
    return {key: value.editor_platform for key, value in PARAMETER_TYPES.items()}


def device_class_keys() -> list[str]:
    """Return every device class that can be assigned to a number parameter."""
    return sorted(item.value for item in NumberDeviceClass)


def allowed_units(device_class: str | None) -> set[str] | None:
    """Return the units a device class accepts.

    ``None`` means "no restriction"; an empty string inside the set means the
    device class is used without a unit.
    """
    if not device_class:
        return None
    try:
        parsed = NumberDeviceClass(device_class)
    except ValueError:
        return None
    if parsed not in DEVICE_CLASS_UNITS:
        return None
    units: set[str] = set()
    for item in DEVICE_CLASS_UNITS[parsed]:
        if item is None:
            units.add("")
        elif isinstance(item, type):
            units.update(str(member.value) for member in item)
        else:
            units.add(str(item))
    return units


def number_device_class(parameter: ParameterDef) -> NumberDeviceClass | None:
    """Return the device class of the editor entity of ``parameter``."""
    if not parameter.device_class:
        return None
    try:
        return NumberDeviceClass(parameter.device_class)
    except ValueError:
        return None


def sensor_device_class(parameter: ParameterDef) -> SensorDeviceClass | None:
    """Return the device class of the value entity of ``parameter``."""
    if parameter.type == TYPE_SELECT:
        return SensorDeviceClass.ENUM
    if parameter.type in TEMPORAL_TYPES:
        return SensorDeviceClass.TIMESTAMP
    if not parameter.device_class:
        return None
    try:
        return SensorDeviceClass(parameter.device_class)
    except ValueError:
        return None


def sensor_state_class(parameter: ParameterDef) -> SensorStateClass | None:
    """Return the state class the value sensor may use.

    Numbers are measurements, but a few device classes (energy and the other
    meters) only accept totals - handing them ``measurement`` would make Home
    Assistant reject the entity.
    """
    if parameter.type != TYPE_NUMBER:
        return None
    device_class = sensor_device_class(parameter)
    if device_class is None:
        return SensorStateClass.MEASUREMENT
    allowed = DEVICE_CLASS_STATE_CLASSES.get(device_class, set())
    if not allowed:
        return None
    if SensorStateClass.MEASUREMENT in allowed:
        return SensorStateClass.MEASUREMENT
    return sorted(allowed)[0]


def as_timestamp(value: Any, type_key: str) -> datetime | None:
    """Return a point in time for a stored date/time/datetime value.

    A date becomes midnight of that day and a time becomes that time *today*,
    both in local time, so the resulting sensor always carries a real timestamp
    that automations can use as a trigger. The local time zone is attached to
    the wall clock time rather than added as an offset, so the result stays
    correct across daylight saving changes.
    """
    if value is None:
        return None
    if type_key == TYPE_DATETIME:
        parsed = dt_util.parse_datetime(str(value))
        if parsed is None:
            return None
        return _localise(parsed)
    if type_key == TYPE_DATE:
        day = dt_util.parse_date(str(value))
        if day is None:
            return None
        return _localise(datetime.combine(day, time.min))
    if type_key == TYPE_TIME:
        moment = dt_util.parse_time(str(value))
        if moment is None:
            return None
        return _localise(datetime.combine(dt_util.now().date(), moment))
    return None


def _localise(value: datetime) -> datetime:
    """Return ``value`` in the local time zone, assuming local wall clock time."""
    if value.tzinfo is None:
        return value.replace(tzinfo=dt_util.get_default_time_zone())
    return dt_util.as_local(value)
