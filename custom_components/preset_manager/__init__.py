"""The Preset Manager integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryError
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

from . import following, hubs
from .const import (
    CONF_MODES,
    CONF_PARAMETERS,
    DOMAIN,
    ENTRY_VERSION,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
)
from .coordinator import (
    PresetManagerConfigEntry,
    PresetManagerRuntime,
    async_setup_runtime,
)
from .entity import (
    MANUFACTURER,
    MODEL_PRESET_MODE,
    async_expected_preset_ids,
    async_expected_preset_mode_ids,
)
from .services import async_setup_services
from .store import async_setup_store

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

#: What each hub brings. The mode selector, the mode sensor and the automatic
#: switch belong to a preset mode; everything else belongs to a preset. Three
#: platforms are forwarded by both hubs and tell the two apart by the hub they
#: are set up from.
PLATFORMS_PRESET_MODES: list[Platform] = [
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]
PLATFORMS_PRESETS: list[Platform] = [
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
PLATFORMS: dict[str, list[Platform]] = {
    HUB_PRESET_MODES: PLATFORMS_PRESET_MODES,
    HUB_PRESETS: PLATFORMS_PRESETS,
    HUB_BLUEPRINTS: [],
}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Register the services and build the runtime of the domain."""
    await async_setup_runtime(hass)
    async_setup_services(hass)
    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> bool:
    """Bring a config entry up to the current schema.

    Version 1 held one config entry per preset mode and per blueprint. It is
    not migrated: 0.1.0 was released and withdrawn without anybody running it,
    so the only entries at that version are from a development install, and a
    migration nobody needs is a path nobody tests. Such an entry is refused
    rather than half read - Home Assistant then says so on the entry instead
    of leaving the user with a setup that looks fine and is not.
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

    if entry.version < ENTRY_VERSION:
        _LOGGER.error(
            "Config entry '%s' was created by %s before its objects moved into "
            "hubs (schema %s.%s). Delete it and add the integration again",
            entry.title,
            DOMAIN,
            entry.version,
            entry.minor_version,
        )
        return False

    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> bool:
    """Set up one of the three hubs."""
    kind = hubs.hub_kind(entry)
    if kind is None:
        # Refused by async_migrate_entry already; nothing reaches this but an
        # entry someone built by hand.
        raise ConfigEntryError(f"'{entry.title}' is not a hub of {DOMAIN}")

    runtime = await async_setup_runtime(hass)
    entry.runtime_data = runtime

    if kind == HUB_PRESET_MODES:
        await runtime.async_load_preset_modes(entry)
        _async_register_preset_mode_devices(hass, entry, runtime)
        expected = async_expected_preset_mode_ids(runtime)
        _async_remove_stale_entities(hass, entry, expected)
    elif kind == HUB_PRESETS:
        runtime.async_load_presets(entry)
        _async_remove_stale_entities(hass, entry, async_expected_preset_ids(runtime))
    else:
        # A blueprint has no runtime of its own: it is configuration for the
        # presets following it. The runtime only remembers its definition, so
        # that a deleted blueprint can still hand it over.
        runtime.async_load_blueprints()

    if platforms := PLATFORMS[kind]:
        await hass.config_entries.async_forward_entry_setups(entry, platforms)
    entry.async_on_unload(entry.add_update_listener(_async_hub_updated))
    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> bool:
    """Unload one of the hubs."""
    kind = hubs.hub_kind(entry)
    if kind is None:
        return True

    unloaded = True
    if platforms := PLATFORMS[kind]:
        unloaded = await hass.config_entries.async_unload_platforms(entry, platforms)

    # This happens even when a platform refused to unload. Home Assistant marks
    # such an entry as failed and never retries it, so a mode source left
    # running would drive a half torn down runtime, and values not written here
    # would be lost - the hub is going away either way. The unload still
    # reports the failure.
    runtime = entry.runtime_data
    if kind == HUB_PRESET_MODES:
        runtime.async_unload_preset_modes()
    elif kind == HUB_PRESETS:
        runtime.async_unload_presets()
    await runtime.store.async_save_now()
    return unloaded


async def async_remove_entry(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> None:
    """Clean up after a deleted hub.

    Deleting a hub deletes every object in it, and the objects of the other
    hubs keep what they were following: the presets of the deleted blueprints
    inherit their parameters, the presets of the deleted preset modes their
    modes. Same as deleting a single object, only all at once.
    """
    kind = hubs.hub_kind(entry)
    store = await async_setup_store(hass)

    if kind == HUB_PRESETS:
        for subentry_id in entry.subentries:
            store.remove_preset(subentry_id)
    elif kind == HUB_PRESET_MODES:
        for subentry_id, subentry in entry.subentries.items():
            following.async_detach_from_preset_mode(
                hass, subentry_id, subentry.data.get(CONF_MODES, [])
            )
            store.remove_preset_mode(subentry_id)
    elif kind == HUB_BLUEPRINTS:
        for subentry_id, subentry in entry.subentries.items():
            following.async_detach_from_blueprint(
                hass, subentry_id, subentry.data.get(CONF_PARAMETERS, [])
            )
    await store.async_save_now()


async def async_remove_config_entry_device(
    hass: HomeAssistant, entry: PresetManagerConfigEntry, device: DeviceEntry
) -> bool:
    """Allow removing devices that no longer belong to the hub."""
    known = set(entry.subentries)
    return not any(
        domain == DOMAIN and identifier in known
        for domain, identifier in device.identifiers
    )


async def _async_hub_updated(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> None:
    """React to an object being added, changed or deleted.

    Values live outside of the config entries, so this only fires for
    structural changes - modes, presets, parameters, and what follows what.
    A reload is the last resort: it is the only way to add or remove an
    entity, and it takes every other entity of the hub down with it, so the
    runtime first tries to take the change over as it stands.
    """
    runtime = entry.runtime_data
    # First hand a deleted object's definition to whoever followed it: the
    # runtime is the last place it still exists.
    runtime.async_reconcile()

    kind = hubs.hub_kind(entry)
    if kind == HUB_PRESET_MODES:
        if await runtime.async_apply_preset_modes(entry):
            await _async_reload(hass, entry.entry_id)
        else:
            _async_register_preset_mode_devices(hass, entry, runtime)
    elif kind == HUB_BLUEPRINTS:
        runtime.async_load_blueprints()

    # The presets read their modes from the preset modes hub and their
    # parameters from the blueprints hub, so any of the three changes them.
    presets = hubs.async_hub(hass, HUB_PRESETS)
    if presets is None or presets.state is not ConfigEntryState.LOADED:
        return
    if runtime.async_apply_presets(presets):
        await _async_reload(hass, presets.entry_id)
    else:
        _async_rename_preset_devices(hass, runtime)


async def _async_reload(hass: HomeAssistant, entry_id: str) -> None:
    """Reload a hub that is currently loaded."""
    entry = hass.config_entries.async_get_entry(entry_id)
    if entry is not None and entry.state is not None and entry.state.recoverable:
        await hass.config_entries.async_reload(entry_id)


def _async_register_preset_mode_devices(
    hass: HomeAssistant,
    entry: PresetManagerConfigEntry,
    runtime: PresetManagerRuntime,
) -> None:
    """Create the device of every preset mode.

    They have to exist before the platforms are set up, because the entities
    of a preset mode are added to them.
    """
    registry = dr.async_get(hass)
    for subentry_id, coordinator in runtime.preset_modes.items():
        registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            config_subentry_id=subentry_id,
            identifiers={(DOMAIN, subentry_id)},
            name=coordinator.config.name,
            manufacturer=MANUFACTURER,
            model=MODEL_PRESET_MODE,
            entry_type=DeviceEntryType.SERVICE,
        )


def _async_rename_preset_devices(
    hass: HomeAssistant, runtime: PresetManagerRuntime
) -> None:
    """Follow the renaming of a preset on its device.

    The entities take their name from the device, so this is all a rename
    needs - and a name the user gave the device themselves is untouched by it.
    """
    registry = dr.async_get(hass)
    for subentry_id, coordinator in runtime.presets.items():
        device = registry.async_get_device(identifiers={(DOMAIN, subentry_id)})
        if device is not None and device.name != coordinator.config.name:
            registry.async_update_device(device.id, name=coordinator.config.name)


def _async_remove_stale_entities(
    hass: HomeAssistant,
    entry: PresetManagerConfigEntry,
    expected: set[str],
) -> None:
    """Remove registry entries that no longer exist in the configuration."""
    registry = er.async_get(hass)
    for registry_entry in er.async_entries_for_config_entry(registry, entry.entry_id):
        if registry_entry.unique_id not in expected:
            _LOGGER.debug("Removing stale entity %s", registry_entry.entity_id)
            registry.async_remove(registry_entry.entity_id)
