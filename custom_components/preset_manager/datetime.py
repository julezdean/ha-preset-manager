"""Datetime platform: editors for date and time mode values."""

from __future__ import annotations

from datetime import datetime

from homeassistant.components.datetime import DateTimeEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from .coordinator import PresetModeConfigEntry
from .entity import ModeValueEditorEntity
from .parameter_types import get_parameter_type

#: Nothing on these platforms does I/O: a value is resolved in memory and
#: written to a debounced store, so there is no device to overwhelm and no
#: reason to serialise. Declared rather than left to the default, which would
#: quietly become 1 the day an entity here grew a synchronous update method.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PresetModeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the date/time editors of every preset."""
    runtime = entry.runtime_data
    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ModeParameterDateTime(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.DATETIME
            for mode in coordinator.modes
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ModeParameterDateTime(ModeValueEditorEntity, DateTimeEntity):
    """Editable date and time of one parameter in one mode."""

    @property
    def native_value(self) -> datetime | None:
        """Return the configured value as an aware datetime."""
        value = self.raw_value
        if value is None:
            return None
        parsed = dt_util.parse_datetime(str(value))
        return None if parsed is None else dt_util.as_utc(parsed)

    async def async_set_value(self, value: datetime) -> None:
        """Store a new value."""
        self._write_value(value)
