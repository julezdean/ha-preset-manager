"""Tests for the ``preset_manager/config`` websocket command.

The command exists because four things never reach a frontend: which entity
edits which mode of which parameter, what a preset follows, the mode keys, and
the mode icons. Every test here is about one of those four, plus the promise
that it hands out structure and never a value.
"""

from __future__ import annotations

from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.typing import WebSocketGenerator

from custom_components.preset_manager.const import (
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
)
from custom_components.preset_manager.websocket_api import WS_TYPE_CONFIG

from .conftest import (
    BLUEPRINT_ID,
    BRIGHTNESS,
    COLOR_TEMPERATURE,
    OFF_DELAY,
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_setup_hubs,
    async_setup_one,
    make_blueprint,
    make_preset,
    make_preset_mode,
)

TOGGLE = {"key": "boost", "name": "Boost", "type": "boolean"}
SECRET = {
    "key": "token",
    "name": "Token",
    "type": "text",
    "display_mode": "password",
    "default": "hunter2",
}


async def async_config(hass_ws_client: WebSocketGenerator, hass: HomeAssistant) -> Any:
    """Call the command and return its result."""
    client = await hass_ws_client(hass)
    await client.send_json_auto_id({"type": WS_TYPE_CONFIG})
    response = await client.receive_json()
    assert response["success"], response
    return response["result"]


def one(items: list[dict[str, Any]], key: str, value: Any) -> dict[str, Any]:
    """Return the single item whose ``key`` is ``value``."""
    found = [item for item in items if item[key] == value]
    assert len(found) == 1, found
    return found[0]


async def test_reports_the_modes_with_their_keys_and_icons(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """The keys and the icons of every mode, not only of the active one."""
    await async_setup_one(
        hass,
        modes=[
            {"key": "home", "name": "Home", "icon": "mdi:home"},
            {"key": "night", "name": "Night"},
        ],
    )

    result = await async_config(hass_ws_client, hass)
    preset_mode = one(result["preset_modes"], "id", PRESET_MODE_ID)
    assert preset_mode["name"] == "House Mode"
    assert preset_mode["modes"] == [
        {"key": "home", "name": "Home", "icon": "mdi:home"},
        {"key": "night", "name": "Night", "icon": None},
    ]


async def test_wires_every_entity_of_a_preset_mode(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """The three entities of a preset mode, by their real entity ids."""
    await async_setup_one(
        hass,
        conditions={"night": [{"condition": "template", "value_template": "{{ 1 }}"}]},
    )

    preset_mode = one(
        (await async_config(hass_ws_client, hass))["preset_modes"], "id", PRESET_MODE_ID
    )
    assert preset_mode["entities"] == {
        "mode": "sensor.house_mode_mode",
        "active_mode": "select.house_mode_active_mode",
        "automatic": "switch.house_mode_automatic",
    }
    assert preset_mode["has_conditions"] is True
    for entity_id in preset_mode["entities"].values():
        assert hass.states.get(entity_id) is not None


async def test_omits_the_automatic_of_a_preset_mode_without_conditions(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A manual preset mode has nothing to switch between, and says so."""
    await async_setup_one(hass)

    preset_mode = one(
        (await async_config(hass_ws_client, hass))["preset_modes"], "id", PRESET_MODE_ID
    )
    assert "automatic" not in preset_mode["entities"]
    assert preset_mode["has_conditions"] is False
    assert preset_mode["source_entity"] is None


async def test_reports_an_external_preset_mode_without_a_selector(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Handed to an entity: no selector, no automatic, and the entity named."""
    hass.states.async_set("input_select.house_mode", "Night")
    await async_setup_one(hass, source_entity="input_select.house_mode")

    preset_mode = one(
        (await async_config(hass_ws_client, hass))["preset_modes"], "id", PRESET_MODE_ID
    )
    assert preset_mode["source_entity"] == "input_select.house_mode"
    assert preset_mode["entities"] == {"mode": "sensor.house_mode_mode"}


async def test_wires_one_editor_per_mode_and_parameter(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, motion: Hubs
) -> None:
    """The whole reason for the command: which entity edits which cell."""
    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    brightness = one(preset["parameters"], "key", "brightness")

    assert brightness["entity"] == "sensor.motion_sensor_living_room_brightness"
    assert brightness["editors"] == {
        "home": "number.motion_sensor_living_room_home_brightness",
        "away": "number.motion_sensor_living_room_away_brightness",
        "night": "number.motion_sensor_living_room_night_brightness",
        "window_open": "number.motion_sensor_living_room_window_open_brightness",
    }
    for entity_id in brightness["editors"].values():
        assert hass.states.get(entity_id) is not None


async def test_keeps_the_parameters_in_their_configured_order(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, motion: Hubs
) -> None:
    """The card draws them top to bottom in this order."""
    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    assert [item["key"] for item in preset["parameters"]] == [
        BRIGHTNESS["key"],
        COLOR_TEMPERATURE["key"],
        OFF_DELAY["key"],
    ]


async def test_uses_the_platform_of_the_parameter_type(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A toggle publishes a binary sensor and is edited by a switch."""
    await async_setup_one(hass, presets=[make_preset("Heating Bath", [TOGGLE])])

    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    boost = one(preset["parameters"], "key", "boost")
    assert boost["type"] == "boolean"
    assert boost["entity"] == "binary_sensor.heating_bath_boost"
    assert boost["editors"]["night"] == "switch.heating_bath_night_boost"


async def test_says_which_preset_mode_a_preset_follows(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, motion: Hubs
) -> None:
    """The subentry id, which is the only place this relation exists."""
    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    assert preset["preset_mode"] == PRESET_MODE_ID
    assert preset["entities"] == {
        "active_mode": "sensor.motion_sensor_living_room_active_mode",
        "mode_selection": "select.motion_sensor_living_room_mode_selection",
        "automatic": "switch.motion_sensor_living_room_follows_preset_mode",
    }


async def test_keeps_a_preset_that_lost_its_preset_mode(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """It follows nothing and keeps the modes it had; the card must show it."""
    await async_setup_hubs(
        hass,
        presets=[
            make_preset(
                "Shutter Living Room",
                [BRIGHTNESS],
                preset_mode=None,
                modes=[{"key": "night", "name": "Night"}],
            )
        ],
    )

    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    assert preset["preset_mode"] is None
    assert [item["key"] for item in preset["modes"]] == ["night"]


async def test_resolves_the_parameters_of_a_blueprint(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A preset following one reports the blueprint's parameters as its own."""
    await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        blueprints=[make_blueprint()],
        presets=[make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID)],
    )

    result = await async_config(hass_ws_client, hass)
    preset = one(result["presets"], "id", PRESET_ID)
    assert preset["blueprint"] == BLUEPRINT_ID
    assert [item["key"] for item in preset["parameters"]] == ["target_temperature"]
    assert result["blueprints"] == [{"id": BLUEPRINT_ID, "name": "Heating"}]


async def test_reports_the_device_of_every_object(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, motion: Hubs
) -> None:
    """So a card can link to the device page of what it shows."""
    result = await async_config(hass_ws_client, hass)
    assert one(result["preset_modes"], "id", PRESET_MODE_ID)["device_id"]
    assert one(result["presets"], "id", PRESET_ID)["device_id"]


async def test_carries_no_values_at_all(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """Structure only - which is also why nothing has to be redacted here."""
    await async_setup_one(hass, presets=[make_preset("Heating Bath", [SECRET])])

    result = await async_config(hass_ws_client, hass)
    assert "hunter2" not in repr(result)
    parameter = one(
        one(result["presets"], "id", PRESET_ID)["parameters"], "key", "token"
    )
    assert set(parameter) == {"key", "name", "type", "entity", "editors"}


async def test_carries_no_conditions(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator
) -> None:
    """A dashboard has no use for the automation logic behind a mode."""
    await async_setup_one(
        hass,
        conditions={
            "night": [{"condition": "state", "entity_id": "sun.sun", "state": "x"}]
        },
    )

    preset_mode = one(
        (await async_config(hass_ws_client, hass))["preset_modes"], "id", PRESET_MODE_ID
    )
    assert all(set(mode) == {"key", "name", "icon"} for mode in preset_mode["modes"])


async def test_answers_a_non_admin(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_read_only_access_token: str,
    motion: Hubs,
) -> None:
    """Dashboards are rendered for everybody, so the card is too."""
    client = await hass_ws_client(hass, hass_read_only_access_token)
    await client.send_json_auto_id({"type": WS_TYPE_CONFIG})
    response = await client.receive_json()
    assert response["success"]
    assert response["result"]["presets"]


async def test_reports_a_disabled_entity_rather_than_dropping_the_row(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, motion: Hubs
) -> None:
    """The card can then say "unavailable" instead of silently omitting it."""
    registry = er.async_get(hass)
    registry.async_update_entity(
        "number.motion_sensor_living_room_night_brightness",
        disabled_by=er.RegistryEntryDisabler.USER,
    )

    preset = one((await async_config(hass_ws_client, hass))["presets"], "id", PRESET_ID)
    brightness = one(preset["parameters"], "key", "brightness")
    assert brightness["editors"]["night"] == (
        "number.motion_sensor_living_room_night_brightness"
    )


@pytest.mark.parametrize(
    "kind", [HUB_PRESET_MODES, HUB_PRESETS, HUB_BLUEPRINTS], ids=lambda kind: kind
)
async def test_answers_with_empty_lists_before_anything_exists(
    hass: HomeAssistant, hass_ws_client: WebSocketGenerator, kind: str
) -> None:
    """One hub set up on its own must not make the command fail."""
    await async_setup_hubs(hass, **{kind: []})

    result = await async_config(hass_ws_client, hass)
    assert result == {"preset_modes": [], "presets": [], "blueprints": []}
