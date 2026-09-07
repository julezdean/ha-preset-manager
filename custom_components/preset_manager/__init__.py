"""The Preset Mode integration."""

from __future__ import annotations

import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
)
from homeassistant.helpers import (
    device_registry as dr,
)
from homeassistant.helpers import (
    entity_registry as er,
)
from homeassistant.helpers.device_registry import DeviceEntry, DeviceEntryType
from homeassistant.helpers.typing import ConfigType

from . import blueprints
from .const import DOMAIN, ENTRY_VERSION
from .coordinator import PresetModeConfigEntry, PresetModeRuntime
from .entity import MANUFACTURER, MODEL_PRESET_MODE, async_expected_unique_ids
from .services import async_setup_services
from .store import async_setup_store

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DATE,
    Platform.DATETIME,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TEXT,
    Platform.TIME,
]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services and open the shared value store."""
    await async_setup_store(hass)
    async_setup_services(hass)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: PresetModeConfigEntry
) -> bool:
    """Bring a config entry up to the current schema.

    It exists from the first release on, before it had anything to do: without
    it Home Assistant logs "Migration handler not found" and refuses to set up
    an entry whose major version is lower than this flow's, which would turn
    the first breaking schema change into a broken setup for everybody. A lower
    minor version alone is tolerated without a handler, which is what makes
    ENTRY_MINOR_VERSION the additive one.

    Presets are subentries and carry no version of their own - their data is
    migrated here, alongside the entry they belong to.
    """
    if entry.version > ENTRY_VERSION:
        # Written by a newer version of the integration; its keys are unknown
        # to this one, and guessing at them would corrupt the setup.
        _LOGGER.error(
            "Config entry '%s' was created by a newer version of %s "
            "(%s.%s); downgrading is not supported",
            entry.title,
            DOMAIN,
            entry.version,
            entry.minor_version,
        )
        return False

    # Migration steps go here, smallest version first, each one ending in an
    # async_update_entry() that records the version it reached.

    return True


async def async_setup_entry(hass: HomeAssistant, entry: PresetModeConfigEntry) -> bool:
    """Set up a preset mode - or a blueprint - from a config entry."""
    if blueprints.is_blueprint(entry):
        # A blueprint is configuration and nothing else: no device, no
        # entities, no runtime. It only has to notice its own changes and hand
        # them to the presets that follow it.
        entry.async_on_unload(entry.add_update_listener(_async_blueprint_updated))
        return True

    store = await async_setup_store(hass)

    runtime = PresetModeRuntime(hass, entry, store)
    await runtime.async_initialize()
    entry.runtime_data = runtime

    _async_register_mode_device(hass, entry, runtime)
    _async_remove_stale_entities(hass, entry, runtime)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_config_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: PresetModeConfigEntry) -> bool:
    """Unload a config entry."""
    if blueprints.is_blueprint(entry):
        return True

    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Both of these happen even when a platform refused to unload. Home
    # Assistant marks such an entry as failed and never retries it, so a mode
    # source left running would run against a half torn down runtime, and
    # values not written here would be lost - the entry is going away either
    # way. The unload still reports the failure.
    runtime = entry.runtime_data
    runtime.async_shutdown()
    await runtime.store.async_save_now()
    return unloaded


async def async_remove_entry(hass: HomeAssistant, entry: PresetModeConfigEntry) -> None:
    """Drop the stored state of a deleted preset mode and its presets."""
    if blueprints.is_blueprint(entry):
        # Deleting a set must not take the presets that follow it with it: they
        # keep its parameters as their own and are editable again.
        blueprints.async_detach_presets(hass, entry)
        return

    store = await async_setup_store(hass)
    store.remove_preset_mode(entry.entry_id)
    for subentry_id in entry.subentries:
        store.remove_preset(subentry_id)
    await store.async_save_now()


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: PresetModeConfigEntry, device: DeviceEntry
) -> bool:
    """Allow removing devices that no longer belong to the entry."""
    known = {entry.entry_id, *entry.subentries}
    return not any(
        domain == DOMAIN and identifier in known
        for domain, identifier in device.identifiers
    )


async def _async_blueprint_updated(
    hass: HomeAssistant, entry: PresetModeConfigEntry
) -> None:
    """Hand a changed blueprint to every preset that follows it."""
    await blueprints.async_apply_blueprint(hass, entry.entry_id)


async def _async_config_updated(
    hass: HomeAssistant, entry: PresetModeConfigEntry
) -> None:
    """Reload the preset mode when its modes or its presets changed.

    Values are stored outside of the config entry, so this listener is only
    triggered by structural changes (modes, presets, parameters).
    """
    await hass.config_entries.async_reload(entry.entry_id)


def _async_register_mode_device(
    hass: HomeAssistant,
    entry: PresetModeConfigEntry,
    runtime: PresetModeRuntime,
) -> None:
    """Create the preset mode device the preset devices are attached to.

    It has to exist before the platforms are set up, because the preset devices
    reference it as their ``via_device``.
    """
    dr.async_get(hass).async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name=runtime.preset_mode.config.name,
        manufacturer=MANUFACTURER,
        model=MODEL_PRESET_MODE,
        entry_type=DeviceEntryType.SERVICE,
    )


def _async_remove_stale_entities(
    hass: HomeAssistant,
    entry: PresetModeConfigEntry,
    runtime: PresetModeRuntime,
) -> None:
    """Remove registry entries that no longer exist in the configuration."""
    expected = async_expected_unique_ids(runtime)
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.unique_id not in expected:
            _LOGGER.debug("Removing stale entity %s", registry_entry.entity_id)
            registry.async_remove(registry_entry.entity_id)
