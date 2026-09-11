"""Switch platform: editors for boolean mode values."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import hubs
from .const import HUB_PRESET_MODES, UID_AUTOMATIC
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
    """Set up the automatic switches and the switch editors."""
    runtime = entry.runtime_data

    if hubs.hub_kind(entry) == HUB_PRESET_MODES:
        # Nothing to switch here any more: a preset mode runs on its
        # conditions or on the entity it follows, with no way to take it over.
        return

    for subentry_id, coordinator in runtime.presets.items():
        entities: list[SwitchEntity] = [ModeAutomaticSwitch(coordinator)]
        entities.extend(
            ModeParameterSwitch(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.SWITCH
            for mode in coordinator.modes
        )
        async_add_entities(entities, config_subentry_id=subentry_id)


class ModeAutomaticSwitch(PresetEntity, SwitchEntity):
    """Switches one preset between following its preset mode and standing alone.

    Every preset has one, including those whose preset mode has no automatic
    of its own or follows another entity - what is switched here is not the
    conditions but whether this preset listens to the dimension at all.
    """

    _attr_translation_key = "mode_automatic"
    #: Not "automatic": that is the object id of the preset mode's switch, and
    #: a preset named like its preset mode would push one of the two into an
    #: "_2" suffix. Nor "mode_automatic", which would look symmetric and be
    #: worse - a preset "House" under a preset mode "House Mode" builds the
    #: same id, and *that* collision nobody can see. Any suffix not ending in
    #: "automatic" makes the whole class impossible; this one also says what
    #: the switch decides.
    _object_id_name = "follows_preset_mode"

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
