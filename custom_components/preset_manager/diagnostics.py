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

from . import following, hubs
from .const import (
    CONF_BLUEPRINT,
    CONF_DEFAULT,
    CONF_PARAMETERS,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
)
from .coordinator import (
    PresetCoordinator,
    PresetManagerConfigEntry,
    PresetModeCoordinator,
)
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


def _preset_mode(
    hass: HomeAssistant, preset_mode: PresetModeCoordinator
) -> dict[str, Any]:
    """Return the state of one preset mode."""
    config = preset_mode.config
    report: dict[str, Any] = {
        "name": config.name,
        # Conditions included: a mode that can never match is only visible here.
        "modes": [mode.to_dict() for mode in config.modes],
        "source_kind": preset_mode.source_kind,
        "has_conditions": config.has_conditions,
        "automatic": preset_mode.automatic,
        "writable": preset_mode.writable,
        "active_mode": preset_mode.active_mode_key,
        "stored_active_mode": preset_mode.store.active_mode(config.subentry_id),
        "presets": [item.config.name for item in preset_mode.presets],
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
        "modes": [mode.to_dict() for mode in config.modes],
        # The two references a preset resolves on every setup, and whether
        # they are currently attached: "unknown everywhere" is either.
        "preset_mode": config.preset_mode,
        "attached": coordinator.attached,
        # Whether it is taking the mode of that preset mode at all, and which
        # mode it holds if not: a preset "showing the wrong values" is this
        # one line more often than it is anything else.
        "automatic": coordinator.automatic,
        "manual_mode": coordinator.store.manual_mode(config.subentry_id),
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
        blueprint = hubs.async_object(hass, HUB_BLUEPRINTS, config.blueprint)
        report["blueprint"] = {
            "subentry_id": config.blueprint,
            # A blueprint missing from the storage - a backup restored without
            # it - leaves the preset with no parameters at all.
            "exists": blueprint is not None,
            "title": None if blueprint is None else blueprint.title,
        }
    return report


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: PresetManagerConfigEntry
) -> dict[str, Any]:
    """Return the diagnostics of one hub."""
    kind = hubs.hub_kind(entry)
    report: dict[str, Any] = {
        "entry": {
            "hub": kind,
            "title": entry.title,
            "version": entry.version,
            "minor_version": entry.minor_version,
            "state": entry.state.value,
        }
    }

    if kind == HUB_BLUEPRINTS:
        # A blueprint sets nothing up, so there is no state beyond the list it
        # holds and who follows it.
        report["blueprints"] = [
            {
                "subentry_id": subentry_id,
                "title": subentry.title,
                "parameters": list(subentry.data.get(CONF_PARAMETERS, [])),
                "followed_by": [
                    preset.title
                    for preset in following.async_presets_following(
                        hass, CONF_BLUEPRINT, subentry_id
                    ).values()
                ],
            }
            for subentry_id, subentry in hubs.async_blueprints(hass).items()
        ]
        return report

    if entry.state is not ConfigEntryState.LOADED:
        # No runtime to read. The stored data is what a failed setup left, and
        # it is what a migration problem would show.
        report["stored_objects"] = [
            {
                "subentry_id": subentry_id,
                "title": subentry.title,
                "data": dict(subentry.data),
            }
            for subentry_id, subentry in entry.subentries.items()
        ]
        return report

    runtime = entry.runtime_data
    if kind == HUB_PRESET_MODES:
        report["preset_modes"] = {
            subentry_id: _preset_mode(hass, coordinator)
            for subentry_id, coordinator in runtime.preset_modes.items()
        }
        return report

    report["presets"] = {
        subentry_id: _preset(hass, coordinator)
        for subentry_id, coordinator in runtime.presets.items()
    }
    return report
