"""Binary sensor platform: resolved values of boolean parameters."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PresetManagerConfigEntry
from .entity import ParameterValueEntity
from .parameter_types import get_parameter_type

#: Nothing on these platforms does I/O: a value is resolved in memory and
#: written to a debounced store, so there is no device to overwhelm and no
#: reason to serialise. Declared rather than left to the default, which would
#: quietly become 1 the day an entity here grew a synchronous update method.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PresetManagerConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up binary sensors for boolean parameters."""
    runtime = entry.runtime_data
    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ParameterValueBinarySensor(coordinator, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).value_platform
            is Platform.BINARY_SENSOR
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ParameterValueBinarySensor(ParameterValueEntity, BinarySensorEntity):
    """Publishes the currently valid value of a boolean parameter."""

    @property
    def is_on(self) -> bool | None:
        """Return the resolved value."""
        value = self.resolved_value
        return None if value is None else bool(value)
