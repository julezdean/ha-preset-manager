"""Tests for entity naming.

Entity ids have to stay English and stable regardless of the UI language,
while the displayed names follow the language of the Home Assistant instance.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from .conftest import (
    BRIGHTNESS,
    OFF_DELAY,
    async_setup_hubs,
    async_setup_one,
    make_preset,
    make_preset_mode,
)


async def _setup(hass: HomeAssistant, language: str) -> None:
    """Set up an instance with the given UI language."""
    await hass.config.async_update(language=language)
    await async_setup_one(
        hass, presets=[make_preset("Heating Living Room", [BRIGHTNESS, OFF_DELAY])]
    )


@pytest.mark.parametrize("language", ["en", "de", "nl"])
async def test_entity_ids_are_language_independent(
    hass: HomeAssistant, language: str
) -> None:
    """The entity ids of translated entities are always English."""
    await _setup(hass, language)

    assert hass.states.get("sensor.house_mode_mode") is not None
    assert hass.states.get("sensor.heating_living_room_active_mode") is not None
    # Parameter entities are named after the user's own text in every language.
    assert hass.states.get("sensor.heating_living_room_brightness") is not None
    assert hass.states.get("number.heating_living_room_night_brightness") is not None


async def test_display_names_follow_the_language(hass: HomeAssistant) -> None:
    """The friendly names are translated even though the ids are English."""
    await _setup(hass, "de")

    assert (
        hass.states.get("sensor.heating_living_room_active_mode").attributes[
            "friendly_name"
        ]
        == "Heating Living Room Aktiver Mode"
    )
    assert (
        hass.states.get("switch.heating_living_room_follows_preset_mode").attributes[
            "friendly_name"
        ]
        == "Heating Living Room Mode-Automatik"
    )


async def test_display_names_in_english(hass: HomeAssistant) -> None:
    """The English names are used on an English instance."""
    await _setup(hass, "en")

    assert (
        hass.states.get("sensor.heating_living_room_active_mode").attributes[
            "friendly_name"
        ]
        == "Heating Living Room Active mode"
    )
    assert (
        hass.states.get("switch.heating_living_room_follows_preset_mode").attributes[
            "friendly_name"
        ]
        == "Heating Living Room Automatic mode selection"
    )


async def test_editor_unique_ids_survive_underscores_in_both_keys(
    hass: HomeAssistant,
) -> None:
    """Mode key and parameter key are both slugs and may contain underscores.

    Joined by an underscore, mode "night_mode" with parameter "brightness" and
    mode "night" with parameter "mode_brightness" build the same unique id, and
    Home Assistant drops one of the two editors instead of creating it.
    """
    await async_setup_one(
        hass,
        modes=[
            {"key": "night_mode", "name": "Night mode"},
            {"key": "night", "name": "Night"},
        ],
        presets=[
            make_preset(
                "Lamp",
                [
                    {"key": "brightness", "name": "Brightness", "type": "number"},
                    {
                        "key": "mode_brightness",
                        "name": "Mode brightness",
                        "type": "number",
                    },
                ],
            )
        ],
    )

    # Two modes x two parameters, none of them swallowed by a clashing id.
    assert len(hass.states.async_all("number")) == 4


async def test_a_preset_named_like_its_preset_mode_collides_with_nothing(
    hass: HomeAssistant,
) -> None:
    """The two objects share a name and still no entity is renamed.

    A preset mode has nothing but its mode sensor now, so the old collision
    between the two automatic switches cannot happen - but the preset's own
    entities still have to stay clear of it, and an "_2" suffix is the kind of
    breakage a user can neither see the cause of nor repair.
    """
    await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(
                title="House Mode",
                conditions={
                    "night": [
                        {
                            "condition": "state",
                            "entity_id": "sensor.anything",
                            "state": "Night",
                        }
                    ]
                },
            )
        ],
        presets=[make_preset("House Mode", [BRIGHTNESS])],
    )

    assert hass.states.get("sensor.house_mode_mode") is not None
    assert hass.states.get("switch.house_mode_follows_preset_mode") is not None
    assert hass.states.get("select.house_mode_mode_selection") is not None
    assert [
        state.entity_id
        for state in hass.states.async_all()
        if state.entity_id.endswith("_2")
    ] == []
