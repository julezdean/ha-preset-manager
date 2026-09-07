"""Text platform: editors for textual mode values."""

from __future__ import annotations

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import PresetCoordinator, PresetModeConfigEntry
from .entity import ModeValueEditorEntity
from .models import ModeDef, ParameterDef
from .parameter_types import MODE_PASSWORD, get_parameter_type

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
    """Set up the text editors of every preset."""
    runtime = entry.runtime_data
    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ModeParameterText(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.TEXT
            for mode in coordinator.modes
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ModeParameterText(ModeValueEditorEntity, TextEntity):
    """Editable text value of one parameter in one mode."""

    def __init__(
        self,
        coordinator: PresetCoordinator,
        mode: ModeDef,
        parameter: ParameterDef,
    ) -> None:
        """Initialise the text editor."""
        super().__init__(coordinator, mode, parameter)
        self._attr_native_min = parameter.min_length or 0
        if parameter.max_length is not None:
            self._attr_native_max = parameter.max_length
        if parameter.pattern:
            self._attr_pattern = parameter.pattern
        self._attr_mode = (
            TextMode.PASSWORD
            if parameter.display_mode == MODE_PASSWORD
            else TextMode.TEXT
        )

    @property
    def native_value(self) -> str | None:
        """Return the configured value."""
        value = self.raw_value
        return None if value is None else str(value)

    async def async_set_value(self, value: str) -> None:
        """Store a new value."""
        self._write_value(value)
