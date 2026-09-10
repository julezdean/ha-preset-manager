"""Runtime layer of the Preset Mode.

The integration is fully push based: nothing is polled, so the coordinators are
used purely as Home Assistant's standard listener plumbing. A state is only
pushed to the entities when the computed result actually changed, which keeps
setups with many preset_modes, presets, modes and parameters cheap.

The objects live in three hubs (see ``hubs``), so the runtime belongs to the
domain rather than to a config entry:

    PresetManagerRuntime          everything the domain owns
        |- PresetModeCoordinator  the modes of one preset mode + the active one
        |     |- ModeSource       manual, the conditions, or another entity
        |- PresetCoordinator      resolves the values of one preset

A preset coordinator is *attached* to the coordinator of the preset mode it
follows, and lives without one: the hubs are set up in whatever order Home
Assistant picks, and a preset outlives the deletion of its preset mode. It
therefore takes its modes from its own configuration and asks the preset mode
for one thing only - which of them is active right now. It may also decline to
ask: a preset has an automatic of its own, and with it off the mode is the one
somebody set on the preset itself.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import following, hubs
from .const import CONF_PARAMETERS, DATA_RUNTIME, DOMAIN
from .models import (
    ModeDef,
    ParameterDef,
    PresetConfig,
    PresetModeConfig,
    modes_to_data,
    resolve_mode,
)
from .parameter_types import ParameterValueError, coerce_value
from .sources import ModeSource, create_source
from .store import PresetValueStore, async_setup_store

_LOGGER = logging.getLogger(__name__)

type PresetManagerConfigEntry = ConfigEntry[PresetManagerRuntime]


def _preset_mode_shape(config: PresetModeConfig) -> tuple[Any, ...]:
    """Return what about a preset mode decides which entities exist.

    The conditions and the name are not in it: a renamed mode keeps its key,
    and both are read on every state instead of being baked into an entity.
    Whether it follows an entity is, because that is what the mode selector
    exists or does not exist for.
    """
    return (
        tuple(replace(mode, conditions=()) for mode in config.modes),
        config.is_external,
        config.has_conditions,
    )


def _preset_shape(config: PresetConfig) -> tuple[Any, ...]:
    """Return what about a preset decides which entities exist.

    One editor entity per mode and parameter, and one value entity per
    parameter - so the definitions themselves are in it, not only their keys:
    a changed range or a renamed mode is carried by the entity, not looked up.
    """
    return (config.modes, config.parameters)


@dataclass(frozen=True, kw_only=True, slots=True)
class PresetState:
    """Resolved state of one preset."""

    mode_key: str | None
    mode_name: str | None
    #: Resolved value per parameter key (``None`` = unknown).
    values: dict[str, Any] = field(default_factory=dict)
    #: Parameters without a stored value and without a default.
    unset_parameters: tuple[str, ...] = ()


class PresetManagerRuntime:
    """Everything the domain owns, across all three hubs.

    The coordinators are keyed by subentry id, not reachable through whichever
    config entry happens to hold them: presets and preset modes live in
    different hubs, either of which can be loaded, reloaded or disabled while
    the other stays up. What links them is :meth:`async_attach`, and it runs
    whenever either side changes.
    """

    def __init__(self, hass: HomeAssistant, store: PresetValueStore) -> None:
        """Initialise the runtime of the domain."""
        self.hass = hass
        self.store = store
        #: Every preset mode of a loaded hub, by subentry id.
        self.preset_modes: dict[str, PresetModeCoordinator] = {}
        #: Every preset of a loaded hub, by subentry id.
        self.presets: dict[str, PresetCoordinator] = {}
        #: Last known parameters of every blueprint, by subentry id. A deleted
        #: blueprint is already gone from the configuration when we hear about
        #: it, so this is where the copy its presets inherit comes from.
        self.blueprints: dict[str, list[dict[str, Any]]] = {}

    # Loading -----------------------------------------------------------------

    async def async_load_preset_modes(self, entry: PresetManagerConfigEntry) -> None:
        """Build a coordinator for every configured preset mode."""
        for subentry_id, subentry in hubs.async_preset_modes(self.hass).items():
            coordinator = PresetModeCoordinator(
                self,
                PresetModeConfig.from_subentry(
                    subentry_id, subentry.title, subentry.data
                ),
                entry,
            )
            self.preset_modes[subentry_id] = coordinator
            coordinator.async_initialize()

        self.async_attach()
        for coordinator in self.preset_modes.values():
            await coordinator.async_start_source()
        self.async_prune_store()

    @callback
    def async_unload_preset_modes(self) -> None:
        """Drop every preset mode coordinator; the presets stay."""
        for coordinator in self.preset_modes.values():
            coordinator.async_stop_source()
        self.preset_modes.clear()
        self.async_attach()

    @callback
    def async_load_presets(self, entry: PresetManagerConfigEntry) -> None:
        """Build a coordinator for every configured preset."""
        for subentry_id, subentry in hubs.async_presets(self.hass).items():
            config = PresetConfig.from_subentry(
                subentry_id,
                subentry.title,
                # What the preset follows is read here, once per setup, from
                # the configuration of the other hubs - loaded or not.
                hubs.async_resolve_preset_data(self.hass, subentry.data),
            )
            coordinator = PresetCoordinator(self, config, entry)
            self.presets[subentry_id] = coordinator
            coordinator.async_initialize()

        self.async_attach()
        self.async_prune_store()

    @callback
    def async_unload_presets(self) -> None:
        """Drop every preset coordinator."""
        self.presets.clear()
        self.async_attach()

    @callback
    def async_load_blueprints(self) -> None:
        """Remember the parameters of every blueprint."""
        self.blueprints = {
            subentry_id: [dict(item) for item in subentry.data.get(CONF_PARAMETERS, [])]
            for subentry_id, subentry in hubs.async_blueprints(self.hass).items()
        }

    # Wiring ------------------------------------------------------------------

    @callback
    def async_attach(self) -> None:
        """Link every preset to the preset mode it follows.

        A preset whose preset mode is configured but not loaded is not
        orphaned - it waits, and its editors keep working. Only a preset
        without any preset mode gets the repair issue.
        """
        for coordinator in self.preset_modes.values():
            coordinator.presets.clear()

        for preset_id, preset in self.presets.items():
            target = (
                self.preset_modes.get(preset.config.preset_mode)
                if preset.config.preset_mode is not None
                else None
            )
            preset.async_attach(target)
            if target is not None:
                target.presets.append(preset)

            if preset.config.is_orphaned:
                following.async_create_orphan_issue(
                    self.hass, preset_id, preset.config.name
                )
            else:
                following.async_clear_orphan_issue(self.hass, preset_id)

    # Updating ----------------------------------------------------------------

    async def async_apply_preset_modes(self, entry: PresetManagerConfigEntry) -> bool:
        """Take a changed configuration over, or ask to be reloaded.

        A reload tears every entity of the hub down and builds it again, which
        is the only way to add or remove one - and a blunt answer to a rename.
        What can be applied in place is applied here; the return value says
        that the change needs the reload after all.
        """
        configured = hubs.async_preset_modes(self.hass)
        if set(configured) != set(self.preset_modes):
            # A preset mode was added or deleted, with its entities.
            return True

        applied: list[tuple[PresetModeCoordinator, PresetModeConfig]] = []
        for subentry_id, subentry in configured.items():
            coordinator = self.preset_modes[subentry_id]
            config = PresetModeConfig.from_subentry(
                subentry_id, subentry.title, subentry.data
            )
            if _preset_mode_shape(config) != _preset_mode_shape(coordinator.config):
                return True
            applied.append((coordinator, config))

        for coordinator, config in applied:
            await coordinator.async_apply_config(config)
        return False

    @callback
    def async_apply_presets(self, entry: PresetManagerConfigEntry) -> bool:
        """Take a changed configuration over, or ask to be reloaded."""
        configured = hubs.async_presets(self.hass)
        if set(configured) != set(self.presets):
            return True

        applied: list[tuple[PresetCoordinator, PresetConfig]] = []
        for subentry_id, subentry in configured.items():
            coordinator = self.presets[subentry_id]
            config = PresetConfig.from_subentry(
                subentry_id,
                subentry.title,
                hubs.async_resolve_preset_data(self.hass, subentry.data),
            )
            if _preset_shape(config) != _preset_shape(coordinator.config):
                return True
            applied.append((coordinator, config))

        for coordinator, config in applied:
            coordinator.async_apply_config(config)
        # What a preset follows is not part of its shape - the same modes can
        # come from another preset mode, or from the snapshot of a deleted one
        # - so the wiring is redone whether or not anything else changed.
        self.async_attach()
        return False

    @callback
    def async_reconcile(self) -> None:
        """Hand a deleted object's definition to the presets that followed it.

        Home Assistant removes a subentry without saying which one went, and by
        the time the update listener runs it is gone from the configuration.
        The loaded runtime is the only place its definition still exists, which
        is why this has to happen here rather than in a flow.
        """
        configured = hubs.async_preset_modes(self.hass)
        for subentry_id, coordinator in list(self.preset_modes.items()):
            if subentry_id not in configured:
                following.async_detach_from_preset_mode(
                    self.hass, subentry_id, modes_to_data(coordinator.config.modes)
                )

        blueprints = hubs.async_blueprints(self.hass)
        for subentry_id, parameters in list(self.blueprints.items()):
            if subentry_id not in blueprints:
                following.async_detach_from_blueprint(
                    self.hass, subentry_id, parameters
                )
        self.async_load_blueprints()

    @callback
    def async_prune_store(self) -> None:
        """Remove stored data that no longer belongs to the configuration.

        Only a loaded preset knows its modes and parameters, so only those are
        cleaned up in detail. What may be dropped entirely is read from the
        configuration of the hubs, which is there whether they are loaded or
        not - values must not depend on what happened to be set up first.
        """
        valid = {
            preset_id: (
                [mode.key for mode in preset.config.modes],
                [parameter.key for parameter in preset.config.parameters],
            )
            for preset_id, preset in self.presets.items()
        }
        self.store.prune(valid, set(hubs.async_presets(self.hass)))
        self.store.prune_preset_modes(set(hubs.async_preset_modes(self.hass)))


async def async_setup_runtime(hass: HomeAssistant) -> PresetManagerRuntime:
    """Return the runtime of the domain, creating it on first use."""
    data = hass.data.setdefault(DOMAIN, {})
    if (runtime := data.get(DATA_RUNTIME)) is None:
        runtime = PresetManagerRuntime(hass, await async_setup_store(hass))
        data[DATA_RUNTIME] = runtime
    return runtime


@callback
def async_get_runtime(hass: HomeAssistant) -> PresetManagerRuntime | None:
    """Return the runtime of the domain, if the integration has been set up."""
    return hass.data.get(DOMAIN, {}).get(DATA_RUNTIME)


class PresetModeCoordinator(DataUpdateCoordinator[str | None]):
    """Owns one set of modes and knows which of them is active."""

    def __init__(
        self,
        runtime: PresetManagerRuntime,
        config: PresetModeConfig,
        entry: PresetManagerConfigEntry,
    ) -> None:
        """Initialise the preset mode coordinator."""
        super().__init__(
            runtime.hass,
            _LOGGER,
            name=f"{DOMAIN}.{config.subentry_id}",
            config_entry=entry,
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
        stored = self.store.active_mode(self.config.subentry_id)
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
        return self.has_source and self.store.automatic(self.config.subentry_id)

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

    def resolve_mode(self, value: str) -> ModeDef | None:
        """Resolve a mode from a key, a display name or a slug."""
        return resolve_mode(self.config.modes, value)

    async def async_apply_config(self, config: PresetModeConfig) -> None:
        """Follow a changed configuration without being rebuilt.

        Only reached for changes that leave every entity in place - a rename,
        other conditions, another source entity. The source is rebuilt from
        the new configuration and evaluated right away, so a corrected
        condition takes effect when it is saved rather than at the next state
        change of whatever it watches.
        """
        if config == self.config:
            return
        self.config = config
        self.async_stop_source()
        await self.async_start_source()
        self.async_update_listeners()
        for preset in self.presets:
            preset.async_update_state()

    async def async_set_automatic(self, value: bool) -> None:
        """Switch between following the source and setting the mode by hand."""
        if not self.store.set_automatic(self.config.subentry_id, value):
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
        self.store.set_active_mode(self.config.subentry_id, mode_key)
        self.async_set_updated_data(mode_key)
        for preset in self.presets:
            preset.async_update_state()


class PresetCoordinator(DataUpdateCoordinator[PresetState]):
    """Resolves the currently valid values of a single preset.

    Which mode those values come from is normally the preset mode's business,
    but not necessarily: every preset carries an automatic of its own, and
    switching it off pins the preset to a mode while the dimension carries on
    without it.
    """

    def __init__(
        self,
        runtime: PresetManagerRuntime,
        config: PresetConfig,
        entry: PresetManagerConfigEntry,
    ) -> None:
        """Initialise the preset coordinator."""
        super().__init__(
            runtime.hass,
            _LOGGER,
            name=f"{DOMAIN}.{config.subentry_id}",
            config_entry=entry,
            update_interval=None,
            always_update=False,
        )
        self.runtime = runtime
        self.config = config
        #: The preset mode this preset follows, once it is loaded. ``None``
        #: while its hub is not set up, and for good after that preset mode
        #: was deleted - the preset then keeps everything but its active mode.
        self.preset_mode: PresetModeCoordinator | None = None
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
        """Return the modes this preset has a value for."""
        return list(self.config.modes)

    @property
    def attached(self) -> bool:
        """Return whether the preset mode driving this preset is loaded."""
        return self.preset_mode is not None

    def resolve_mode(self, value: str) -> ModeDef | None:
        """Resolve a mode from a key, a display name or a slug."""
        return resolve_mode(self.config.modes, value)

    # Automatic ---------------------------------------------------------------

    @property
    def automatic(self) -> bool:
        """Return whether the preset takes the mode of its preset mode.

        Unlike the automatic of a preset mode, this one exists for every
        preset: there is always something to step out from under, even where
        the preset mode itself is set by hand or follows another entity.
        """
        return self.store.preset_automatic(self.config.subentry_id)

    @property
    def writable(self) -> bool:
        """Return whether the mode of this preset may be set by hand.

        Orphaned rather than merely unattached: a preset whose hub is not up
        yet is still going to follow a preset mode, and refusing writes for
        the length of a restart would be an error nobody can act on.
        """
        return not self.automatic and not self.config.is_orphaned

    async def async_set_automatic(self, value: bool) -> None:
        """Switch between following the preset mode and setting the mode here."""
        if self.config.is_orphaned:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="preset_orphaned",
                translation_placeholders={"preset": self.config.name},
            )
        if self.automatic == value:
            return
        if not value:
            # Switching off changes nothing that is on screen: the mode the
            # preset mode was handing over becomes the hand-set one. Without
            # this the preset would drop onto whatever was set by hand last -
            # possibly months ago - the moment the switch flips.
            self.store.set_manual_mode(self.config.subentry_id, self.data.mode_key)
        self.store.set_preset_automatic(self.config.subentry_id, value)
        self._async_push_mode_change()

    @callback
    def async_set_active_mode(self, value: str) -> None:
        """Set the mode of this preset by hand, from a key or display name."""
        if self.config.is_orphaned:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="preset_orphaned",
                translation_placeholders={"preset": self.config.name},
            )
        if self.automatic:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="preset_automatic_active",
                translation_placeholders={"preset": self.config.name},
            )
        mode = self.resolve_mode(value)
        if mode is None:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="unsupported_mode",
                translation_placeholders={
                    "mode": value,
                    "preset": self.config.name,
                    "modes": ", ".join(item.name for item in self.modes),
                },
            )
        if not self.store.set_manual_mode(self.config.subentry_id, mode.key):
            return
        self._async_push_mode_change()

    @callback
    def _async_push_mode_change(self) -> None:
        """Write the state again, even where the resolved values did not move.

        Switching the automatic normally resolves to the very same mode - that
        is the point of it - so the ordinary "only push what changed" would
        push nothing, while the switch, the selector and the sensor all have to
        show the new arrangement.
        """
        new_state = self._compute_state()
        if new_state == self.data:
            self.async_update_listeners()
        else:
            self.async_set_updated_data(new_state)

    @callback
    def async_apply_config(self, config: PresetConfig) -> None:
        """Follow a changed configuration without being rebuilt."""
        if config == self.config:
            return
        self.config = config
        self.async_update_state()
        self.async_update_listeners()

    @callback
    def async_attach(self, preset_mode: PresetModeCoordinator | None) -> None:
        """Follow ``preset_mode`` from now on, or nothing at all."""
        if preset_mode is self.preset_mode:
            return
        self.preset_mode = preset_mode
        if self.data is not None:
            # Not during setup: the initial state is computed once, attached.
            self.async_update_state()

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
        always usable. It stays undefined while no preset mode is attached -
        the hub is not up yet, or the preset is waiting to be assigned one.
        A preset without a preset mode resolves nothing even when it was set
        to a mode by hand: it is broken configuration, and a preset that
        quietly kept working would hide that.
        """
        if self.preset_mode is None:
            return None
        if not self.automatic:
            manual = self.store.manual_mode(self.config.subentry_id)
            # A mode that was deleted under the preset falls back to the one
            # of the preset mode rather than leaving it without any.
            if manual is not None and self.config.mode(manual) is not None:
                return manual
        active = self.preset_mode.active_mode_key
        if active is not None and self.config.mode(active) is not None:
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
        mode = self.config.mode(mode_key)
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
