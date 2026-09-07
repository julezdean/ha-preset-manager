"""Bringing the 0.1.0 layout into the three hubs.

Until 0.1.0 every preset mode and every blueprint was a config entry of its
own, and a preset was a subentry of the preset mode it belonged to. From 0.2.0
on there are three hubs and every object is a subentry (see ``hubs``).

Nothing an existing installation can see changes with it. A subentry id may be
any string, so every object keeps the id it already had - which is what every
device identifier, every entity unique id and every key in the value store is
built from. The registries follow on their own: an entity is looked up by its
unique id and a device by its identifiers, and both are then moved to the hub
that now provides them, with their name, area, icon and history intact. The
old entries are removed once they are empty.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.config_entries import (
    SOURCE_IMPORT,
    ConfigEntry,
    ConfigSubentryDataWithId,
)
from homeassistant.core import HomeAssistant

from . import hubs
from .const import (
    CONF_ENTRY_TYPE,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    CONF_SOURCE_ENTITY,
    DATA_MIGRATION_LOCK,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_TYPE_BLUEPRINT,
    ENTRY_VERSION,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
    HUB_SUBENTRY_TYPES,
    HUB_TITLES,
    SUBENTRY_TYPE_PRESET,
)

_LOGGER = logging.getLogger(__name__)


def _subentry(
    kind: str, subentry_id: str, title: str, data: dict[str, Any]
) -> ConfigSubentryDataWithId:
    """Return one object of a hub, keeping the id it had as an entry."""
    return ConfigSubentryDataWithId(
        data=data,
        subentry_id=subentry_id,
        subentry_type=HUB_SUBENTRY_TYPES[kind],
        title=title,
        unique_id=None,
    )


async def _async_create_hub(
    hass: HomeAssistant, kind: str, subentries: list[ConfigSubentryDataWithId]
) -> None:
    """Create one hub, unless there is nothing to put in it."""
    if not subentries:
        return
    hub = ConfigEntry(
        data={},
        discovery_keys=hubs.NO_DISCOVERY_KEYS,
        domain=DOMAIN,
        minor_version=ENTRY_MINOR_VERSION,
        options={},
        source=SOURCE_IMPORT,
        subentries_data=subentries,
        title=HUB_TITLES[kind],
        unique_id=kind,
        version=ENTRY_VERSION,
    )
    # Adding sets the hub up right away, which is what makes the order below
    # matter: a preset reads its modes from the configuration of the preset
    # modes hub, so that one has to exist before the presets hub is set up.
    await hass.config_entries.async_add(hub)


async def async_migrate_legacy_entries(hass: HomeAssistant) -> None:
    """Move every pre-0.2 config entry into the hubs and remove it.

    Every legacy entry is migrated in one go, however many of them are being
    set up in parallel: the second one finds nothing left to do.
    """
    lock: asyncio.Lock = hass.data.setdefault(DOMAIN, {}).setdefault(
        DATA_MIGRATION_LOCK, asyncio.Lock()
    )
    async with lock:
        legacy = [
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if hubs.hub_kind(entry) is None
        ]
        if not legacy:
            return

        preset_modes: list[ConfigSubentryDataWithId] = []
        presets: list[ConfigSubentryDataWithId] = []
        blueprints: list[ConfigSubentryDataWithId] = []

        for entry in legacy:
            if entry.data.get(CONF_ENTRY_TYPE) == ENTRY_TYPE_BLUEPRINT:
                blueprints.append(
                    _subentry(
                        HUB_BLUEPRINTS,
                        entry.entry_id,
                        entry.title,
                        {
                            CONF_PARAMETERS: [
                                dict(item)
                                for item in entry.data.get(CONF_PARAMETERS, [])
                            ]
                        },
                    )
                )
                continue

            data: dict[str, Any] = {
                CONF_MODES: [dict(item) for item in entry.data.get(CONF_MODES, [])]
            }
            if source_entity := entry.data.get(CONF_SOURCE_ENTITY):
                data[CONF_SOURCE_ENTITY] = source_entity
            preset_modes.append(
                _subentry(HUB_PRESET_MODES, entry.entry_id, entry.title, data)
            )

            for subentry in entry.subentries.values():
                if subentry.subentry_type != SUBENTRY_TYPE_PRESET:
                    continue
                # Containment becomes a reference: the preset now names the
                # preset mode it follows instead of being a part of it.
                presets.append(
                    _subentry(
                        HUB_PRESETS,
                        subentry.subentry_id,
                        subentry.title,
                        dict(subentry.data) | {CONF_PRESET_MODE: entry.entry_id},
                    )
                )

        await _async_create_hub(hass, HUB_PRESET_MODES, preset_modes)
        await _async_create_hub(hass, HUB_BLUEPRINTS, blueprints)
        await _async_create_hub(hass, HUB_PRESETS, presets)

        _LOGGER.info(
            "Migrated %s preset mode(s), %s preset(s) and %s blueprint(s) "
            "into the hubs of %s",
            len(preset_modes),
            len(presets),
            len(blueprints),
            DOMAIN,
        )

        for entry in legacy:
            # The entry being set up right now cannot remove itself, and the
            # hubs have taken over its devices and entities by now, so what is
            # left to remove is an empty entry.
            hass.async_create_task(hass.config_entries.async_remove(entry.entry_id))
