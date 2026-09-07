"""Diagnostics for the Preset Manager integration.

The state of this integration is entirely local and entirely invisible from the
entity states: modes with their conditions, presets with their parameters, and
one value per mode and parameter. A preset reporting ``unknown`` has at least
five causes - no condition matched, the source entity names no mode, the
parameter has neither a value nor a default, the blueprint is gone, or the
stored mode no longer exists - and none of them can be told apart from the
outside. This download is what turns "it says unknown" into a diagnosis
without a round of questions.

Nothing here is a credential: the integration talks to no API, holds no token
and stores nothing it was not given by the user. The one thing that could be
private is a text parameter the user put in password mode, so its values and
its default are redacted - the definition itself stays, because a parameter
that vanished from the report would be the more confusing outcome.

Diagnostics are also offered for an entry that failed to set up, and there is
no runtime to read then. That case is the one where they are needed most, so it
reports the stored data instead of raising.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import blueprints
from .const import CONF_DEFAULT
from .coordinator import PresetCoordinator, PresetModeConfigEntry, PresetModeRuntime
from .models import ParameterDef, PresetConfig
from .parameter_types import MODE_PASSWORD, TYPE_TEXT

REDACTED = "**REDACTED**"


def _is_secret(parameter: ParameterDef) -> bool:
    """Return whether the values of a parameter must not be handed out."""
    return parameter.type == TYPE_TEXT and parameter.display_mode == MODE_PASSWORD


def _secret_keys(config: PresetConfig) -> set[str]:
    """Return the keys of every parameter whose values are redacted."""
    return {item.key for item in config.parameters if _is_secret(item)}


def _parameter(parameter: ParameterDef) -> dict[str, Any]:
    """Return the definition of a parameter, without a secret default."""
    data = parameter.to_dict()
    if _is_secret(parameter) and CONF_DEFAULT in data:
        data[CONF_DEFAULT] = REDACTED
    return data


def _values(secret_keys: set[str], values: Mapping[str, Any]) -> dict[str, Any]:
    """Return values with the ones belonging to a secret parameter redacted."""
    return {
        key: REDACTED if key in secret_keys else value for key, value in values.items()
    }


def _preset_mode(hass: HomeAssistant, runtime: PresetModeRuntime) -> dict[str, Any]:
    """Return the state of the preset mode itself."""
    preset_mode = runtime.preset_mode
    config = preset_mode.config
    report: dict[str, Any] = {
        # Conditions included: a mode that can never match is only visible here.
        "modes": [mode.to_dict() for mode in config.modes],
        "source_kind": preset_mode.source_kind,
        "has_conditions": config.has_conditions,
        "automatic": preset_mode.automatic,
        "writable": preset_mode.writable,
        "active_mode": preset_mode.active_mode_key,
        "stored_active_mode": runtime.store.active_mode(config.entry_id),
    }
    if config.source_entity is not None:
        state = hass.states.get(config.source_entity)
        report["source_entity"] = config.source_entity
        # The state of that entity against the mode names is the whole
        # question when an external preset mode reports nothing.
        report["source_entity_state"] = None if state is None else state.state
    return report


def _preset(hass: HomeAssistant, coordinator: PresetCoordinator) -> dict[str, Any]:
    """Return the configuration, the resolved state and the values of a preset."""
    config = coordinator.config
    secret_keys = _secret_keys(config)
    state = coordinator.data

    report: dict[str, Any] = {
        "name": config.name,
        "parameters": [_parameter(item) for item in config.parameters],
        "state": {
            "mode_key": state.mode_key,
            "mode_name": state.mode_name,
            "values": _values(secret_keys, state.values),
            "unset_parameters": list(state.unset_parameters),
        },
        "stored_values": {
            mode.key: _values(
                secret_keys,
                coordinator.store.get_mode_values(config.subentry_id, mode.key),
            )
            for mode in coordinator.modes
        },
    }

    if config.blueprint is not None:
        entry = hass.config_entries.async_get_entry(config.blueprint)
        report["blueprint"] = {
            "entry_id": config.blueprint,
            # A blueprint missing from the storage - a backup restored without
            # it - leaves the preset with no parameters at all.
            "exists": entry is not None and blueprints.is_blueprint(entry),
            "title": None if entry is None else entry.title,
        }
    return report


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PresetModeConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of one config entry."""
    report: dict[str, Any] = {
        "entry": {
            "entry_type": blueprints.entry_type(entry),
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "state": entry.state.value,
        }
    }

    if blueprints.is_blueprint(entry):
        # A blueprint sets nothing up, so there is no runtime and no state
        # beyond the list it holds and who follows it.
        report["parameters"] = blueprints.parameters_of(entry)
        report["bound_presets"] = [
            {"preset_mode": owner.title, "preset": subentry.title}
            for owner, subentry in blueprints.async_bound_presets(hass, entry.entry_id)
        ]
        return report

    if entry.state is not ConfigEntryState.LOADED:
        # No runtime to read. The stored data is what a failed setup left, and
        # it is what a migration problem would show.
        report["stored_data"] = dict(entry.data)
        report["stored_presets"] = [
            {"title": subentry.title, "data": dict(subentry.data)}
            for subentry in entry.subentries.values()
        ]
        return report

    runtime = entry.runtime_data
    report["preset_mode"] = _preset_mode(hass, runtime)
    report["presets"] = [
        _preset(hass, coordinator) for coordinator in runtime.presets.values()
    ]
    return report
