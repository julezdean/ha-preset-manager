"""Where the objects of the integration live.

The domain owns three config entries and nothing else. Each of them is a hub
collecting one kind of object as its subentries:

    Preset Modes      preset mode      the modes plus the rule picking one
    Presets           preset           the parameters of one device, per mode
    Preset Blueprints blueprint        parameter definitions, shared

Nothing is contained in anything else. A preset names the preset mode it
follows and the blueprint it follows, both by subentry id, and both references
may point at nothing: a preset outlives the deletion of either and says so
rather than disappearing with it. That is the whole reason the objects are
siblings instead of a hierarchy - a blueprint is shared across preset modes and
belongs to none of them, and a preset is worth keeping when its dimension goes.

Everything here reads the *configuration*, not the runtime, and therefore works
for a hub that is not loaded: which modes a preset has must not depend on
whether the Preset Modes hub happened to be set up first.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigSubentry, DiscoveryKey
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_BLUEPRINT,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    DOMAIN,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
    HUB_SUBENTRY_TYPES,
)

#: A hub is created by the config flow or by the migration, never found: it
#: has no discovery keys, and Home Assistant wants the mapping spelled out.
NO_DISCOVERY_KEYS: MappingProxyType[str, tuple[DiscoveryKey, ...]] = MappingProxyType(
    {}
)


@callback
def hub_kind(entry: ConfigEntry) -> str | None:
    """Return which hub ``entry`` is, or ``None`` if it is not one.

    An entry of an older version has no unique id yet; it is migrated into a
    hub before it is ever set up.
    """
    if entry.unique_id in HUB_SUBENTRY_TYPES:
        return entry.unique_id
    return None


@callback
def async_hub(hass: HomeAssistant, kind: str) -> ConfigEntry | None:
    """Return the hub of one kind, if it exists."""
    return next(
        (
            entry
            for entry in hass.config_entries.async_entries(DOMAIN)
            if entry.unique_id == kind
        ),
        None,
    )


@callback
def async_objects(hass: HomeAssistant, kind: str) -> dict[str, ConfigSubentry]:
    """Return every object of one kind, by subentry id."""
    hub = async_hub(hass, kind)
    if hub is None:
        return {}
    wanted = HUB_SUBENTRY_TYPES[kind]
    return {
        subentry.subentry_id: subentry
        for subentry in hub.subentries.values()
        if subentry.subentry_type == wanted
    }


@callback
def async_object(
    hass: HomeAssistant, kind: str, subentry_id: str | None
) -> ConfigSubentry | None:
    """Return one object by id, if it exists."""
    if subentry_id is None:
        return None
    return async_objects(hass, kind).get(subentry_id)


@callback
def async_preset_modes(hass: HomeAssistant) -> dict[str, ConfigSubentry]:
    """Return every preset mode, by subentry id."""
    return async_objects(hass, HUB_PRESET_MODES)


@callback
def async_presets(hass: HomeAssistant) -> dict[str, ConfigSubentry]:
    """Return every preset, by subentry id."""
    return async_objects(hass, HUB_PRESETS)


@callback
def async_blueprints(hass: HomeAssistant) -> dict[str, ConfigSubentry]:
    """Return every blueprint, by subentry id."""
    return async_objects(hass, HUB_BLUEPRINTS)


@callback
def async_resolve_preset_data(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Return the data of a preset with everything it follows filled in.

    Parameters come from its blueprint and modes from its preset mode, and both
    are read on every setup rather than copied into the preset: one source of
    truth is what keeps a change in either from having to be written anywhere.

    What a preset follows may be gone. Its parameters are then whatever it
    carries itself, and its modes are the snapshot taken when the preset mode
    was deleted - see ``following.async_detach_presets_of_preset_mode``.
    """
    resolved = dict(data)
    if blueprint := async_object(hass, HUB_BLUEPRINTS, data.get(CONF_BLUEPRINT)):
        resolved[CONF_PARAMETERS] = [
            dict(item) for item in blueprint.data.get(CONF_PARAMETERS, [])
        ]
    if preset_mode := async_object(hass, HUB_PRESET_MODES, data.get(CONF_PRESET_MODE)):
        resolved[CONF_MODES] = [
            dict(item) for item in preset_mode.data.get(CONF_MODES, [])
        ]
    return resolved
