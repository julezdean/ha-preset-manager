"""Tests for mode resolution, switching preset modes and error cases."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager.const import (
    DOMAIN,
    SERVICE_SET_ACTIVE_MODE,
)

from .conftest import (
    BRIGHTNESS,
    OFF_DELAY,
    async_set_active_mode,
    make_entry,
    make_preset,
)

SELECT = "select.house_mode_active_mode"
PRESET_MODE_SENSOR = "sensor.house_mode_mode"
BRIGHTNESS_SENSOR = "sensor.motion_sensor_living_room_brightness"
MODE_SENSOR = "sensor.motion_sensor_living_room_active_mode"


async def _set_values(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    """Fill the example values of the motion sensor instance."""
    coordinator = next(iter(entry.runtime_data.presets.values()))
    for mode_key, brightness, color_temperature, delay in (
        ("home", 80, 3000, 120),
        ("away", 0, 2700, 0),
        ("night", 15, 2200, 30),
        ("window_open", 5, 2500, 10),
    ):
        coordinator.async_set_value(mode_key, "brightness", brightness)
        coordinator.async_set_value(mode_key, "color_temperature", color_temperature)
        coordinator.async_set_value(mode_key, "off_delay", delay)
    await hass.async_block_till_done()


async def test_values_follow_active_mode(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Switching the mode updates all value sensors immediately."""
    await _set_values(hass, motion_entry)

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Night"},
        blocking=True,
    )
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"
    assert hass.states.get(MODE_SENSOR).state == "Night"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"
    assert (
        hass.states.get("sensor.motion_sensor_living_room_color_temperature").state
        == "2200.0"
    )
    assert hass.states.get("sensor.motion_sensor_living_room_off_delay").state == "30.0"

    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Home"},
        blocking=True,
    )
    assert hass.states.get(MODE_SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"


async def test_mode_sensor_attributes(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """The mode sensor exposes the resolved values as attributes."""
    await _set_values(hass, motion_entry)
    await hass.services.async_call(
        "select",
        "select_option",
        {"entity_id": SELECT, "option": "Night"},
        blocking=True,
    )

    attributes = hass.states.get(MODE_SENSOR).attributes
    assert attributes["mode_key"] == "night"
    assert attributes["mode_source"] == "House Mode"
    assert attributes["modes"] == ["Home", "Away", "Night", "Window open"]
    assert attributes["values"] == {
        "brightness": 15.0,
        "color_temperature": 2200.0,
        "off_delay": 30.0,
    }

    preset_mode_attributes = hass.states.get(PRESET_MODE_SENSOR).attributes
    assert preset_mode_attributes["mode_key"] == "night"
    assert preset_mode_attributes["automatic"] is False


async def test_initial_mode_is_default(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Without a stored mode the default mode is active."""
    assert hass.states.get(SELECT).state == "Home"
    assert hass.states.get(MODE_SENSOR).state == "Home"


async def test_set_active_mode_service(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """The entity service accepts keys as well as display names."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_ACTIVE_MODE,
        {"mode": "window_open"},
        target={"entity_id": SELECT},
        blocking=True,
    )
    assert hass.states.get(SELECT).state == "Window open"

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_ACTIVE_MODE,
        {"mode": "Away"},
        target={"entity_id": SELECT},
        blocking=True,
    )
    assert hass.states.get(SELECT).state == "Away"

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_ACTIVE_MODE,
            {"mode": "Party"},
            target={"entity_id": SELECT},
            blocking=True,
        )


# Modes ------------------------------------------------------------------------


def _state(entity: str, state: str) -> list[dict]:
    """A single state condition."""
    return [{"condition": "state", "entity_id": entity, "state": state}]


async def test_conditions_follow_an_entity(hass: HomeAssistant) -> None:
    """Following another entity is expressed as one condition per mode."""
    hass.states.async_set("sensor.mode_source", "Night")
    entry = make_entry(
        conditions={
            key: _state("sensor.mode_source", name)
            for key, name in (
                ("home", "Home"),
                ("away", "Away"),
                ("night", "Night"),
                ("window_open", "Window open"),
            )
        },
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"
    assert hass.states.get("switch.house_mode_automatic").state == "on"

    hass.states.async_set("sensor.mode_source", "Window open")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"
    assert hass.states.get("sensor.heating_active_mode").state == "Window open"

    # Every mode has conditions here, so an unmatched state leaves the
    # preset mode without an active mode.
    hass.states.async_set("sensor.mode_source", "Party")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "unknown"
    assert hass.states.get("sensor.heating_active_mode").state == "unknown"


async def test_conditions_from_a_template(hass: HomeAssistant) -> None:
    """A template condition per mode reacts to state changes."""
    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("person.someone", "home")
    entry = make_entry(
        conditions={
            "window_open": [
                {
                    "condition": "template",
                    "value_template": ("{{ is_state('binary_sensor.window', 'on') }}"),
                }
            ],
            "away": [
                {
                    "condition": "template",
                    "value_template": ("{{ not is_state('person.someone', 'home') }}"),
                }
            ],
        },
        modes=[
            {"key": "window_open", "name": "Window open"},
            {"key": "away", "name": "Away"},
            {"key": "home", "name": "Home"},
        ],
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("person.someone", "not_home")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Away"
    assert hass.states.get("sensor.heating_active_mode").state == "Away"

    # The window has priority: it comes first in the list.
    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_automatic_preset_mode_is_not_writable(hass: HomeAssistant) -> None:
    """A preset mode with conditions refuses manual changes while automatic."""
    hass.states.async_set("binary_sensor.window", "off")
    entry = make_entry(conditions={"night": _state("binary_sensor.window", "on")})
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    with pytest.raises(ServiceValidationError):
        await async_set_active_mode(hass, "Night")


async def test_conditions_priority_is_the_mode_order(hass: HomeAssistant) -> None:
    """The first mode whose conditions match wins."""
    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("input_boolean.vacation", "off")
    entry = make_entry(
        modes=[
            {"key": "window_open", "name": "Window open"},
            {"key": "away", "name": "Away"},
            {"key": "home", "name": "Home"},
        ],
        conditions={
            "window_open": _state("binary_sensor.window", "on"),
            "away": _state("input_boolean.vacation", "on"),
        },
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    # Nothing matches -> "Home" catches it, because it has no conditions.
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("input_boolean.vacation", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Away"

    # The window is higher in the list and wins over the vacation switch.
    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"

    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("input_boolean.vacation", "off")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"


async def test_mode_without_conditions_catches_everything_below_it(
    hass: HomeAssistant,
) -> None:
    """A mode without conditions is the fallback of the rows above it."""
    hass.states.async_set("binary_sensor.window", "off")
    entry = make_entry(
        modes=[
            {"key": "window_open", "name": "Window open"},
            {"key": "home", "name": "Home"},
            # Below the catch-all, so it is only reachable by hand.
            {"key": "night", "name": "Night"},
        ],
        conditions={"window_open": _state("binary_sensor.window", "on")},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_nothing_matches_leaves_the_preset_mode_unknown(
    hass: HomeAssistant,
) -> None:
    """Without a catch-all row no mode is active."""
    hass.states.async_set("binary_sensor.window", "off")
    entry = make_entry(
        modes=[{"key": "window_open", "name": "Window open"}],
        conditions={"window_open": _state("binary_sensor.window", "on")},
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "unknown"
    assert hass.states.get("sensor.heating_active_mode").state == "unknown"

    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_external_entity_names_the_mode(hass: HomeAssistant) -> None:
    """The state of the source entity is the mode."""
    hass.states.async_set("input_select.house", "Night")
    entry = make_entry(
        source_entity="input_select.house",
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"
    assert hass.states.get("sensor.heating_active_mode").state == "Night"
    # There is no automatic to report - the entity is the automatic.
    attributes = hass.states.get(PRESET_MODE_SENSOR).attributes
    assert attributes["source_entity"] == "input_select.house"
    assert "automatic" not in attributes

    hass.states.async_set("input_select.house", "Away")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Away"

    # The key and the slug work as well as the display name.
    hass.states.async_set("input_select.house", "window_open")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_external_state_without_a_mode_is_unknown(
    hass: HomeAssistant,
) -> None:
    """A state naming no mode, and an unavailable entity, mean unknown."""
    hass.states.async_set("input_select.house", "Party")
    entry = make_entry(
        source_entity="input_select.house",
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "unknown"
    assert hass.states.get("sensor.heating_active_mode").state == "unknown"

    hass.states.async_set("input_select.house", "Home")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("input_select.house", "unavailable")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "unknown"


async def test_external_preset_mode_has_no_switch_and_no_select(
    hass: HomeAssistant,
) -> None:
    """Nothing is left to switch or to select from the outside."""
    hass.states.async_set("input_select.house", "Home")
    entry = make_entry(
        source_entity="input_select.house",
        conditions={"night": _state("binary_sensor.window", "on")},
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SELECT) is None
    assert hass.states.get("switch.house_mode_automatic") is None
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    # The conditions are stored but never evaluated.
    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"


async def test_external_preset_mode_refuses_manual_changes(hass: HomeAssistant) -> None:
    """The mode belongs to the entity, not to the user.

    There is no selector to target, so the refusal is tested where it lives:
    an external preset mode has no way in from the outside at all.
    """
    hass.states.async_set("input_select.house", "Home")
    entry = make_entry(source_entity="input_select.house")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get(SELECT) is None
    with pytest.raises(ServiceValidationError):
        entry.runtime_data.preset_mode.async_set_active_mode("Night")


async def test_preset_mode_without_conditions_has_no_switch(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Without conditions a preset mode is purely manual."""
    assert hass.states.get("switch.house_mode_automatic") is None
    assert hass.states.get(SELECT) is not None


async def test_several_preset_modes_are_independent(hass: HomeAssistant) -> None:
    """Presets follow the preset mode they belong to."""
    house = make_entry(
        presets=[make_preset("Heating", [BRIGHTNESS], subentry_id="a" * 32)]
    )
    window = make_entry(
        title="Window State",
        modes=[
            {"key": "closed", "name": "Closed"},
            {"key": "open", "name": "Open"},
        ],
        entry_id="2" * 32,
        presets=[make_preset("Shutter", [BRIGHTNESS], subentry_id="b" * 32)],
    )
    for entry in (house, window):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.house_mode_mode").state == "Home"
    assert hass.states.get("sensor.window_state_mode").state == "Closed"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"
    assert hass.states.get("sensor.shutter_active_mode").state == "Closed"

    await async_set_active_mode(
        hass, "Open", entity_id="select.window_state_active_mode"
    )
    assert hass.states.get("sensor.window_state_mode").state == "Open"
    assert hass.states.get("sensor.shutter_active_mode").state == "Open"
    # The other preset mode is untouched.
    assert hass.states.get("sensor.house_mode_mode").state == "Home"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"


async def test_a_second_preset_mode_is_addressed_by_its_own_selector(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Adding a second preset mode leaves calls to the first one working.

    The service used to fall back to "the only preset mode" when none was
    named, so every existing call broke the moment a second one appeared.
    Targeting a selector cannot become ambiguous.
    """
    entry = make_entry(title="Window State", entry_id="2" * 32)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await async_set_active_mode(hass, "Night")
    assert hass.states.get(SELECT).state == "Night"

    await async_set_active_mode(
        hass, "Away", entity_id="select.window_state_active_mode"
    )
    assert hass.states.get("select.window_state_active_mode").state == "Away"
    # The first preset mode is untouched.
    assert hass.states.get(SELECT).state == "Night"


# Fallbacks and missing data ---------------------------------------------------


async def test_preset_covers_every_mode_of_its_mode(hass: HomeAssistant) -> None:
    """A preset follows the active mode whatever it is."""
    entry = make_entry(presets=[make_preset("Heating", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = next(iter(entry.runtime_data.presets.values()))
    assert [mode.name for mode in coordinator.modes] == [
        "Home",
        "Away",
        "Night",
        "Window open",
    ]

    for mode_key, name in (
        ("home", "Home"),
        ("away", "Away"),
        ("night", "Night"),
        ("window_open", "Window open"),
    ):
        await async_set_active_mode(hass, mode_key)
        assert hass.states.get("sensor.heating_active_mode").state == name
        # Every mode has an editor entity.
        assert hass.states.get(f"number.heating_{mode_key}_brightness") is not None


async def test_preset_picks_up_a_new_mode(hass: HomeAssistant) -> None:
    """Adding a mode to the preset mode extends every preset of it."""
    entry = make_entry(presets=[make_preset("Heating", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get("number.heating_vacation_brightness") is None

    modes = [*entry.data["modes"], {"key": "vacation", "name": "Vacation"}]
    hass.config_entries.async_update_entry(entry, data={**entry.data, "modes": modes})
    await hass.async_block_till_done()

    assert hass.states.get("number.heating_vacation_brightness") is not None


async def test_missing_parameter_value_uses_default(hass: HomeAssistant) -> None:
    """A parameter without a stored value falls back to its default."""
    entry = make_entry(
        presets=[make_preset("Heating", [{**BRIGHTNESS, "default": 42}, OFF_DELAY])]
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heating_brightness").state == "42.0"
    # No default and no stored value -> unknown, and reported as unset.
    assert hass.states.get("sensor.heating_off_delay").state == "unknown"
    values = hass.states.get("sensor.heating_active_mode").attributes["values"]
    assert values["off_delay"] is None


async def test_preset_of_an_empty_preset_mode_is_unknown(hass: HomeAssistant) -> None:
    """A preset whose preset mode has no modes left reports unknown."""
    entry = make_entry(modes=[], presets=[make_preset("Heating", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heating_active_mode").state == "unknown"
    assert hass.states.get("sensor.heating_brightness").state == "unknown"
    # Without modes there is nothing to edit either.
    assert hass.states.get("number.heating_night_brightness") is None


async def test_template_condition_reacts_to_state(hass: HomeAssistant) -> None:
    """A stored template condition is turned back into a real template."""
    hass.states.async_set("input_number.brightness", "5")
    entry = make_entry(
        modes=[
            {"key": "night", "name": "Night"},
            {"key": "home", "name": "Home"},
        ],
        conditions={
            "night": [
                {
                    "condition": "template",
                    # Stored as a plain string in the subentry.
                    "value_template": (
                        "{{ states('input_number.brightness') | int < 10 }}"
                    ),
                }
            ]
        },
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"

    hass.states.async_set("input_number.brightness", "80")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"
