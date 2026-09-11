"""Tests for what decides the mode of a preset mode.

Exactly two things do: its conditions, or the entity it follows. There is no
third, and no way in from outside - a preset mode is a list of modes plus,
optionally, the logic that picks one. Taking a single device out of that is
what the automatic of a *preset* is for, and lives in ``test_preset_automatic``.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import (
    BRIGHTNESS,
    Hubs,
    async_setup_hubs,
    async_setup_one,
    make_preset,
    make_preset_mode,
)

SENSOR = "sensor.house_mode_mode"
PRESET_SENSOR = "sensor.heating_active_mode"


async def _condition_driven(hass: HomeAssistant) -> Hubs:
    """A preset mode whose modes are chosen by conditions on one sensor."""
    hass.states.async_set("sensor.mode_source", "Night")
    return await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(
                conditions={
                    key: [
                        {
                            "condition": "state",
                            "entity_id": "sensor.mode_source",
                            "state": name,
                        }
                    ]
                    for key, name in (
                        ("home", "Home"),
                        ("away", "Away"),
                        ("night", "Night"),
                        ("window_open", "Window open"),
                    )
                }
            )
        ],
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )


async def test_a_preset_mode_has_one_entity(hass: HomeAssistant) -> None:
    """It reports its mode and is not operated."""
    await _condition_driven(hass)

    assert hass.states.get(SENSOR) is not None
    assert hass.states.get("select.house_mode_active_mode") is None
    assert hass.states.get("switch.house_mode_automatic") is None
    assert hass.states.get("switch.house_mode_follows_preset_mode") is None


async def test_the_conditions_decide_and_keep_deciding(hass: HomeAssistant) -> None:
    """Nothing holds them back, so every change of the source arrives."""
    await _condition_driven(hass)
    assert hass.states.get(SENSOR).state == "Night"
    assert hass.states.get(PRESET_SENSOR).state == "Night"

    hass.states.async_set("sensor.mode_source", "Away")
    await hass.async_block_till_done()

    assert hass.states.get(SENSOR).state == "Away"
    assert hass.states.get(PRESET_SENSOR).state == "Away"


async def test_an_entity_decides_where_one_is_configured(hass: HomeAssistant) -> None:
    """The other driver, and the one that replaces setting a mode by hand."""
    hass.states.async_set("input_select.house", "Night")
    await async_setup_one(
        hass,
        source_entity="input_select.house",
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    assert hass.states.get(SENSOR).state == "Night"

    hass.states.async_set("input_select.house", "Home")
    await hass.async_block_till_done()

    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(PRESET_SENSOR).state == "Home"


async def test_without_a_driver_it_stays_on_its_first_mode(hass: HomeAssistant) -> None:
    """A preset mode can be nothing but a list of modes.

    That is a configuration, not a defect: the presets following it are the
    ones taken out by hand, one at a time. A fresh one starting on "no mode
    active" would only look broken.
    """
    await async_setup_one(hass, presets=[make_preset("Heating", [BRIGHTNESS])])

    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(PRESET_SENSOR).state == "Home"


async def test_the_computed_mode_survives_a_restart(hass: HomeAssistant) -> None:
    """It is persisted, so a restart does not blank every preset until the
    source next changes."""
    hubs = await _condition_driven(hass)
    hass.states.async_set("sensor.mode_source", "Window open")
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "Window open"

    await hass.config_entries.async_reload(hubs.entry("preset_modes").entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SENSOR).state == "Window open"
