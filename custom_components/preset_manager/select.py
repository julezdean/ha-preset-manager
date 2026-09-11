"""Select platform: the mode selector and enum value editors."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.select import SelectEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import hubs
from .const import (
    ATTR_MODE,
    HUB_PRESET_MODES,
    SERVICE_SET_ACTIVE_MODE,
    UID_MODE_SELECTION,
)
from .coordinator import PresetCoordinator, PresetManagerConfigEntry
from .entity import ModeValueEditorEntity, PresetEntity
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
    """Set up the mode selectors and the enum editors."""
    runtime = entry.runtime_data

    if hubs.hub_kind(entry) == HUB_PRESET_MODES:
        # A preset mode has no selector: its mode comes from its conditions or
        # from the entity it follows, and from nothing else. Taking one device
        # out of that is what the automatic of a *preset* is for.
        return

    # The one place the mode is set by hand: a preset that is not following
    # its preset mode, addressed by its own selector.
    entity_platform.async_get_current_platform().async_register_entity_service(
        SERVICE_SET_ACTIVE_MODE,
        {vol.Required(ATTR_MODE): cv.string},
        "async_set_active_mode",
    )

    for subentry_id, coordinator in runtime.presets.items():
        entities: list[SelectEntity] = [PresetModeSelect(coordinator)]
        entities.extend(
            ModeParameterSelect(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.SELECT
            for mode in coordinator.modes
        )
        async_add_entities(entities, config_subentry_id=subentry_id)


class PresetModeSelect(PresetEntity, SelectEntity):
    """Sets the mode of one preset while its automatic is off.

    It shows the effective mode either way, the same as the selector of a
    preset mode does under a running automatic - what changes with the switch
    is whether it accepts a write, not what it reports.

    Not called "active mode": the preset already has a sensor of that name,
    and two entities with one name on one device is a riddle rather than a
    pair.
    """

    _attr_translation_key = "mode_selection"
    _object_id_name = "mode_selection"

    def __init__(self, coordinator: PresetCoordinator) -> None:
        """Initialise the mode selector of a preset."""
        super().__init__(coordinator, UID_MODE_SELECTION)
        self._attr_options = [mode.name for mode in coordinator.modes]

    @property
    def current_option(self) -> str | None:
        """Return the name of the effective mode."""
        return self.state_data.mode_name

    async def async_select_option(self, option: str) -> None:
        """Set the mode of this preset by its display name."""
        self.coordinator.async_set_active_mode(option)

    async def async_set_active_mode(self, mode: str) -> None:
        """Set the mode of this preset by its stable key."""
        self.coordinator.async_set_active_mode(mode)


class ModeParameterSelect(ModeValueEditorEntity, SelectEntity):
    """Editable enum value of one parameter in one mode."""

    @property
    def options(self) -> list[str]:
        """Return the configured options."""
        return list(self.parameter.options)

    @property
    def current_option(self) -> str | None:
        """Return the configured value."""
        value = self.raw_value
        return None if value is None else str(value)

    async def async_select_option(self, option: str) -> None:
        """Store a new value."""
        self._write_value(option)
