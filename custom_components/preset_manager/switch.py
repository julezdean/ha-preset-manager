"""Switch platform: editors for boolean mode values."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import hubs
from .const import HUB_PRESET_MODES, UID_AUTOMATIC
from .coordinator import (
    PresetCoordinator,
    PresetManagerConfigEntry,
    PresetModeCoordinator,
)
from .entity import ModeValueEditorEntity, PresetEntity, PresetModeEntity
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
    """Set up the automatic switches and the switch editors."""
    runtime = entry.runtime_data

    if hubs.hub_kind(entry) == HUB_PRESET_MODES:
        for subentry_id, preset_mode in runtime.preset_modes.items():
            # Without a source there is nothing to switch between.
            if preset_mode.has_source:
                async_add_entities(
                    [AutomaticSwitch(preset_mode)], config_subentry_id=subentry_id
                )
        return

    for subentry_id, coordinator in runtime.presets.items():
        entities: list[SwitchEntity] = [PresetAutomaticSwitch(coordinator)]
        entities.extend(
            ModeParameterSwitch(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.SWITCH
            for mode in coordinator.modes
        )
        async_add_entities(entities, config_subentry_id=subentry_id)


class AutomaticSwitch(PresetModeEntity, SwitchEntity):
    """Switches a preset mode between automatic and manual."""

    _attr_translation_key = "automatic"
    _object_id_name = "automatic"

    def __init__(self, preset_mode: PresetModeCoordinator) -> None:
        """Initialise the automatic switch."""
        super().__init__(preset_mode, UID_AUTOMATIC)

    @property
    def is_on(self) -> bool:
        """Return whether the mode follows the source."""
        return self.preset_mode.automatic

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Follow the source again and evaluate it right away."""
        await self.preset_mode.async_set_automatic(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Keep the current mode and allow setting it by hand."""
        await self.preset_mode.async_set_automatic(False)


class PresetAutomaticSwitch(PresetEntity, SwitchEntity):
    """Switches one preset between following its preset mode and standing alone.

    Every preset has one, including those whose preset mode has no automatic
    of its own or follows another entity - what is switched here is not the
    conditions but whether this preset listens to the dimension at all.
    """

    _attr_translation_key = "automatic"
    _object_id_name = "automatic"

    def __init__(self, coordinator: PresetCoordinator) -> None:
        """Initialise the automatic switch of a preset."""
        super().__init__(coordinator, UID_AUTOMATIC)

    @property
    def is_on(self) -> bool:
        """Return whether the preset takes the mode of its preset mode."""
        return self.coordinator.automatic

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Follow the preset mode again, from its current mode."""
        await self.coordinator.async_set_automatic(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Keep the current mode and allow setting it on this preset."""
        await self.coordinator.async_set_automatic(False)


class ModeParameterSwitch(ModeValueEditorEntity, SwitchEntity):
    """Editable boolean value of one parameter in one mode."""

    @property
    def is_on(self) -> bool | None:
        """Return the configured value."""
        value = self.raw_value
        return None if value is None else bool(value)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Set the value to ``True``."""
        self._write_value(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Set the value to ``False``."""
        self._write_value(False)
