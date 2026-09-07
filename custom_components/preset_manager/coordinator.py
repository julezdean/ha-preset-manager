"""Runtime layer of the Preset Mode.

The integration is fully push based: nothing is polled, so the coordinators are
used purely as Home Assistant's standard listener plumbing. A state is only
pushed to the entities when the computed result actually changed, which keeps
setups with many preset_modes, presets, modes and parameters cheap.

One config entry is one preset mode, its subentries are the presets that
follow it:

    PresetModeRuntime        everything the config entry owns
        |- PresetModeCoordinator       the modes of the preset mode + the active one
        |     |- ModeSource   manual, the conditions, or another entity
        |- PresetCoordinator     resolves the values of one preset
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify

from .blueprints import async_resolve_preset_data
from .const import DOMAIN, SUBENTRY_TYPE_PRESET
from .models import ModeDef, ParameterDef, PresetConfig, PresetModeConfig
from .parameter_types import ParameterValueError, coerce_value
from .sources import ModeSource, create_source
from .store import PresetValueStore

_LOGGER = logging.getLogger(__name__)

type PresetModeConfigEntry = ConfigEntry[PresetModeRuntime]


@dataclass(frozen=True, kw_only=True, slots=True)
class PresetState:
    """Resolved state of one preset."""

    mode_key: str | None
    mode_name: str | None
    #: Resolved value per parameter key (``None`` = unknown).
    values: dict[str, Any] = field(default_factory=dict)
    #: Parameters without a stored value and without a default.
    unset_parameters: tuple[str, ...] = ()


class PresetModeRuntime:
    """Holds the preset mode of one config entry and all its presets."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: PresetModeConfigEntry,
        store: PresetValueStore,
    ) -> None:
        """Initialise the runtime."""
        self.hass = hass
        self.entry = entry
        self.store = store
        self.preset_mode = PresetModeCoordinator(
            self, PresetModeConfig.from_entry(entry.entry_id, entry.title, entry.data)
        )
        self.presets: dict[str, PresetCoordinator] = {}

    async def async_initialize(self) -> None:
        """Build the preset coordinators and start the mode source."""
        for subentry in self.entry.subentries.values():
            if subentry.subentry_type != SUBENTRY_TYPE_PRESET:
                continue
            config = PresetConfig.from_subentry(
                subentry.subentry_id,
                subentry.title,
                # A preset following a blueprint has no parameters of its
                # own; they are read from the set on every setup.
                async_resolve_preset_data(self.hass, subentry.data),
            )
            coordinator = PresetCoordinator(self, config, self.preset_mode)
            self.presets[subentry.subentry_id] = coordinator
            self.preset_mode.presets.append(coordinator)

        self.preset_mode.async_initialize()
        for preset in self.presets.values():
            preset.async_initialize()
        await self.preset_mode.async_start_source()

        self.async_prune_store()

    @callback
    def async_shutdown(self) -> None:
        """Stop the mode source."""
        self.preset_mode.async_stop_source()

    @callback
    def async_prune_store(self) -> None:
        """Remove stored data that no longer belongs to the configuration.

        The store is shared by every config entry, so what may be dropped is
        decided from *all* entries of the domain - including the ones that are
        not loaded right now. Only the presets of this entry are cleaned up in
        detail, because only their configuration is known here.
        """
        valid = {
            preset_id: (
                [mode.key for mode in preset.modes],
                [parameter.key for parameter in preset.config.parameters],
            )
            for preset_id, preset in self.presets.items()
        }
        entries = self.hass.config_entries.async_entries(DOMAIN)
        self.store.prune(
            valid,
            {subentry_id for entry in entries for subentry_id in entry.subentries},
        )
        self.store.prune_preset_modes({entry.entry_id for entry in entries})


class PresetModeCoordinator(DataUpdateCoordinator[str | None]):
    """Owns one set of modes and knows which of them is active."""

    def __init__(self, runtime: PresetModeRuntime, config: PresetModeConfig) -> None:
        """Initialise the preset mode coordinator."""
        super().__init__(
            runtime.hass,
            _LOGGER,
            name=f"{DOMAIN}.{config.entry_id}",
            config_entry=runtime.entry,
            update_interval=None,
            always_update=False,
        )
        self.runtime = runtime
        self.config = config
        self.presets: list[PresetCoordinator] = []
        self._source: ModeSource | None = None

    # Setup -------------------------------------------------------------------

    @callback
    def async_initialize(self) -> None:
        """Determine the mode that is active right after a restart."""
        self.data = self._initial_mode_key()

    async def async_start_source(self) -> None:
        """Create and start the source that drives the active mode."""
        self._source = create_source(self)
        await self._source.async_start()

    @callback
    def async_stop_source(self) -> None:
        """Stop the source."""
        if self._source is not None:
            self._source.async_stop()
            self._source = None

    def _initial_mode_key(self) -> str | None:
        """Return the mode to start with; the source corrects it right after.

        A manual preset mode has no source to correct it, so it starts on its first
        mode - the same mode the condition source would pick, where every
        mode is a match because none of them has conditions.
        """
        stored = self.store.active_mode(self.config.entry_id)
        if stored and self.config.mode(stored) is not None:
            return stored
        if self.has_source or self.external or not self.config.modes:
            return None
        return self.config.modes[0].key

    @property
    def store(self) -> PresetValueStore:
        """Return the value store."""
        return self.runtime.store

    @property
    def modes(self) -> tuple[ModeDef, ...]:
        """Return the modes of this preset mode."""
        return self.config.modes

    @property
    def external(self) -> bool:
        """Return whether another entity decides the mode."""
        return self.config.is_external

    @property
    def has_source(self) -> bool:
        """Return whether the automatic can be switched off.

        Only the conditions can: an external preset mode is not something the user
        takes over by hand, it belongs to the entity it follows.
        """
        return self.config.has_conditions

    @property
    def automatic(self) -> bool:
        """Return whether the mode currently follows its conditions."""
        return self.has_source and self.store.automatic(self.config.entry_id)

    @property
    def writable(self) -> bool:
        """Return whether the active mode may be set by hand."""
        return not self.automatic and not self.external

    @property
    def source_kind(self) -> str:
        """Return the name of the source currently driving the active mode.

        Which source was built is the first thing to know when a preset mode
        reports the wrong mode, and it is not derivable from the outside:
        ``diagnostics.py`` reports what is actually running rather than what
        the configuration would imply.
        """
        return "none" if self._source is None else type(self._source).__name__

    # Modes ----------------------------------------------------------------

    @property
    def active_mode_key(self) -> str | None:
        """Return the active mode key."""
        return self.data

    @property
    def active_mode(self) -> ModeDef | None:
        """Return the active mode."""
        return self.config.mode(self.data)

    def mode_by_name(self, name: str) -> ModeDef | None:
        """Return a mode by (case insensitive) display name."""
        lowered = name.casefold()
        return next(
            (item for item in self.modes if item.name.casefold() == lowered), None
        )

    def resolve_mode(self, value: str) -> ModeDef | None:
        """Resolve a mode from a key, a display name or a slug."""
        return (
            self.config.mode(value)
            or self.mode_by_name(value)
            or self.config.mode(slugify(value))
        )

    async def async_set_automatic(self, value: bool) -> None:
        """Switch between following the source and setting the mode by hand."""
        if not self.store.set_automatic(self.config.entry_id, value):
            return
        if value and self._source is not None:
            # Do not wait for the next event to catch up with the source.
            await self._source.async_refresh()
        self.async_update_listeners()

    @callback
    def async_apply_from_source(self, mode_key: str | None) -> None:
        """Apply a mode proposed by the source, unless it is switched off."""
        if not self.external and not self.automatic:
            return
        self.async_apply_mode(mode_key)

    @callback
    def async_set_active_mode(self, value: str) -> None:
        """Set the active mode from a key or display name."""
        if self.external:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="external_source",
                translation_placeholders={
                    "preset_mode": self.config.name,
                    "entity_id": self.config.source_entity or "",
                },
            )
        if not self.writable:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="automatic_active",
                translation_placeholders={"preset_mode": self.config.name},
            )
        mode = self.resolve_mode(value)
        if mode is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_mode",
                translation_placeholders={
                    "mode": value,
                    "modes": ", ".join(item.name for item in self.modes),
                },
            )
        self.async_apply_mode(mode.key)

    @callback
    def async_apply_mode(self, mode_key: str | None) -> None:
        """Activate a mode and update everything that depends on it."""
        if self.data == mode_key:
            return
        self.store.set_active_mode(self.config.entry_id, mode_key)
        self.async_set_updated_data(mode_key)
        for preset in self.presets:
            preset.async_update_state()


class PresetCoordinator(DataUpdateCoordinator[PresetState]):
    """Resolves the currently valid values of a single preset."""

    def __init__(
        self,
        runtime: PresetModeRuntime,
        config: PresetConfig,
        preset_mode: PresetModeCoordinator,
    ) -> None:
        """Initialise the preset coordinator."""
        super().__init__(
            runtime.hass,
            _LOGGER,
            name=f"{DOMAIN}.{config.subentry_id}",
            config_entry=runtime.entry,
            update_interval=None,
            always_update=False,
        )
        self.runtime = runtime
        self.config = config
        self.preset_mode = preset_mode
        #: Listeners per (mode key, parameter key). Keyed rather than flat: a
        #: flat list meant one slider move rewrote the state of every editor
        #: entity of the preset - P x N of them, all but one with the value
        #: they already had.
        self._raw_listeners: dict[tuple[str, str], list[Callable[[], None]]] = {}

    @callback
    def async_initialize(self) -> None:
        """Compute the initial state."""
        self.data = self._compute_state()

    @property
    def store(self) -> PresetValueStore:
        """Return the value store."""
        return self.runtime.store

    @property
    def modes(self) -> list[ModeDef]:
        """Return the modes of the preset mode this preset belongs to."""
        return list(self.preset_mode.modes)

    # Listeners ---------------------------------------------------------------

    @callback
    def async_add_raw_listener(
        self, mode_key: str, parameter_key: str, update_callback: Callable[[], None]
    ) -> CALLBACK_TYPE:
        """Subscribe to changes of one mode/parameter combination."""
        key = (mode_key, parameter_key)
        listeners = self._raw_listeners.setdefault(key, [])
        listeners.append(update_callback)

        @callback
        def remove_listener() -> None:
            if update_callback in listeners:
                listeners.remove(update_callback)
            if not listeners:
                self._raw_listeners.pop(key, None)

        return remove_listener

    @callback
    def _async_notify_raw_listeners(self, mode_key: str, parameter_key: str) -> None:
        """Notify the entity editing this one mode/parameter combination."""
        for update_callback in list(
            self._raw_listeners.get((mode_key, parameter_key), ())
        ):
            update_callback()

    # Resolution --------------------------------------------------------------

    def _resolve_mode(self) -> str | None:
        """Return the effective mode key.

        A preset covers every mode of its preset mode, so the active mode is
        always usable. Only a preset mode without modes leaves it undefined.
        """
        active = self.preset_mode.active_mode_key
        if active is not None and self.preset_mode.config.mode(active) is not None:
            return active
        return None

    def _resolve_value(
        self, mode_key: str | None, parameter: ParameterDef
    ) -> tuple[Any, bool]:
        """Return the value of ``parameter`` for ``mode_key``."""
        if mode_key is not None and self.store.has_value(
            self.config.subentry_id, mode_key, parameter.key
        ):
            raw = self.store.get_value(self.config.subentry_id, mode_key, parameter.key)
            try:
                return coerce_value(raw, parameter), False
            except ParameterValueError:
                _LOGGER.warning(
                    "Stored value %r of %s/%s is not valid for type '%s'",
                    raw,
                    self.config.name,
                    parameter.name,
                    parameter.type,
                )
        if parameter.default is not None:
            try:
                return coerce_value(parameter.default, parameter), False
            except ParameterValueError:
                pass
        # Unset is ``unknown``, for every type, with no way for a type to
        # opt out. A boolean used to fall back to ``False`` here and a text to
        # ``""``, which made "nobody set this" indistinguishable from a
        # deliberate off or a deliberate empty string - while the editor
        # entity for that very value already reported ``unknown``.
        return None, True

    def _compute_state(self) -> PresetState:
        mode_key = self._resolve_mode()
        mode = self.preset_mode.config.mode(mode_key)
        values: dict[str, Any] = {}
        unset: list[str] = []
        for parameter in self.config.parameters:
            value, is_unset = self._resolve_value(mode_key, parameter)
            values[parameter.key] = value
            if is_unset:
                unset.append(parameter.key)
        return PresetState(
            mode_key=mode_key,
            mode_name=mode.name if mode else None,
            values=values,
            unset_parameters=tuple(unset),
        )

    @callback
    def async_update_state(self) -> None:
        """Recompute the state and notify listeners only if it changed."""
        new_state = self._compute_state()
        if new_state == self.data:
            return
        self.async_set_updated_data(new_state)

    # Values ------------------------------------------------------------------

    def get_raw_value(self, mode_key: str, parameter: ParameterDef) -> Any | None:
        """Return the configured value of a parameter in a specific mode."""
        if self.store.has_value(self.config.subentry_id, mode_key, parameter.key):
            raw = self.store.get_value(self.config.subentry_id, mode_key, parameter.key)
            try:
                return coerce_value(raw, parameter)
            except ParameterValueError:
                return None
        if parameter.default is None:
            return None
        try:
            return coerce_value(parameter.default, parameter)
        except ParameterValueError:
            return None

    @callback
    def async_set_value(self, mode_key: str, parameter_key: str, value: Any) -> None:
        """Validate and store a value, then update the affected entities."""
        parameter = self.config.parameter(parameter_key)
        if parameter is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unknown_parameter",
                translation_placeholders={
                    "parameter": parameter_key,
                    "preset": self.config.name,
                    "parameters": ", ".join(
                        item.key for item in self.config.parameters
                    ),
                },
            )
        if not any(mode.key == mode_key for mode in self.modes):
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unsupported_mode",
                translation_placeholders={
                    "mode": mode_key,
                    "preset": self.config.name,
                    "modes": ", ".join(item.name for item in self.modes),
                },
            )
        try:
            coerced = coerce_value(value, parameter)
        except ParameterValueError as err:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_value",
                translation_placeholders={
                    "value": str(value),
                    "parameter": parameter.name,
                    "error": str(err),
                },
            ) from err

        if not self.store.set_value(
            self.config.subentry_id, mode_key, parameter_key, coerced
        ):
            return
        self._async_notify_raw_listeners(mode_key, parameter_key)
        self.async_update_state()
