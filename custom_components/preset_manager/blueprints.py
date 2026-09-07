"""Blueprints: one parameter list, shared by any number of presets.

A blueprint is a config entry of its own, holding nothing but parameter
definitions ("Heating" with a target temperature and a boost duration, ...). A
preset can follow one instead of defining parameters itself, and then the set is
the only place its parameters can be edited.

The preset stores nothing but the entry id of the blueprint (``blueprint``); the
parameters are resolved from the set on every setup and are deliberately **not**
copied into the preset. One source of truth is what makes the promise hold:
there is no second copy that could drift, a set that changed while a preset mode was
disabled still arrives the moment that preset mode loads again, and "is this preset
free or bound?" is one key rather than a comparison of two lists.

What follows a preset instead of the set are its *values*: those stay per preset
and per mode, which is the whole point of sharing only the definitions.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntry, ConfigEntryState, ConfigSubentry
from homeassistant.core import HomeAssistant, callback

from .const import (
    CONF_BLUEPRINT,
    CONF_ENTRY_TYPE,
    CONF_PARAMETERS,
    DOMAIN,
    ENTRY_TYPE_BLUEPRINT,
    ENTRY_TYPE_PRESET_MODE,
    SUBENTRY_TYPE_PRESET,
)
from .store import async_get_store

_LOGGER = logging.getLogger(__name__)


@callback
def entry_type(entry: ConfigEntry) -> str:
    """Return the kind of a config entry.

    The marker is written explicitly, so a third kind of entry is an addition
    rather than a migration. Reading stays tolerant: an entry without the key
    is a preset mode, which is the only kind that ever existed without one.
    """
    return entry.data.get(CONF_ENTRY_TYPE, ENTRY_TYPE_PRESET_MODE)


@callback
def is_blueprint(entry: ConfigEntry) -> bool:
    """Return whether ``entry`` is a blueprint rather than a preset mode."""
    return entry_type(entry) == ENTRY_TYPE_BLUEPRINT


@callback
def async_blueprints(hass: HomeAssistant) -> list[ConfigEntry]:
    """Return every blueprint."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if is_blueprint(entry)
    ]


@callback
def async_preset_modes(hass: HomeAssistant) -> list[ConfigEntry]:
    """Return every preset mode."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if not is_blueprint(entry)
    ]


@callback
def parameters_of(entry: ConfigEntry) -> list[dict[str, Any]]:
    """Return the stored parameter definitions of a blueprint."""
    return [dict(item) for item in entry.data.get(CONF_PARAMETERS, [])]


@callback
def async_resolve_preset_data(
    hass: HomeAssistant, data: Mapping[str, Any]
) -> Mapping[str, Any]:
    """Return the data of a preset with the parameters of its set filled in.

    A preset that follows no set is returned untouched. A preset whose set no
    longer exists keeps whatever parameters it has - which is nothing, unless a
    backup was restored without the set - and says so in the log instead of
    failing the setup.
    """
    set_entry_id = data.get(CONF_BLUEPRINT)
    if not set_entry_id:
        return data
    entry = hass.config_entries.async_get_entry(set_entry_id)
    if entry is None or not is_blueprint(entry):
        _LOGGER.warning(
            "Preset follows the blueprint %s, which does not exist; "
            "its parameters stay empty until it is attached to another set",
            set_entry_id,
        )
        return data
    return {**data, CONF_PARAMETERS: parameters_of(entry)}


@callback
def async_bound_presets(
    hass: HomeAssistant, set_entry_id: str
) -> Iterator[tuple[ConfigEntry, ConfigSubentry]]:
    """Yield every preset following the blueprint, with its preset mode."""
    for entry in async_preset_modes(hass):
        for subentry in entry.subentries.values():
            if (
                subentry.subentry_type == SUBENTRY_TYPE_PRESET
                and subentry.data.get(CONF_BLUEPRINT) == set_entry_id
            ):
                yield entry, subentry


async def async_apply_blueprint(hass: HomeAssistant, set_entry_id: str) -> None:
    """Bring every preset following the set in line with it.

    Nothing is written: the presets read the set on setup, so reloading their
    preset mode is the whole update. One reload per preset mode, however many of its
    presets follow the set.
    """
    entry_ids = {entry.entry_id for entry, _ in async_bound_presets(hass, set_entry_id)}
    for entry_id in entry_ids:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.state is ConfigEntryState.LOADED:
            await hass.config_entries.async_reload(entry_id)


@callback
def async_forget_parameters(
    hass: HomeAssistant, set_entry_id: str, parameter_keys: set[str]
) -> None:
    """Drop the stored values of parameters that changed their type.

    A retyped parameter keeps its key, so its values would survive a change they
    no longer fit - the same reason the preset's own parameter editor drops
    them, applied to every preset the set reaches.
    """
    if not parameter_keys or (store := async_get_store(hass)) is None:
        return
    for _, subentry in async_bound_presets(hass, set_entry_id):
        for key in parameter_keys:
            store.remove_parameter(subentry.subentry_id, key)


@callback
def async_detach_presets(hass: HomeAssistant, set_entry: ConfigEntry) -> None:
    """Turn every preset of a deleted set back into a free-standing one.

    The parameters of the set are copied into the preset on the way out, so
    deleting a set costs its presets their lock, not their configuration or
    their values.
    """
    parameters = parameters_of(set_entry)
    for entry, subentry in async_bound_presets(hass, set_entry.entry_id):
        data = {
            key: value for key, value in subentry.data.items() if key != CONF_BLUEPRINT
        }
        data[CONF_PARAMETERS] = [dict(item) for item in parameters]
        hass.config_entries.async_update_subentry(entry, subentry, data=data)
        _LOGGER.debug(
            "Preset '%s' kept the parameters of the deleted set '%s'",
            subentry.title,
            set_entry.title,
        )
