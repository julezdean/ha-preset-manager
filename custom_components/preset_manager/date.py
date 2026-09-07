"""Date platform: editors for date mode values."""

from __future__ import annotations

from datetime import date

from homeassistant.components.date import DateEntity
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
    """Set up the date editors of every preset."""
    runtime = entry.runtime_data
    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ModeParameterDate(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.DATE
            for mode in coordinator.modes
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ModeParameterDate(ModeValueEditorEntity, DateEntity):
    """Editable date of one parameter in one mode."""

    @property
    def native_value(self) -> date | None:
        """Return the configured value."""
        value = self.raw_value
        return None if value is None else dt_util.parse_date(str(value))

    async def async_set_value(self, value: date) -> None:
        """Store a new value."""
        self._write_value(value)
