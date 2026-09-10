"""Tests for the automatic of a single preset.

The preset mode has an automatic of its own, tested in ``test_automatic``:
that one switches between the conditions and the hand. This one switches
between the *preset mode* and the hand, exists on every preset whatever its
preset mode can do, and leaves the dimension running while one preset steps
out from under it.
"""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

from custom_components.preset_manager.const import DOMAIN, SERVICE_SET_ACTIVE_MODE

from .conftest import (
    BRIGHTNESS,
    COLOR_TEMPERATURE,
    OFF_DELAY,
    PRESET_MODE_ID,
    Hubs,
    async_set_active_mode,
    async_setup_hubs,
    make_preset,
    make_preset_mode,
)

PRESET_MODE_SELECT = "select.house_mode_active_mode"
PRESET_MODE_SENSOR = "sensor.house_mode_mode"

SWITCH = "switch.motion_sensor_living_room_automatic"
SELECT = "select.motion_sensor_living_room_mode_selection"
SENSOR = "sensor.motion_sensor_living_room_active_mode"
BRIGHTNESS_SENSOR = "sensor.motion_sensor_living_room_brightness"


async def _set_values(hass: HomeAssistant, hubs: Hubs) -> None:
    """Give every mode a brightness to tell them apart by."""
    for mode_key, brightness in (
        ("home", 80),
        ("away", 0),
        ("night", 15),
        ("window_open", 5),
    ):
        hubs.preset.async_set_value(mode_key, "brightness", brightness)
    await hass.async_block_till_done()


async def _turn(hass: HomeAssistant, service: str) -> None:
    """Switch the automatic of the preset on or off."""
    await hass.services.async_call(
        "switch", service, {"entity_id": SWITCH}, blocking=True
    )


async def _select(hass: HomeAssistant, option: str) -> None:
    """Pick a mode on the preset itself."""
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": option},
        blocking=True,
    )


async def test_entities_exist_on_every_preset(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Even under a preset mode that has no automatic of its own.

    ``motion`` follows a preset mode without conditions, which therefore has
    no automatic switch - and the preset has one all the same.
    """
    assert hass.states.get("switch.house_mode_automatic") is None
    assert hass.states.get(SWITCH).state == "on"
    assert hass.states.get(SELECT) is not None


async def test_follows_the_preset_mode_by_default(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Nothing changes for a preset nobody switched."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "night")

    assert hass.states.get(SENSOR).state == "Night"
    assert hass.states.get(SELECT).state == "Night"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"


async def test_switching_off_keeps_the_mode_in_effect(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Nothing on screen moves the moment the switch flips."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "night")

    await _turn(hass, "turn_off")

    assert hass.states.get(SWITCH).state == "off"
    assert hass.states.get(SENSOR).state == "Night"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"


async def test_the_dimension_moves_on_without_the_preset(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The whole point: one preset stays behind, the rest do not."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "night")
    await _turn(hass, "turn_off")

    await async_set_active_mode(hass, "home")

    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"
    assert hass.states.get(SENSOR).state == "Night"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"


async def test_second_preset_keeps_following(hass: HomeAssistant) -> None:
    """Stepping out is per preset, not per dimension."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[
            make_preset(
                "Motion Sensor Living Room",
                [BRIGHTNESS, COLOR_TEMPERATURE, OFF_DELAY],
            ),
            make_preset("Heating", [BRIGHTNESS], subentry_id=None),
        ],
    )
    await async_set_active_mode(hass, "night")
    await _turn(hass, "turn_off")
    await async_set_active_mode(hass, "home")
    await hass.async_block_till_done()

    assert hass.states.get(SENSOR).state == "Night"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"
    assert hubs.preset_mode.active_mode_key == "home"


async def test_mode_can_be_set_on_the_preset(hass: HomeAssistant, motion: Hubs) -> None:
    """With the automatic off, the preset picks its own mode."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "night")
    await _turn(hass, "turn_off")

    await _select(hass, "Home")

    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"
    # The dimension was not touched by that.
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"


async def test_service_sets_the_mode_by_key(hass: HomeAssistant, motion: Hubs) -> None:
    """``set_active_mode`` works on a preset the way it does on a preset mode."""
    await _set_values(hass, motion)
    await _turn(hass, "turn_off")

    await async_set_active_mode(hass, "window_open", entity_id=SELECT)

    assert hass.states.get(SENSOR).state == "Window open"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "5.0"


async def test_switching_back_on_rejoins_the_dimension(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Whatever was set by hand is dropped, not remembered."""
    await _set_values(hass, motion)
    await _turn(hass, "turn_off")
    await _select(hass, "Window open")
    await async_set_active_mode(hass, "away")

    await _turn(hass, "turn_on")

    assert hass.states.get(SENSOR).state == "Away"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "0.0"


async def test_selecting_while_automatic_is_on_is_refused(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Setting the mode by hand has to be a deliberate act, as it is above."""
    await async_set_active_mode(hass, "night")

    with pytest.raises(ServiceValidationError):
        await _select(hass, "Home")

    assert hass.states.get(SENSOR).state == "Night"


async def test_unsupported_mode_is_refused(hass: HomeAssistant, motion: Hubs) -> None:
    """A mode the preset has no values for cannot be picked."""
    await _turn(hass, "turn_off")

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_ACTIVE_MODE,
            {"entity_id": SELECT, "mode": "vacation"},
            blocking=True,
        )


async def test_attribute_reports_the_automatic(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A template can tell a preset that follows from one that does not."""
    assert hass.states.get(SENSOR).attributes["automatic"] is True

    await _turn(hass, "turn_off")

    state = hass.states.get(SENSOR)
    assert state.attributes["automatic"] is False
    # Which preset mode it belongs to stays true while it holds its own mode.
    assert state.attributes["mode_source"] == "House Mode"


async def test_state_survives_a_reload(hass: HomeAssistant, motion: Hubs) -> None:
    """The stored mode and the switch come back after a restart."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "night")
    await _turn(hass, "turn_off")
    await _select(hass, "Home")

    await hass.config_entries.async_reload(motion.entry("presets").entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SWITCH).state == "off"
    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"


async def test_orphaned_preset_stays_orphaned(hass: HomeAssistant) -> None:
    """A preset without a preset mode has no mode to hold, and says so."""
    await async_setup_hubs(
        hass,
        presets=[
            make_preset(
                "Motion Sensor Living Room",
                [BRIGHTNESS],
                preset_mode=None,
                modes=[{"key": "night", "name": "Night"}],
            )
        ],
    )

    with pytest.raises(ServiceValidationError):
        await _turn(hass, "turn_off")
    with pytest.raises(ServiceValidationError):
        await _select(hass, "Night")

    assert hass.states.get(SWITCH).state == "on"
    assert hass.states.get(SENSOR).state == "unknown"


async def test_deleted_mode_falls_back_to_the_dimension(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The mode a preset holds can be taken away under it."""
    await _set_values(hass, motion)
    await async_set_active_mode(hass, "home")
    await _turn(hass, "turn_off")
    await _select(hass, "Night")
    assert hass.states.get(SENSOR).state == "Night"

    hub = motion.entry("preset_modes")
    subentry = hub.subentries[PRESET_MODE_ID]
    modes = [item for item in subentry.data["modes"] if item["key"] != "night"]
    hass.config_entries.async_update_subentry(
        hub, subentry, data={**subentry.data, "modes": modes}
    )
    await hass.async_block_till_done()

    # Back on the mode of the preset mode - not on no mode at all.
    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"
    # And still not following it: the switch was not touched.
    assert hass.states.get(SWITCH).state == "off"
