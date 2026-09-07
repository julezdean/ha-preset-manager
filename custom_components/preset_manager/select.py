"""Select platform: the mode selector and enum value editors."""

from __future__ import annotations

import voluptuous as vol
from homeassistant.components.select import SelectEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import ATTR_MODE, SERVICE_SET_ACTIVE_MODE, UID_ACTIVE_MODE
from .coordinator import PresetModeConfigEntry, PresetModeCoordinator
from .entity import ModeValueEditorEntity, PresetModeEntity
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
    """Set up the mode selectors and the enum editors."""
    runtime = entry.runtime_data

    # The mode selector is what a preset mode is set on, so setting it by its
    # stable key is a service on that entity rather than a service of the
    # domain looking the preset mode up by its (renameable) display name.
    entity_platform.async_get_current_platform().async_register_entity_service(
        SERVICE_SET_ACTIVE_MODE,
        {vol.Required(ATTR_MODE): cv.string},
        "async_set_active_mode",
    )

    # The selector exists for every preset mode that can be set by hand at all: it
    # would otherwise appear and disappear with the automatic switch, taking its
    # entity id and history with it. A preset mode following another entity is the
    # exception - there is nothing to select.
    if not runtime.preset_mode.external:
        async_add_entities([ActiveModeSelect(runtime.preset_mode)])

    for subentry_id, coordinator in runtime.presets.items():
        entities = [
            ModeParameterSelect(coordinator, mode, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).editor_platform is Platform.SELECT
            for mode in coordinator.modes
        ]
        if entities:
            async_add_entities(entities, config_subentry_id=subentry_id)


class ActiveModeSelect(PresetModeEntity, SelectEntity):
    """Selects the active mode of a preset mode."""

    _attr_translation_key = "active_mode"
    _object_id_name = "active_mode"

    def __init__(self, preset_mode: PresetModeCoordinator) -> None:
        """Initialise the mode selector."""
        super().__init__(preset_mode, UID_ACTIVE_MODE)
        self._attr_options = [mode.name for mode in preset_mode.modes]

    @property
    def current_option(self) -> str | None:
        """Return the name of the active mode."""
        mode = self.preset_mode.active_mode
        return mode.name if mode else None

    async def async_select_option(self, option: str) -> None:
        """Activate another mode by its display name.

        Refused while the automatic is on - switching the mode by hand has
        to be a deliberate act, not a side effect of a click.
        """
        self.preset_mode.async_set_active_mode(option)

    async def async_set_active_mode(self, mode: str) -> None:
        """Activate another mode by its stable key.

        The key is what survives a rename, which is why this exists beside
        ``select.select_option`` - that one only knows the display name.
        """
        self.preset_mode.async_set_active_mode(mode)


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
