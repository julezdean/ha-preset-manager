"""The structure of the integration, for its own dashboard card.

Four things about this integration never reach a frontend, and none of them can
be guessed from the states:

1. **which entity edits which mode of which parameter** - that lives in the
   unique id (``<subentry>_cfg_<mode>-<parameter>``) and nowhere else,
2. **which preset follows which preset mode** - a subentry id, deliberately not
   a ``via_device`` and deliberately not a state attribute,
3. **the mode keys** other than the active one,
4. **the mode icons**, which are configured, stored and until now unused.

A card that reconstructed any of it from display names would break on the first
rename - which is the one thing this integration promises never to do. So the
card asks for the structure instead, and reads the *values* from the states,
where they already are: a renamed preset, a switched mode and a moved slider
arrive without a round trip.

**This command is not public surface.** Card and integration ship in one
version and a user cannot separate them, so it may change with any release -
unlike the entity ids, unique ids, services, attributes and storage formats.
It is documented in the README as what it is, not promised.

It needs no admin: a dashboard is rendered for every user, and there is nothing
here that a state does not already show. Values are not part of it at all,
which is also why the password mode of a text parameter needs no redaction
here the way it does in the diagnostics.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from . import hubs
from .const import (
    DOMAIN,
    HUB_BLUEPRINTS,
    UID_ACTIVE_MODE,
    UID_AUTOMATIC,
    UID_CONFIG,
    UID_PRESET_MODE_SENSOR,
    UID_SEPARATOR,
    UID_VALUE,
)
from .models import ModeDef, PresetConfig, PresetModeConfig
from .parameter_types import get_parameter_type

#: The command the card calls. Prefixed with the domain the way every
#: integration owned command is.
WS_TYPE_CONFIG = f"{DOMAIN}/config"


@callback
def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Register the websocket commands of the integration."""
    websocket_api.async_register_command(hass, ws_config)


def _mode(mode: ModeDef) -> dict[str, Any]:
    """Return one mode, without its conditions.

    The conditions decide the active mode and are answered by the state of the
    mode sensor; spelling them out here would hand a dashboard a copy of the
    automation logic it has no use for.
    """
    return {"key": mode.key, "name": mode.name, "icon": mode.icon}


class _EntityLookup:
    """Resolves the entity id behind a unique id.

    Built from the same ``UID_*`` constants the entities are built from, so the
    card is wired to the registry rather than to a naming convention. An entity
    the user disabled resolves all the same - the card then finds no state for
    it and says so, which is more useful than a row that silently disappears.
    """

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialise the lookup."""
        self._registry = er.async_get(hass)

    def __call__(self, platform: str, unique_id: str) -> str | None:
        """Return the entity id of one entity of this integration."""
        return self._registry.async_get_entity_id(platform, DOMAIN, unique_id)


@callback
def _async_device_id(hass: HomeAssistant, subentry_id: str) -> str | None:
    """Return the device of one object, for a card that links to it."""
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, subentry_id)})
    return None if device is None else device.id


@callback
def _async_preset_modes(hass: HomeAssistant, lookup: _EntityLookup) -> list[dict]:
    """Return every configured preset mode."""
    result: list[dict[str, Any]] = []
    for subentry_id, subentry in hubs.async_preset_modes(hass).items():
        config = PresetModeConfig.from_subentry(
            subentry_id, subentry.title, subentry.data
        )
        entities: dict[str, str] = {}
        if entity_id := lookup("sensor", f"{subentry_id}_{UID_PRESET_MODE_SENSOR}"):
            entities["mode"] = entity_id
        # Both of these exist only for some preset modes - an external one has
        # no selector, and one without conditions has nothing to automate.
        if not config.is_external and (
            entity_id := lookup("select", f"{subentry_id}_{UID_ACTIVE_MODE}")
        ):
            entities["active_mode"] = entity_id
        if config.has_conditions and (
            entity_id := lookup("switch", f"{subentry_id}_{UID_AUTOMATIC}")
        ):
            entities["automatic"] = entity_id

        result.append(
            {
                "id": subentry_id,
                "name": config.name,
                "device_id": _async_device_id(hass, subentry_id),
                "modes": [_mode(mode) for mode in config.modes],
                "source_entity": config.source_entity,
                "has_conditions": config.has_conditions,
                "entities": entities,
            }
        )
    return result


@callback
def _async_presets(hass: HomeAssistant, lookup: _EntityLookup) -> list[dict]:
    """Return every configured preset, with its parameters wired up."""
    result: list[dict[str, Any]] = []
    for subentry_id, subentry in hubs.async_presets(hass).items():
        # The same resolution the coordinator does: parameters come from the
        # blueprint it follows, modes from its preset mode, and both work
        # whether or not the other hub happens to be loaded.
        config = PresetConfig.from_subentry(
            subentry_id,
            subentry.title,
            hubs.async_resolve_preset_data(hass, subentry.data),
        )

        parameters: list[dict[str, Any]] = []
        for parameter in config.parameters:
            parameter_type = get_parameter_type(parameter.type)
            editors: dict[str, str] = {}
            if (platform := parameter_type.editor_platform) is not None:
                for mode in config.modes:
                    unique_id = (
                        f"{subentry_id}_{UID_CONFIG}_{mode.key}"
                        f"{UID_SEPARATOR}{parameter.key}"
                    )
                    if entity_id := lookup(platform, unique_id):
                        editors[mode.key] = entity_id
            parameters.append(
                {
                    "key": parameter.key,
                    "name": parameter.name,
                    "type": parameter.type,
                    # Everything a control needs beyond this - range, step,
                    # options, pattern, unit, precision - is on the state of
                    # the entity itself, where Home Assistant's own controls
                    # read it from.
                    "entity": lookup(
                        parameter_type.value_platform,
                        f"{subentry_id}_{UID_VALUE}_{parameter.key}",
                    ),
                    "editors": editors,
                }
            )

        entities = {}
        if entity_id := lookup("sensor", f"{subentry_id}_{UID_ACTIVE_MODE}"):
            entities["active_mode"] = entity_id

        result.append(
            {
                "id": subentry_id,
                "name": config.name,
                "device_id": _async_device_id(hass, subentry_id),
                "preset_mode": config.preset_mode,
                "blueprint": config.blueprint,
                "modes": [_mode(mode) for mode in config.modes],
                "parameters": parameters,
                "entities": entities,
            }
        )
    return result


@websocket_api.websocket_command({vol.Required("type"): WS_TYPE_CONFIG})
@callback
def ws_config(
    hass: HomeAssistant,
    connection: websocket_api.ActiveConnection,
    msg: dict[str, Any],
) -> None:
    """Return the structure of every object of the integration."""
    lookup = _EntityLookup(hass)
    connection.send_result(
        msg["id"],
        {
            "preset_modes": _async_preset_modes(hass, lookup),
            "presets": _async_presets(hass, lookup),
            # Only what a card can say about one: the name a preset shows to
            # explain where its parameters come from.
            "blueprints": [
                {"id": subentry_id, "name": subentry.title}
                for subentry_id, subentry in hubs.async_objects(
                    hass, HUB_BLUEPRINTS
                ).items()
            ],
        },
    )
