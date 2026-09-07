"""Tests for editing, validating and persisting mode values."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager.entity import ModeValueEditorEntity

from .conftest import (
    BRIGHTNESS,
    OFF_DELAY,
    async_set_active_mode,
    make_entry,
    make_preset,
)

SELECT = "select.house_mode_active_mode"
NIGHT_BRIGHTNESS = "number.motion_sensor_living_room_night_brightness"
BRIGHTNESS_SENSOR = "sensor.motion_sensor_living_room_brightness"

ACTIVE = {
    "key": "active",
    "name": "Active",
    "type": "boolean",
}
MODE = {
    "key": "mode",
    "name": "Operating mode",
    "type": "select",
    "options": ["auto", "manual"],
}
LABEL = {
    "key": "note",
    "name": "Note",
    "type": "text",
    "max_length": 10,
    "pattern": "[a-z]+",
    "display_mode": "password",
}
WAKE_UP = {
    "key": "wake_up",
    "name": "Wake up",
    "type": "time",
}
HOLIDAY = {
    "key": "holiday",
    "name": "Holiday",
    "type": "date",
}
NEXT_SERVICE = {
    "key": "next_service",
    "name": "Next service",
    "type": "datetime",
}


async def test_number_editor_updates_value_sensor(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Editing a value of the active mode updates the value sensor."""
    await async_set_active_mode(hass, "night")
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NIGHT_BRIGHTNESS, "value": 15},
        blocking=True,
    )

    assert hass.states.get(NIGHT_BRIGHTNESS).state == "15.0"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"


async def test_editing_inactive_mode_does_not_change_sensor(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Editing an inactive mode leaves the value sensor untouched."""
    await async_set_active_mode(hass, "home")
    await hass.services.async_call(
        "number",
        "set_value",
        {
            "entity_id": "number.motion_sensor_living_room_home_brightness",
            "value": 80,
        },
        blocking=True,
    )
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NIGHT_BRIGHTNESS, "value": 15},
        blocking=True,
    )

    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"
    assert hass.states.get(NIGHT_BRIGHTNESS).state == "15.0"


async def test_values_survive_a_restart(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Values and the active mode are restored after a reload."""
    await async_set_active_mode(hass, "night")
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NIGHT_BRIGHTNESS, "value": 15},
        blocking=True,
    )

    await hass.config_entries.async_reload(motion_entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SELECT).state == "Night"
    assert hass.states.get(NIGHT_BRIGHTNESS).state == "15.0"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"


async def test_out_of_range_value_is_refused(
    hass: HomeAssistant, motion_entry: MockConfigEntry, subentry_id: str
) -> None:
    """Values outside the configured range are refused."""
    coordinator = motion_entry.runtime_data.presets[subentry_id]
    with pytest.raises(ServiceValidationError):
        coordinator.async_set_value("night", "brightness", 150)


async def test_unknown_parameter_is_refused(
    hass: HomeAssistant, motion_entry: MockConfigEntry, subentry_id: str
) -> None:
    """Writing to an unknown parameter raises a validation error."""
    coordinator = motion_entry.runtime_data.presets[subentry_id]
    with pytest.raises(ServiceValidationError):
        coordinator.async_set_value("night", "volume", 5)


async def test_unknown_mode_is_refused(hass: HomeAssistant) -> None:
    """Writing a value for a mode the preset mode does not have raises an error."""
    entry = make_entry(presets=[make_preset("Heating", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = next(iter(entry.runtime_data.presets.values()))
    with pytest.raises(ServiceValidationError):
        coordinator.async_set_value("vacation", "brightness", 15)


async def test_boolean_text_and_select_parameters(hass: HomeAssistant) -> None:
    """Every parameter type gets a matching editor and value entity."""
    entry = make_entry(presets=[make_preset("Kitchen Light", [ACTIVE, MODE, LABEL])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await async_set_active_mode(hass, "night")
    await hass.services.async_call(
        "switch",
        "turn_on",
        {"entity_id": "switch.kitchen_light_night_active"},
        blocking=True,
    )
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": "select.kitchen_light_night_operating_mode", "option": "manual"},
        blocking=True,
    )
    await hass.services.async_call(
        "text",
        "set_value",
        {"entity_id": "text.kitchen_light_night_note", "value": "dimmed"},
        blocking=True,
    )

    assert hass.states.get("binary_sensor.kitchen_light_active").state == "on"
    assert hass.states.get("sensor.kitchen_light_operating_mode").state == "manual"
    assert hass.states.get("sensor.kitchen_light_note").state == "dimmed"


async def test_entity_ids_are_stable_across_value_changes(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Changing values never recreates entities."""
    before = set(hass.states.async_entity_ids())
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": NIGHT_BRIGHTNESS, "value": 42},
        blocking=True,
    )
    await async_set_active_mode(hass, "night")
    assert set(hass.states.async_entity_ids()) == before


async def test_text_parameter_carries_its_limits(hass: HomeAssistant) -> None:
    """Length, pattern and display mode reach the text editor."""
    entry = make_entry(presets=[make_preset("Kitchen Light", [LABEL])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get("text.kitchen_light_night_note")
    assert state.attributes["max"] == 10
    assert state.attributes["pattern"] == "[a-z]+"
    assert state.attributes["mode"] == "password"


async def test_number_parameter_carries_device_class(hass: HomeAssistant) -> None:
    """The device class reaches both the editor and the value sensor."""
    entry = make_entry(presets=[make_preset("Heating", [OFF_DELAY])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    editor = hass.states.get("number.heating_night_off_delay")
    assert editor.attributes["device_class"] == "duration"
    sensor = hass.states.get("sensor.heating_off_delay")
    assert sensor.attributes["device_class"] == "duration"
    assert sensor.attributes["state_class"] == "measurement"


async def test_date_and_time_values_are_timestamps(hass: HomeAssistant) -> None:
    """Date, time and datetime parameters publish a real point in time."""
    entry = make_entry(
        presets=[make_preset("Kitchen Light", [WAKE_UP, HOLIDAY, NEXT_SERVICE])]
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await async_set_active_mode(hass, "night")
    await hass.services.async_call(
        "time",
        "set_value",
        {"entity_id": "time.kitchen_light_night_wake_up", "time": "06:30:00"},
        blocking=True,
    )
    await hass.services.async_call(
        "date",
        "set_value",
        {"entity_id": "date.kitchen_light_night_holiday", "date": "2026-07-01"},
        blocking=True,
    )
    await hass.services.async_call(
        "datetime",
        "set_value",
        {
            "entity_id": "datetime.kitchen_light_night_next_service",
            "datetime": "2026-07-01 08:15:00",
        },
        blocking=True,
    )

    for entity_id in (
        "sensor.kitchen_light_wake_up",
        "sensor.kitchen_light_holiday",
        "sensor.kitchen_light_next_service",
    ):
        state = hass.states.get(entity_id)
        assert state.attributes["device_class"] == "timestamp"
        assert dt_util.parse_datetime(state.state) is not None

    # A time of day resolves to that time today.
    wake_up = dt_util.as_local(
        dt_util.parse_datetime(hass.states.get("sensor.kitchen_light_wake_up").state)
    )
    assert wake_up.date() == dt_util.now().date()
    assert (wake_up.hour, wake_up.minute) == (6, 30)

    holiday = dt_util.as_local(
        dt_util.parse_datetime(hass.states.get("sensor.kitchen_light_holiday").state)
    )
    assert (holiday.year, holiday.month, holiday.day) == (2026, 7, 1)
    assert (holiday.hour, holiday.minute) == (0, 0)


async def test_one_change_writes_exactly_one_editor_state(
    hass: HomeAssistant,
) -> None:
    """A value change must only touch the entity that edits that value.

    There were two independent fan-outs, both costing 19 of 20 writes:

    * the raw listeners sat in one flat list per preset, so every editor was
      notified of every value, and
    * every editor is a ``CoordinatorEntity``, so a change to the *active*
      mode pushed the recomputed state to all of them as well.
    """
    parameters = [
        {"key": f"p{index}", "name": f"P{index}", "type": "number", "maximum": 100}
        for index in range(5)
    ]
    writes: list[str] = []
    original = ModeValueEditorEntity.async_write_ha_state

    def counting(self: ModeValueEditorEntity) -> None:
        writes.append(self.entity_id)
        original(self)

    # Patched before the setup: the listeners capture the bound method as it is
    # at the time they subscribe.
    with patch.object(ModeValueEditorEntity, "async_write_ha_state", counting):
        entry = make_entry(presets=[make_preset("Lamp", parameters)])
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert len(entry.data["modes"]) * len(parameters) == 20

        # Both cases: a mode that is not active, and the active one - only
        # the second recomputes the state of the preset.
        for mode, expected_sensor in (("night", "unknown"), ("home", "42.0")):
            target = f"number.lamp_{mode}_p0"
            writes.clear()
            await hass.services.async_call(
                "number",
                "set_value",
                {"entity_id": target, "value": 42},
                blocking=True,
            )
            await hass.async_block_till_done()

            assert writes == [target], f"{mode}: {len(writes)} writes"
            assert hass.states.get(target).state == "42.0"
            # The value sensor follows the active mode, through the coordinator.
            assert hass.states.get("sensor.lamp_p0").state == expected_sensor


#: Every parameter type, with the entity that edits it and the entity that
#: publishes the resolved value.
UNSET_CASES = [
    (
        {"key": "num", "name": "Num", "type": "number", "maximum": 100},
        "number.lamp_home_num",
        "sensor.lamp_num",
    ),
    (
        {"key": "flag", "name": "Flag", "type": "boolean"},
        "switch.lamp_home_flag",
        "binary_sensor.lamp_flag",
    ),
    (
        {"key": "note", "name": "Note", "type": "text"},
        "text.lamp_home_note",
        "sensor.lamp_note",
    ),
    (
        {"key": "pick", "name": "Pick", "type": "select", "options": ["a", "b"]},
        "select.lamp_home_pick",
        "sensor.lamp_pick",
    ),
    (
        {"key": "when", "name": "When", "type": "datetime"},
        "datetime.lamp_home_when",
        "sensor.lamp_when",
    ),
    (
        {"key": "day", "name": "Day", "type": "date"},
        "date.lamp_home_day",
        "sensor.lamp_day",
    ),
    (
        {"key": "at", "name": "At", "type": "time"},
        "time.lamp_home_at",
        "sensor.lamp_at",
    ),
]


@pytest.mark.parametrize(("parameter", "editor", "value"), UNSET_CASES)
async def test_an_unset_value_is_unknown_for_every_type(
    hass: HomeAssistant, parameter: dict, editor: str, value: str
) -> None:
    """ "Nobody set this" has to be one answer, and the same one everywhere.

    A boolean used to fall back to ``False`` and a text to ``""``, so an
    unconfigured value was indistinguishable from a deliberate off or a
    deliberate empty string - while the editor entity for that very value
    already said ``unknown``. An automation reading the value sensor acted on
    a value the integration had invented.
    """
    entry = make_entry(presets=[make_preset("Lamp", [parameter])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(editor).state == STATE_UNKNOWN
    assert hass.states.get(value).state == STATE_UNKNOWN
    # And the attribute templates read agrees with both of them.
    assert hass.states.get("sensor.lamp_active_mode").attributes["values"] == {
        parameter["key"]: None
    }
