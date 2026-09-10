"""Tests for mode resolution, switching preset modes and error cases."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from .conftest import (
    BRIGHTNESS,
    OFF_DELAY,
    PRESET_MODE_ID,
    Hubs,
    async_activate_mode,
    async_setup_hubs,
    async_setup_one,
    make_preset,
    make_preset_mode,
    to_subentry,
)

PRESET_MODE_SENSOR = "sensor.house_mode_mode"
BRIGHTNESS_SENSOR = "sensor.motion_sensor_living_room_brightness"
MODE_SENSOR = "sensor.motion_sensor_living_room_active_mode"


async def _set_values(hass: HomeAssistant, hubs: Hubs) -> None:
    """Fill the example values of the motion sensor instance."""
    coordinator = hubs.preset
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


async def test_values_follow_active_mode(hass: HomeAssistant, motion: Hubs) -> None:
    """Switching the mode updates all value sensors immediately."""
    await _set_values(hass, motion)

    await async_activate_mode(hass, "night")
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"
    assert hass.states.get(MODE_SENSOR).state == "Night"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "15.0"
    assert (
        hass.states.get("sensor.motion_sensor_living_room_color_temperature").state
        == "2200.0"
    )
    assert hass.states.get("sensor.motion_sensor_living_room_off_delay").state == "30.0"

    await async_activate_mode(hass, "home")
    assert hass.states.get(MODE_SENSOR).state == "Home"
    assert hass.states.get(BRIGHTNESS_SENSOR).state == "80.0"


async def test_mode_sensor_attributes(hass: HomeAssistant, motion: Hubs) -> None:
    """The mode sensor exposes the resolved values as attributes."""
    await _set_values(hass, motion)
    await async_activate_mode(hass, "night")

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


async def test_initial_mode_is_default(hass: HomeAssistant, motion: Hubs) -> None:
    """Without a stored mode the default mode is active."""
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"
    assert hass.states.get(MODE_SENSOR).state == "Home"


# Modes ------------------------------------------------------------------------


def _state(entity: str, state: str) -> list[dict]:
    """A single state condition."""
    return [{"condition": "state", "entity_id": entity, "state": state}]


async def test_conditions_follow_an_entity(hass: HomeAssistant) -> None:
    """Following another entity is expressed as one condition per mode."""
    hass.states.async_set("sensor.mode_source", "Night")
    await async_setup_one(
        hass,
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
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"

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
    await async_setup_one(
        hass,
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
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("person.someone", "not_home")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Away"
    assert hass.states.get("sensor.heating_active_mode").state == "Away"

    # The window has priority: it comes first in the list.
    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_conditions_priority_is_the_mode_order(hass: HomeAssistant) -> None:
    """The first mode whose conditions match wins."""
    hass.states.async_set("binary_sensor.window", "off")
    hass.states.async_set("input_boolean.vacation", "off")
    await async_setup_one(
        hass,
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
    await async_setup_one(
        hass,
        modes=[
            {"key": "window_open", "name": "Window open"},
            {"key": "home", "name": "Home"},
            # Below the catch-all, so it is only reachable by hand.
            {"key": "night", "name": "Night"},
        ],
        conditions={"window_open": _state("binary_sensor.window", "on")},
    )
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"

    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_nothing_matches_leaves_the_preset_mode_unknown(
    hass: HomeAssistant,
) -> None:
    """Without a catch-all row no mode is active."""
    hass.states.async_set("binary_sensor.window", "off")
    await async_setup_one(
        hass,
        modes=[{"key": "window_open", "name": "Window open"}],
        conditions={"window_open": _state("binary_sensor.window", "on")},
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    assert hass.states.get(PRESET_MODE_SENSOR).state == "unknown"
    assert hass.states.get("sensor.heating_active_mode").state == "unknown"

    hass.states.async_set("binary_sensor.window", "on")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Window open"


async def test_external_entity_names_the_mode(hass: HomeAssistant) -> None:
    """The state of the source entity is the mode."""
    hass.states.async_set("input_select.house", "Night")
    await async_setup_one(
        hass,
        source_entity="input_select.house",
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
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


async def test_several_preset_modes_are_independent(hass: HomeAssistant) -> None:
    """Presets follow the preset mode they belong to."""
    await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(),
            make_preset_mode(
                title="Window State",
                modes=[
                    {"key": "closed", "name": "Closed"},
                    {"key": "open", "name": "Open"},
                ],
                subentry_id="2" * 32,
            ),
        ],
        presets=[
            make_preset("Heating", [BRIGHTNESS], subentry_id="a" * 32),
            make_preset(
                "Shutter",
                [BRIGHTNESS],
                subentry_id="b" * 32,
                preset_mode="2" * 32,
            ),
        ],
    )

    assert hass.states.get("sensor.house_mode_mode").state == "Home"
    assert hass.states.get("sensor.window_state_mode").state == "Closed"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"
    assert hass.states.get("sensor.shutter_active_mode").state == "Closed"

    await async_activate_mode(hass, "open", subentry_id="2" * 32)
    assert hass.states.get("sensor.window_state_mode").state == "Open"
    assert hass.states.get("sensor.shutter_active_mode").state == "Open"
    # The other preset mode is untouched.
    assert hass.states.get("sensor.house_mode_mode").state == "Home"
    assert hass.states.get("sensor.heating_active_mode").state == "Home"


async def test_a_second_preset_mode_is_independent(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Adding one leaves the first one where it was.

    The service used to fall back to "the only preset mode" when none was
    named, so every existing call broke the moment a second one appeared. It
    cannot be aimed at a preset mode at all any more, which settles that for
    good - but the runtime still has to keep the two apart.
    """
    hass.config_entries.async_add_subentry(
        motion.entry("preset_modes"),
        to_subentry(make_preset_mode(title="Window State", subentry_id="2" * 32)),
    )
    await hass.async_block_till_done()

    await async_activate_mode(hass, "night")
    await async_activate_mode(hass, "away", subentry_id="2" * 32)

    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"
    assert hass.states.get("sensor.window_state_mode").state == "Away"


async def test_preset_covers_every_mode_of_its_mode(hass: HomeAssistant) -> None:
    """A preset follows the active mode whatever it is."""
    hubs = await async_setup_one(hass, presets=[make_preset("Heating", [BRIGHTNESS])])

    coordinator = next(iter(hubs.runtime.presets.values()))
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
        await async_activate_mode(hass, mode_key)
        assert hass.states.get("sensor.heating_active_mode").state == name
        # Every mode has an editor entity.
        assert hass.states.get(f"number.heating_{mode_key}_brightness") is not None


async def test_preset_picks_up_a_new_mode(hass: HomeAssistant) -> None:
    """Adding a mode to the preset mode extends every preset of it."""
    hubs = await async_setup_one(hass, presets=[make_preset("Heating", [BRIGHTNESS])])
    assert hass.states.get("number.heating_vacation_brightness") is None

    hub = hubs.entry("preset_modes")
    subentry = hub.subentries[PRESET_MODE_ID]
    modes = [*subentry.data["modes"], {"key": "vacation", "name": "Vacation"}]
    hass.config_entries.async_update_subentry(
        hub, subentry, data={**subentry.data, "modes": modes}
    )
    await hass.async_block_till_done()

    assert hass.states.get("number.heating_vacation_brightness") is not None


async def test_missing_parameter_value_uses_default(hass: HomeAssistant) -> None:
    """A parameter without a stored value falls back to its default."""
    await async_setup_one(
        hass,
        presets=[make_preset("Heating", [{**BRIGHTNESS, "default": 42}, OFF_DELAY])],
    )

    assert hass.states.get("sensor.heating_brightness").state == "42.0"
    # No default and no stored value -> unknown, and reported as unset.
    assert hass.states.get("sensor.heating_off_delay").state == "unknown"
    values = hass.states.get("sensor.heating_active_mode").attributes["values"]
    assert values["off_delay"] is None


async def test_preset_of_an_empty_preset_mode_is_unknown(hass: HomeAssistant) -> None:
    """A preset whose preset mode has no modes left reports unknown."""
    await async_setup_one(
        hass, modes=[], presets=[make_preset("Heating", [BRIGHTNESS])]
    )

    assert hass.states.get("sensor.heating_active_mode").state == "unknown"
    assert hass.states.get("sensor.heating_brightness").state == "unknown"
    # Without modes there is nothing to edit either.
    assert hass.states.get("number.heating_night_brightness") is None


async def test_template_condition_reacts_to_state(hass: HomeAssistant) -> None:
    """A stored template condition is turned back into a real template."""
    hass.states.async_set("input_number.brightness", "5")
    await async_setup_one(
        hass,
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
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Night"

    hass.states.async_set("input_number.brightness", "80")
    await hass.async_block_till_done()
    assert hass.states.get(PRESET_MODE_SENSOR).state == "Home"
