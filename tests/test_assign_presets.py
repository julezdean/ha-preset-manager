"""Tests for assigning presets from the preset mode and from the blueprint."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import issue_registry as ir

from custom_components.preset_manager.const import (
    CONF_BLUEPRINT,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    CONF_PRESETS,
    DOMAIN,
    SUBENTRY_TYPE_BLUEPRINT,
    SUBENTRY_TYPE_PRESET_MODE,
)

from .conftest import (
    BLUEPRINT_ID,
    BRIGHTNESS,
    PRESET_ID,
    PRESET_MODE_ID,
    TARGET_TEMPERATURE,
    Hubs,
    async_setup_hubs,
    make_blueprint,
    make_preset,
    make_preset_mode,
)

OTHER_MODE_ID = "2" * 32
OTHER_PRESET_ID = "b" * 32


async def _assign(
    hass: HomeAssistant,
    hubs: Hubs,
    kind: str,
    subentry_type: str,
    subentry_id: str,
    presets: list[str],
) -> dict:
    """Run the assign step of one preset mode or blueprint."""
    result = await hass.config_entries.subentries.async_init(
        (hubs.entry(kind).entry_id, subentry_type),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": subentry_id,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_presets"}
    )
    assert result["step_id"] == "assign_presets"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRESETS: presets}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()
    return result


def _options(result: dict) -> list[tuple[str, str]]:
    """Return the (value, label) pairs the picker offers."""
    schema = result["data_schema"].schema
    key = next(item for item in schema if str(item) == CONF_PRESETS)
    return [(item["value"], item["label"]) for item in schema[key].config["options"]]


async def test_the_list_starts_with_what_already_follows(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The step answers "what follows this?" without opening every preset."""
    result = await hass.config_entries.subentries.async_init(
        (motion.entry("preset_modes").entry_id, SUBENTRY_TYPE_PRESET_MODE),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": PRESET_MODE_ID,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_presets"}
    )

    key = next(
        item for item in result["data_schema"].schema if str(item) == CONF_PRESETS
    )
    assert key.description["suggested_value"] == [PRESET_ID]
    assert result["description_placeholders"]["name"] == "House Mode"


async def test_adding_a_preset_moves_it_from_its_old_preset_mode(
    hass: HomeAssistant,
) -> None:
    """The same field the preset writes itself, written from the other side."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(),
            make_preset_mode(
                title="Window State",
                modes=[{"key": "closed", "name": "Closed"}],
                subentry_id=OTHER_MODE_ID,
            ),
        ],
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )

    await _assign(
        hass,
        hubs,
        "preset_modes",
        SUBENTRY_TYPE_PRESET_MODE,
        OTHER_MODE_ID,
        [PRESET_ID],
    )

    preset = hubs.entry("presets").subentries[PRESET_ID]
    assert preset.data[CONF_PRESET_MODE] == OTHER_MODE_ID
    assert hass.states.get("sensor.heating_active_mode").state == "Closed"
    # The modes of the preset mode it left are not kept anywhere.
    assert CONF_MODES not in preset.data


async def test_removing_a_preset_leaves_it_with_its_modes(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Taking a preset off keeps everything but the active mode."""
    motion.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    await _assign(
        hass, motion, "preset_modes", SUBENTRY_TYPE_PRESET_MODE, PRESET_MODE_ID, []
    )

    preset = motion.entry("presets").subentries[PRESET_ID]
    assert CONF_PRESET_MODE not in preset.data
    assert [item["key"] for item in preset.data[CONF_MODES]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]
    assert (
        hass.states.get("number.motion_sensor_living_room_night_brightness").state
        == "15.0"
    )
    issues = ir.async_get(hass)
    assert issues.async_get_issue(DOMAIN, f"orphaned_preset_{PRESET_ID}") is not None


async def test_a_preset_following_another_one_is_marked(hass: HomeAssistant) -> None:
    """Adding it would move it, so the picker says where it is now."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(),
            make_preset_mode(title="Window State", subentry_id=OTHER_MODE_ID),
        ],
        presets=[
            make_preset("Heating", [BRIGHTNESS]),
            make_preset(
                "Shutter",
                [BRIGHTNESS],
                subentry_id=OTHER_PRESET_ID,
                preset_mode=OTHER_MODE_ID,
            ),
        ],
    )

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("preset_modes").entry_id, SUBENTRY_TYPE_PRESET_MODE),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": PRESET_MODE_ID,
        },
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_presets"}
    )

    labels = dict(_options(result))
    # Its own preset is named plainly, the one of the other preset mode is not.
    assert labels[PRESET_ID] == "Heating"
    assert labels[OTHER_PRESET_ID] == "Shutter (Window State)"


async def test_assigning_presets_to_a_blueprint(hass: HomeAssistant) -> None:
    """The blueprint side writes the same key the preset writes itself."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [BRIGHTNESS])],
    )
    assert hass.states.get("number.heating_bath_home_brightness")

    await _assign(
        hass,
        hubs,
        "blueprints",
        SUBENTRY_TYPE_BLUEPRINT,
        BLUEPRINT_ID,
        [PRESET_ID],
    )

    preset = hubs.entry("presets").subentries[PRESET_ID]
    assert preset.data[CONF_BLUEPRINT] == BLUEPRINT_ID
    # Its own parameter list is gone; the blueprint's is what it has now.
    assert CONF_PARAMETERS not in preset.data
    assert hass.states.get("number.heating_bath_home_brightness") is None
    assert hass.states.get("number.heating_bath_home_target_temperature")


async def test_removing_a_preset_from_a_blueprint_keeps_the_parameters(
    hass: HomeAssistant,
) -> None:
    """It keeps the parameters of the blueprint as its own, values included."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID)],
    )
    hubs.preset.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    await _assign(hass, hubs, "blueprints", SUBENTRY_TYPE_BLUEPRINT, BLUEPRINT_ID, [])

    preset = hubs.entry("presets").subentries[PRESET_ID]
    assert CONF_BLUEPRINT not in preset.data
    assert [item["key"] for item in preset.data[CONF_PARAMETERS]] == [
        TARGET_TEMPERATURE["key"]
    ]
    assert (
        hass.states.get("number.heating_bath_night_target_temperature").state == "17.0"
    )
