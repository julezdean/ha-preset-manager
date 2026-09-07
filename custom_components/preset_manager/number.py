"""Number platform: editors for numeric mode values."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PresetCoordinator, PresetManagerConfigEntry
from .entity import ModeValueEditorEntity
from .models import ModeDef, ParameterDef
from .parameter_types import MODE_SLIDER, get_parameter_type, number_device_class

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
    """Set up the number editors of every preset."""
    runtime = entry.runtime_data
    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ModeParameterNumber(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.NUMBER
            for mode in coordinator.modes
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ModeParameterNumber(ModeValueEditorEntity, NumberEntity):
    """Editable numeric value of one parameter in one mode."""

    def __init__(
        self,
        coordinator: PresetCoordinator,
        mode: ModeDef,
        parameter: ParameterDef,
    ) -> None:
        """Initialise the number editor."""
        super().__init__(coordinator, mode, parameter)
        self._attr_device_class = number_device_class(parameter)
        self._attr_native_unit_of_measurement = parameter.unit
        self._attr_mode = (
            NumberMode.SLIDER
            if parameter.display_mode == MODE_SLIDER
            else NumberMode.BOX
        )
        if parameter.minimum is not None:
            self._attr_native_min_value = parameter.minimum
        if parameter.maximum is not None:
            self._attr_native_max_value = parameter.maximum
        if parameter.step is not None:
            self._attr_native_step = parameter.step

    @property
    def native_value(self) -> float | None:
        """Return the configured value."""
        return self.raw_value

    async def async_set_native_value(self, value: float) -> None:
        """Store a new value."""
        self._write_value(value)
