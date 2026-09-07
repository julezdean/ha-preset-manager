"""Tests for entity naming.

Entity ids have to stay English and stable regardless of the UI language,
while the displayed names follow the language of the Home Assistant instance.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from .conftest import BRIGHTNESS, OFF_DELAY, make_entry, make_preset


async def _setup(hass: HomeAssistant, language: str) -> None:
    """Set up an instance with the given UI language."""
    await hass.config.async_update(language=language)
    entry = make_entry(
        presets=[make_preset("Heating Living Room", [BRIGHTNESS, OFF_DELAY])]
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("language", ["en", "de", "nl"])
async def test_entity_ids_are_language_independent(
    hass: HomeAssistant, language: str
) -> None:
    """The entity ids of translated entities are always English."""
    await _setup(hass, language)

    assert hass.states.get("select.house_mode_active_mode") is not None
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
        hass.states.get("select.house_mode_active_mode").attributes["friendly_name"]
        == "House Mode Aktiver Mode"
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
        hass.states.get("select.house_mode_active_mode").attributes["friendly_name"]
        == "House Mode Active mode"
    )


async def test_editor_unique_ids_survive_underscores_in_both_keys(
    hass: HomeAssistant,
) -> None:
    """Mode key and parameter key are both slugs and may contain underscores.

    Joined by an underscore, mode "night_mode" with parameter "brightness" and
    mode "night" with parameter "mode_brightness" build the same unique id, and
    Home Assistant drops one of the two editors instead of creating it.
    """
    entry = make_entry(
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
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # Two modes x two parameters, none of them swallowed by a clashing id.
    assert len(hass.states.async_all("number")) == 4
