"""Tests for duplicating a preset, a preset mode and a blueprint."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.preset_manager.const import (
    CONF_BLUEPRINT,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    CONF_SOURCE_ENTITY,
    SUBENTRY_TYPE_BLUEPRINT,
    SUBENTRY_TYPE_PRESET,
    SUBENTRY_TYPE_PRESET_MODE,
)
from custom_components.preset_manager.store import async_get_store

from .conftest import (
    BLUEPRINT_ID,
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_setup_hubs,
    make_blueprint,
    make_preset,
    make_preset_mode,
)


async def _duplicate(
    hass: HomeAssistant,
    hubs: Hubs,
    kind: str,
    subentry_type: str,
    subentry_id: str,
    name: str,
) -> dict:
    """Run the duplicate step of one object."""
    result = await hass.config_entries.subentries.async_init(
        (hubs.entry(kind).entry_id, subentry_type),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": subentry_id,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "duplicate"}
    )
    assert result["step_id"] == "duplicate"
    assert result["description_placeholders"]["name"]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"copy_name": name}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "duplicated"
    await hass.async_block_till_done()
    return result


def _copy(hubs: Hubs, kind: str, title: str) -> tuple[str, dict]:
    """Return the id and the data of the copy."""
    return next(
        (subentry_id, dict(subentry.data))
        for subentry_id, subentry in hubs.entry(kind).subentries.items()
        if subentry.title == title
    )


async def test_duplicating_a_preset_takes_its_values_along(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A copy without the values would be the empty shell of a preset."""
    motion.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    await _duplicate(
        hass, motion, "presets", SUBENTRY_TYPE_PRESET, PRESET_ID, "Motion Sensor Hall"
    )

    copy_id, data = _copy(motion, "presets", "Motion Sensor Hall")
    assert copy_id != PRESET_ID
    assert [item["key"] for item in data[CONF_PARAMETERS]] == [
        "brightness",
        "color_temperature",
        "off_delay",
    ]
    # It follows the same preset mode ...
    assert data[CONF_PRESET_MODE] == PRESET_MODE_ID
    # ... and carries the values of the preset it was made from.
    assert async_get_store(hass).get_value(copy_id, "night", "brightness") == 15.0
    assert hass.states.get("number.motion_sensor_hall_night_brightness").state == "15.0"
    # The original is untouched.
    assert (
        hass.states.get("number.motion_sensor_living_room_night_brightness").state
        == "15.0"
    )


async def test_duplicating_a_preset_keeps_its_blueprint(hass: HomeAssistant) -> None:
    """A copy of a bound preset follows the same blueprint."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID)],
    )

    await _duplicate(
        hass, hubs, "presets", SUBENTRY_TYPE_PRESET, PRESET_ID, "Heating Bedroom"
    )

    _copy_id, data = _copy(hubs, "presets", "Heating Bedroom")
    assert data[CONF_BLUEPRINT] == BLUEPRINT_ID
    assert CONF_PARAMETERS not in data
    assert hass.states.get("sensor.heating_bedroom_target_temperature") is not None


async def test_duplicating_a_preset_mode_drops_its_source_entity(
    hass: HomeAssistant,
) -> None:
    """Two preset modes on the same entity would be one with two names."""
    hass.states.async_set("input_select.house", "Night")
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode(source_entity="input_select.house")],
    )

    await _duplicate(
        hass,
        hubs,
        "preset_modes",
        SUBENTRY_TYPE_PRESET_MODE,
        PRESET_MODE_ID,
        "Window State",
    )

    _copy_id, data = _copy(hubs, "preset_modes", "Window State")
    assert [item["key"] for item in data[CONF_MODES]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]
    assert CONF_SOURCE_ENTITY not in data
    # The copy decides for itself, so it has a selector of its own.
    assert hass.states.get("select.window_state_active_mode") is not None
    # The original still follows its entity, and has none.
    assert hass.states.get("select.house_mode_active_mode") is None


async def test_duplicating_a_blueprint_leaves_its_presets_alone(
    hass: HomeAssistant,
) -> None:
    """The copy is a second blueprint, not a second owner of the same presets."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID)],
    )

    await _duplicate(
        hass, hubs, "blueprints", SUBENTRY_TYPE_BLUEPRINT, BLUEPRINT_ID, "Cooling"
    )

    copy_id, data = _copy(hubs, "blueprints", "Cooling")
    assert copy_id != BLUEPRINT_ID
    assert [item["key"] for item in data[CONF_PARAMETERS]] == ["target_temperature"]
    preset = hubs.entry("presets").subentries[PRESET_ID]
    assert preset.data[CONF_BLUEPRINT] == BLUEPRINT_ID


async def test_a_duplicated_preset_mode_can_be_edited_on_its_own(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The copy is a preset mode like any other, with its own id."""
    await _duplicate(
        hass,
        motion,
        "preset_modes",
        SUBENTRY_TYPE_PRESET_MODE,
        PRESET_MODE_ID,
        "Window State",
    )
    copy_id, _data = _copy(motion, "preset_modes", "Window State")

    result = await hass.config_entries.subentries.async_init(
        (motion.entry("preset_modes").entry_id, SUBENTRY_TYPE_PRESET_MODE),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": copy_id,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_modes"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_MODES: [{"key": "closed", "name": "Closed"}]},
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert hass.states.get("sensor.window_state_mode").state == "Closed"
    # The preset mode it was copied from kept its own modes.
    assert hass.states.get("sensor.house_mode_mode").state == "Home"
