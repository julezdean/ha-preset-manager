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
from homeassistant.helpers import issue_registry as ir

from custom_components.preset_manager.const import DOMAIN, SERVICE_SET_ACTIVE_MODE

from .conftest import (
    BRIGHTNESS,
    COLOR_TEMPERATURE,
    OFF_DELAY,
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_set_active_mode,
    async_setup_hubs,
    make_preset,
    make_preset_mode,
)

PRESET_MODE_SELECT = "select.house_mode_active_mode"
PRESET_MODE_SENSOR = "sensor.house_mode_mode"

SWITCH = "switch.motion_sensor_living_room_follows_preset_mode"
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


async def test_a_deleted_mode_hands_the_preset_back_to_its_dimension(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The mode a preset holds can be taken away under it.

    Holding nothing is not the same as being held, so the preset really does
    follow again rather than behaving like it with a switch that says
    otherwise - and a repair says so, because nothing else would.
    """
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

    # Back on the mode of the preset mode - and following it again for real.
    assert hass.states.get(SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"
    assert hass.states.get(SWITCH).state == "on"

    issues = ir.async_get(hass)
    issue = issues.async_get_issue(DOMAIN, f"manual_mode_deleted_{PRESET_ID}")
    assert issue is not None
    # The name of the deleted mode, which only the old configuration still had.
    assert issue.translation_placeholders == {
        "preset": "Motion Sensor Living Room",
        "mode": "Night",
    }


async def test_it_keeps_following_after_a_deleted_mode(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The state it is left in has to survive the next switch of the dimension.

    This is what the old fall-back got wrong: the preset followed every switch
    from here on with a switch that read "off".
    """
    await _set_values(hass, motion)
    await _turn(hass, "turn_off")
    await _select(hass, "Night")

    hub = motion.entry("preset_modes")
    subentry = hub.subentries[PRESET_MODE_ID]
    modes = [item for item in subentry.data["modes"] if item["key"] != "night"]
    hass.config_entries.async_update_subentry(
        hub, subentry, data={**subentry.data, "modes": modes}
    )
    await hass.async_block_till_done()

    await async_set_active_mode(hass, "away")
    assert hass.states.get(SENSOR).state == "Away"
    assert hass.states.get(SWITCH).state == "on"


async def test_the_repair_goes_when_the_preset_is_taken_out_again(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """It asks for a decision, and making it is what withdraws the question."""
    await _set_values(hass, motion)
    await _turn(hass, "turn_off")
    await _select(hass, "Night")

    hub = motion.entry("preset_modes")
    subentry = hub.subentries[PRESET_MODE_ID]
    modes = [item for item in subentry.data["modes"] if item["key"] != "night"]
    hass.config_entries.async_update_subentry(
        hub, subentry, data={**subentry.data, "modes": modes}
    )
    await hass.async_block_till_done()
    issues = ir.async_get(hass)
    issue_id = f"manual_mode_deleted_{PRESET_ID}"
    assert issues.async_get_issue(DOMAIN, issue_id) is not None

    await _turn(hass, "turn_off")

    assert issues.async_get_issue(DOMAIN, issue_id) is None
    assert hass.states.get(SENSOR).state == "Home"


async def test_a_deleted_preset_mode_does_not_raise_it(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Losing the whole dimension is the other repair, not this one.

    A deleted preset mode hands its modes to the presets that followed it, so
    the one they are held on is still there - nothing was lost that this issue
    is about, and two repairs for one event would only compete.
    """
    await _set_values(hass, motion)
    await _turn(hass, "turn_off")
    await _select(hass, "Night")

    hub = motion.entry("preset_modes")
    hass.config_entries.async_remove_subentry(hub, PRESET_MODE_ID)
    await hass.async_block_till_done()

    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, f"manual_mode_deleted_{PRESET_ID}") is None
    assert issues.async_get_issue(DOMAIN, f"orphaned_preset_{PRESET_ID}") is not None
    # Still taken out by hand; it just has nothing to be taken out of.
    assert hass.states.get(SWITCH).state == "off"
