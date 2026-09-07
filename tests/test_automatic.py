"""Tests for switching a preset mode between automatic and manual."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from .conftest import (
    BRIGHTNESS,
    Hubs,
    async_set_active_mode,
    async_setup_hubs,
    make_preset,
    make_preset_mode,
)

SELECT = "select.house_mode_active_mode"
SWITCH = "switch.house_mode_automatic"
SENSOR = "sensor.house_mode_mode"


async def _entity_driven(hass: HomeAssistant) -> Hubs:
    """A preset mode whose modes follow sensor.mode_source."""
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


async def test_switch_exists_only_with_conditions(hass: HomeAssistant) -> None:
    """A preset mode without any conditions has nothing to switch."""
    await async_setup_hubs(hass, preset_modes=[make_preset_mode()])

    assert hass.states.get(SELECT) is not None
    assert hass.states.get(SWITCH) is None


async def test_automatic_is_on_by_default(hass: HomeAssistant) -> None:
    """Conditions run on their own until switched off."""
    await _entity_driven(hass)
    assert hass.states.get(SWITCH).state == "on"
    assert hass.states.get(SENSOR).state == "Night"


async def test_manual_ignores_the_source(hass: HomeAssistant) -> None:
    """While automatic is off the conditions no longer change the mode."""
    await _entity_driven(hass)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH}, blocking=True
    )
    assert hass.states.get(SWITCH).state == "off"

    hass.states.async_set("sensor.mode_source", "Away")
    await hass.async_block_till_done()
    # The source moved on, the preset mode did not.
    assert hass.states.get(SENSOR).state == "Night"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Home"},
        blocking=True,
    )
    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"


async def test_turning_automatic_back_on_catches_up(hass: HomeAssistant) -> None:
    """Switching back on evaluates the conditions immediately."""
    await _entity_driven(hass)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH}, blocking=True
    )
    hass.states.async_set("sensor.mode_source", "Away")
    await hass.async_block_till_done()
    assert hass.states.get(SENSOR).state == "Night"

    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": SWITCH}, blocking=True
    )
    await hass.async_block_till_done()
    # No waiting for the next state change of the source.
    assert hass.states.get(SENSOR).state == "Away"


async def test_select_is_refused_while_automatic(hass: HomeAssistant) -> None:
    """Picking a mode by hand requires switching automatic off first."""
    await _entity_driven(hass)

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": SELECT, "option": "Home"},
            blocking=True,
        )
    assert hass.states.get(SENSOR).state == "Night"

    with pytest.raises(ServiceValidationError):
        await async_set_active_mode(hass, "home")


async def test_automatic_survives_a_restart(hass: HomeAssistant) -> None:
    """The switch position is persisted."""
    hubs = await _entity_driven(hass)

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH}, blocking=True
    )
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Home"},
        blocking=True,
    )

    await hass.config_entries.async_reload(hubs.entry("preset_modes").entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SWITCH).state == "off"
    assert hass.states.get(SENSOR).state == "Home"


async def test_sensor_reports_the_automatic_state(hass: HomeAssistant) -> None:
    """The attributes make the current state of the preset mode visible."""
    await _entity_driven(hass)
    assert hass.states.get(SENSOR).attributes["automatic"] is True

    await hass.services.async_call(
        "switch", "turn_off", {"entity_id": SWITCH}, blocking=True
    )
    assert hass.states.get(SENSOR).attributes["automatic"] is False
