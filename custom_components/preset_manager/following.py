"""What a preset follows, and what happens when that disappears.

A preset follows two things by reference: a **preset mode** for its modes and a
**blueprint** for its parameters. Neither is copied into the preset while it
exists - one source of truth is what makes the promise hold, so a changed
blueprint reaches every preset without a write, and "is this preset free or
bound?" stays one key rather than a comparison of two lists.

The copy is made at exactly one moment: when the followed object is deleted.
Its last known definition is then written into every preset that followed it,
which is what lets a preset outlive its preset mode instead of disappearing
with it. Home Assistant offers no hook for the removal of a subentry, so the
definition comes from the runtime, which still holds it while the update
listener runs - see ``coordinator.PresetManagerRuntime.async_reconcile``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping
from typing import Any

from homeassistant.config_entries import ConfigSubentry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from . import hubs
from .const import (
    CONF_BLUEPRINT,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    DOMAIN,
    HUB_PRESETS,
    ISSUE_ORPHANED_PRESET,
)
from .store import async_get_store

_LOGGER = logging.getLogger(__name__)


@callback
def async_presets_following(
    hass: HomeAssistant, key: str, subentry_id: str
) -> dict[str, ConfigSubentry]:
    """Return every preset whose ``key`` points at ``subentry_id``."""
    return {
        preset_id: preset
        for preset_id, preset in hubs.async_presets(hass).items()
        if preset.data.get(key) == subentry_id
    }


@callback
def _async_update_preset(
    hass: HomeAssistant, preset: ConfigSubentry, data: Mapping[str, Any]
) -> None:
    """Write changed data back to one preset."""
    hub = hubs.async_hub(hass, HUB_PRESETS)
    if hub is None:
        return
    hass.config_entries.async_update_subentry(hub, preset, data=dict(data))


@callback
def async_follow(
    hass: HomeAssistant, preset: ConfigSubentry, key: str, subentry_id: str
) -> None:
    """Let one preset follow a preset mode or a blueprint.

    What it followed before is dropped, and so is what it carried for itself:
    the parameters of a preset are the blueprint's while it follows one, and
    its modes are the preset mode's. Both are read on every setup, so a copy
    left behind would only be a copy that could disagree.
    """
    dropped = CONF_PARAMETERS if key == CONF_BLUEPRINT else CONF_MODES
    data = {item: value for item, value in preset.data.items() if item != dropped}
    data[key] = subentry_id
    _async_update_preset(hass, preset, data)


@callback
def async_detach_from_blueprint(
    hass: HomeAssistant, blueprint_id: str, parameters: Iterable[Mapping[str, Any]]
) -> None:
    """Turn every preset of a deleted blueprint back into a free-standing one.

    The parameters of the blueprint are copied into the preset on the way out,
    so deleting a blueprint costs its presets their lock, not their
    configuration and not their values.
    """
    for preset in async_presets_following(hass, CONF_BLUEPRINT, blueprint_id).values():
        async_unfollow_blueprint(hass, preset, parameters)


@callback
def async_unfollow_blueprint(
    hass: HomeAssistant, preset: ConfigSubentry, parameters: Iterable[Mapping[str, Any]]
) -> None:
    """Turn one preset back into a free-standing one."""
    data = {key: value for key, value in preset.data.items() if key != CONF_BLUEPRINT}
    data[CONF_PARAMETERS] = [dict(item) for item in parameters]
    _async_update_preset(hass, preset, data)
    _LOGGER.debug("Preset '%s' kept the parameters of its blueprint", preset.title)


@callback
def async_detach_from_preset_mode(
    hass: HomeAssistant, preset_mode_id: str, modes: Iterable[Mapping[str, Any]]
) -> None:
    """Keep every preset of a deleted preset mode, without its dimension.

    The modes are copied into the preset so that its editors keep existing -
    they are one entity per mode and parameter, and an entity that stops being
    expected is removed from the registry with its name, its area and its
    icon. What the preset loses is the active mode, and therefore every
    resolved value; a repair issue asks for a new preset mode.
    """
    for preset in async_presets_following(
        hass, CONF_PRESET_MODE, preset_mode_id
    ).values():
        async_unfollow_preset_mode(hass, preset, modes)


@callback
def async_unfollow_preset_mode(
    hass: HomeAssistant, preset: ConfigSubentry, modes: Iterable[Mapping[str, Any]]
) -> None:
    """Keep one preset without its dimension."""
    data = {key: value for key, value in preset.data.items() if key != CONF_PRESET_MODE}
    data[CONF_MODES] = [dict(item) for item in modes]
    _async_update_preset(hass, preset, data)
    async_create_orphan_issue(hass, preset.subentry_id, preset.title)
    _LOGGER.debug(
        "Preset '%s' outlived its preset mode and waits for a new one", preset.title
    )


@callback
def async_create_orphan_issue(hass: HomeAssistant, preset_id: str, name: str) -> None:
    """Tell the user that a preset has no preset mode left."""
    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{ISSUE_ORPHANED_PRESET}_{preset_id}",
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_ORPHANED_PRESET,
        translation_placeholders={"preset": name},
    )


@callback
def async_clear_orphan_issue(hass: HomeAssistant, preset_id: str) -> None:
    """Withdraw the issue of a preset that has a preset mode again."""
    ir.async_delete_issue(hass, DOMAIN, f"{ISSUE_ORPHANED_PRESET}_{preset_id}")


@callback
def async_forget_parameters(
    hass: HomeAssistant, blueprint_id: str, parameter_keys: set[str]
) -> None:
    """Drop the stored values of parameters that changed their type.

    A retyped parameter keeps its key, so its values would survive a change
    they no longer fit - the same reason the parameter editor of a preset drops
    them, applied to every preset the blueprint reaches.
    """
    if not parameter_keys or (store := async_get_store(hass)) is None:
        return
    for preset_id in async_presets_following(hass, CONF_BLUEPRINT, blueprint_id):
        for key in parameter_keys:
            store.remove_parameter(preset_id, key)
