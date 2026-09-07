"""Persistent storage for mode values and the active mode.

Mode *values* change often (every slider move on a dashboard), therefore they
are deliberately **not** stored in the config entry: rewriting a config entry
triggers update listeners and a reload of the integration. Instead they live in
a debounced :class:`homeassistant.helpers.storage.Store`, while the config entry
only holds the *structure* (modes, presets, parameters).
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.storage import Store

from .const import (
    DATA_STORE,
    DOMAIN,
    SAVE_DELAY,
    STORAGE_KEY,
    STORAGE_MINOR_VERSION,
    STORAGE_VERSION,
    STORE_ACTIVE_MODES,
    STORE_AUTOMATIC,
    STORE_VALUES,
)

_LOGGER = logging.getLogger(__name__)

type ValueMap = dict[str, dict[str, dict[str, Any]]]


class _ValueFileStore(Store[dict[str, Any]]):
    """The storage file, with a migration path of its own.

    ``Store._async_migrate_func`` raises by default, so a file written by an
    older version would take the whole setup down instead of being converted.
    The hook exists from the first release on for that reason - by the time a
    format change is needed, users already have values in this file.
    """

    async def _async_migrate_func(
        self,
        old_major_version: int,
        old_minor_version: int,
        old_data: dict[str, Any],
    ) -> dict[str, Any]:
        """Bring stored data up to the current format."""
        if old_major_version > STORAGE_VERSION:
            raise ValueError(
                f"{STORAGE_KEY} was written by a newer version of "
                f"{DOMAIN} (storage version {old_major_version}) "
                "and cannot be read by this one"
            )

        # Migration steps go here, smallest version first.

        return old_data


class PresetValueStore:
    """Stores the values of every preset and the state of every preset mode.

    Presets are keyed by their subentry id and preset modes by their
    config entry id. Both are stable across renames. The file is shared by every
    config entry of the integration, so a single instance of this class has to
    be used - two instances would overwrite each other's data.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the store."""
        self._store = _ValueFileStore(
            hass,
            STORAGE_VERSION,
            STORAGE_KEY,
            atomic_writes=True,
            minor_version=STORAGE_MINOR_VERSION,
        )
        self._values: ValueMap = {}
        self._active_modes: dict[str, str] = {}
        self._automatic: dict[str, bool] = {}

    async def async_load(self) -> None:
        """Load persisted data."""
        data = await self._store.async_load()
        if not data:
            return
        self._active_modes = dict(data.get(STORE_ACTIVE_MODES) or {})
        self._automatic = dict(data.get(STORE_AUTOMATIC) or {})
        raw_values = data.get(STORE_VALUES) or {}
        self._values = {
            preset_id: {
                mode_key: dict(parameters) for mode_key, parameters in modes.items()
            }
            for preset_id, modes in raw_values.items()
        }

    async def async_save_now(self) -> None:
        """Write pending data immediately (used on unload)."""
        await self._store.async_save(self._as_dict())

    def _as_dict(self) -> dict[str, Any]:
        return {
            STORE_ACTIVE_MODES: self._active_modes,
            STORE_AUTOMATIC: self._automatic,
            STORE_VALUES: self._values,
        }

    def _schedule_save(self) -> None:
        self._store.async_delay_save(self._as_dict, SAVE_DELAY)

    # Active mode ----------------------------------------------------------

    def active_mode(self, preset_mode_id: str) -> str | None:
        """Return the persisted active mode key of a preset mode."""
        return self._active_modes.get(preset_mode_id)

    def set_active_mode(self, preset_mode_id: str, mode_key: str | None) -> bool:
        """Persist the active mode of a preset mode. ``True`` when it changed."""
        if self._active_modes.get(preset_mode_id) == mode_key:
            return False
        if mode_key is None:
            self._active_modes.pop(preset_mode_id, None)
        else:
            self._active_modes[preset_mode_id] = mode_key
        self._schedule_save()
        return True

    def automatic(self, preset_mode_id: str) -> bool:
        """Return whether a preset mode follows its source.

        Defaults to ``True``: a preset mode with a source configured is meant to
        run on its own until the user switches it off.
        """
        return self._automatic.get(preset_mode_id, True)

    def set_automatic(self, preset_mode_id: str, value: bool) -> bool:
        """Persist the automatic flag. Returns ``True`` when it changed."""
        if self._automatic.get(preset_mode_id, True) == value:
            return False
        self._automatic[preset_mode_id] = value
        self._schedule_save()
        return True

    def remove_preset_mode(self, preset_mode_id: str) -> None:
        """Drop the persisted state of a preset mode."""
        changed = self._active_modes.pop(preset_mode_id, None) is not None
        changed |= self._automatic.pop(preset_mode_id, None) is not None
        if changed:
            self._schedule_save()

    def prune_preset_modes(self, preset_mode_ids: Iterable[str]) -> None:
        """Remove state of preset modes that no longer exist."""
        known = set(preset_mode_ids)
        stale = [item for item in self._active_modes if item not in known]
        stale += [item for item in self._automatic if item not in known]
        for stale_id in stale:
            self._active_modes.pop(stale_id, None)
            self._automatic.pop(stale_id, None)
        if stale:
            self._schedule_save()

    # Values ------------------------------------------------------------------

    def get_value(
        self, preset_id: str, mode_key: str, parameter_key: str
    ) -> Any | None:
        """Return a single stored value or ``None``."""
        return self._values.get(preset_id, {}).get(mode_key, {}).get(parameter_key)

    def has_value(self, preset_id: str, mode_key: str, parameter_key: str) -> bool:
        """Return whether a value is stored."""
        return parameter_key in self._values.get(preset_id, {}).get(mode_key, {})

    def get_mode_values(self, preset_id: str, mode_key: str) -> dict[str, Any]:
        """Return a copy of all stored values of one mode."""
        return dict(self._values.get(preset_id, {}).get(mode_key, {}))

    def set_value(
        self, preset_id: str, mode_key: str, parameter_key: str, value: Any
    ) -> bool:
        """Store a value. Returns ``True`` when it changed."""
        modes = self._values.setdefault(preset_id, {})
        parameters = modes.setdefault(mode_key, {})
        if parameters.get(parameter_key) == value and parameter_key in parameters:
            return False
        parameters[parameter_key] = value
        self._schedule_save()
        return True

    def set_mode_values(
        self, preset_id: str, mode_key: str, values: Mapping[str, Any]
    ) -> bool:
        """Store several values of one mode at once."""
        changed = False
        for parameter_key, value in values.items():
            changed |= self.set_value(preset_id, mode_key, parameter_key, value)
        return changed

    # Housekeeping ------------------------------------------------------------

    def remove_parameter(self, preset_id: str, parameter_key: str) -> None:
        """Drop the stored values of one parameter across all modes.

        Used when the type of a parameter changes: the key stays the same, so
        the values would survive a change they no longer fit.
        """
        changed = False
        for values in self._values.get(preset_id, {}).values():
            if values.pop(parameter_key, None) is not None:
                changed = True
        if changed:
            self._schedule_save()

    def copy_preset(self, source_id: str, target_id: str) -> None:
        """Copy every stored value of one preset onto another.

        Duplicating a preset without its values would hand back an empty
        shell - the values are what the work went into, and the copy is made
        to have them.
        """
        values = self._values.get(source_id)
        if not values:
            return
        self._values[target_id] = {
            mode_key: dict(parameters) for mode_key, parameters in values.items()
        }
        self._schedule_save()

    def remove_preset(self, preset_id: str) -> None:
        """Drop all values of a preset."""
        if self._values.pop(preset_id, None) is not None:
            self._schedule_save()

    def prune(
        self,
        valid: Mapping[str, tuple[Iterable[str], Iterable[str]]],
        known_presets: Iterable[str],
    ) -> None:
        """Remove values for unknown presets, modes and parameters.

        ``valid`` maps a preset id to a tuple of (mode keys, parameter keys)
        that are still configured; only those presets are cleaned up in detail.
        ``known_presets`` lists the presets of *every* config entry - a preset
        of another, possibly not loaded, preset mode has to keep its values.
        """
        known = set(known_presets)
        changed = False
        for preset_id in list(self._values):
            if preset_id not in known:
                del self._values[preset_id]
                changed = True
                continue
            if preset_id not in valid:
                continue
            mode_keys, parameter_keys = valid[preset_id]
            mode_keys = set(mode_keys)
            parameter_keys = set(parameter_keys)
            modes = self._values[preset_id]
            for mode_key in list(modes):
                if mode_key not in mode_keys:
                    del modes[mode_key]
                    changed = True
                    continue
                parameters = modes[mode_key]
                for parameter_key in list(parameters):
                    if parameter_key not in parameter_keys:
                        del parameters[parameter_key]
                        changed = True
        if changed:
            _LOGGER.debug("Pruned orphaned mode values")
            self._schedule_save()


async def async_setup_store(hass: HomeAssistant) -> PresetValueStore:
    """Create and load the store shared by every config entry."""
    data = hass.data.setdefault(DOMAIN, {})
    if (store := data.get(DATA_STORE)) is None:
        store = PresetValueStore(hass)
        await store.async_load()
        data[DATA_STORE] = store
    return store


@callback
def async_get_store(hass: HomeAssistant) -> PresetValueStore | None:
    """Return the shared store, if the integration has been set up."""
    return hass.data.get(DOMAIN, {}).get(DATA_STORE)
