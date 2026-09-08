"""Tests for the config and subentry flows."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.preset_manager.const import (
    CONF_CONDITIONS,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    SUBENTRY_TYPE_BLUEPRINT,
    SUBENTRY_TYPE_PRESET,
    SUBENTRY_TYPE_PRESET_MODE,
    UID_CONFIG,
    UID_SEPARATOR,
)
from custom_components.preset_manager.store import async_get_store

from .conftest import (
    BLUEPRINT_ID,
    BRIGHTNESS,
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_setup_hubs,
    async_setup_one,
    make_blueprint,
    make_preset,
    make_preset_mode,
)


async def _reconfigure_preset_mode(hass: HomeAssistant, hubs: Hubs) -> dict:
    """Open the reconfiguration menu of the preset mode."""
    return await hass.config_entries.subentries.async_init(
        (hubs.entry("preset_modes").entry_id, SUBENTRY_TYPE_PRESET_MODE),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": PRESET_MODE_ID,
        },
    )


async def _reconfigure_preset(
    hass: HomeAssistant, hubs: Hubs, subentry_id: str = PRESET_ID
) -> dict:
    """Open the reconfiguration menu of a preset."""
    return await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": subentry_id,
        },
    )


def _modes_of(hubs: Hubs) -> list[dict]:
    """Return the stored modes of the preset mode."""
    subentry = hubs.entry("preset_modes").subentries[PRESET_MODE_ID]
    return list(subentry.data[CONF_MODES])


# Config flow ------------------------------------------------------------------


async def test_config_flow_creates_a_preset_mode(hass: HomeAssistant) -> None:
    """Every config entry is one preset mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    # The first step picks the kind of entry: a preset mode or a blueprint.
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == ["preset_mode", "preset", "blueprint"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode"}
    )
    assert result["step_id"] == "preset_mode"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "House Mode", CONF_MODES: ["Home", "Away", "Night"]},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    subentry = next(iter(entry.subentries.values()))
    assert subentry.title == "House Mode"
    assert [item["key"] for item in subentry.data[CONF_MODES]] == [
        "home",
        "away",
        "night",
    ]
    assert hass.states.get("select.house_mode_active_mode").state == "Home"


async def test_config_flow_rejects_duplicates(hass: HomeAssistant) -> None:
    """Duplicate mode names are refused."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "House Mode", CONF_MODES: ["Night", "night"]}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MODES: "duplicate_mode"}


async def test_second_preset_mode_joins_the_hub(hass: HomeAssistant) -> None:
    """A further preset mode is added to the hub that already exists."""
    await async_setup_one(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "Window State", CONF_MODES: ["Closed", "Open"]},
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "preset_modes_added"
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert hass.states.get("sensor.window_state_mode").state == "Closed"
    assert hass.states.get("select.window_state_active_mode") is not None
    # The first preset mode is untouched.
    assert hass.states.get("sensor.house_mode_mode").state == "Home"


# Options flow -----------------------------------------------------------------


async def _manage_modes(hass: HomeAssistant, hubs: Hubs) -> dict:
    """Open the mode list of a preset mode."""
    result = await _reconfigure_preset_mode(hass, hubs)
    assert result["step_id"] == "reconfigure"
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_modes"}
    )


async def test_preset_mode_settings_set_and_clear_the_source_entity(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Naming an entity hands the preset mode over to it, clearing it hands it back."""
    hass.states.async_set("input_select.house", "Night")

    result = await _reconfigure_preset_mode(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode_settings"}
    )
    assert result["step_id"] == "preset_mode_settings"
    # The name is not in here; renaming has its own entry in every menu.
    assert set(result["data_schema"].schema) == {CONF_SOURCE_ENTITY}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_SOURCE_ENTITY: "input_select.house"}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert hass.states.get("sensor.house_mode_mode").state == "Night"
    assert hass.states.get("select.house_mode_active_mode") is None

    result = await _reconfigure_preset_mode(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode_settings"}
    )
    # The form is seeded with the entity that is set.
    suggested = {
        str(item): (item.description or {}).get("suggested_value")
        for item in result["data_schema"].schema
    }
    assert suggested[CONF_SOURCE_ENTITY] == "input_select.house"

    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    await hass.async_block_till_done()

    # Without an entity the preset mode is its own again, selector included.
    assert hass.states.get("select.house_mode_active_mode") is not None


async def test_manage_modes_renames_and_keeps_values(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Renaming a row keeps its key, and therefore its stored values."""
    coordinator = next(iter(motion.runtime.presets.values()))
    coordinator.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    result = await _manage_modes(hass, motion)
    assert result["step_id"] == "manage_modes"

    # The list is seeded with the current modes, keys included.
    schema = result["data_schema"].schema
    key = next(item for item in schema if str(item) == CONF_MODES)
    seeded = key.description["suggested_value"]
    assert [row["key"] for row in seeded] == ["home", "away", "night", "window_open"]

    renamed = [dict(row) for row in seeded]
    renamed[2]["name"] = "Sleep"
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MODES: renamed}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    preset_mode = motion.preset_mode
    assert preset_mode.config.mode("night").name == "Sleep"
    assert (
        hass.states.get("number.motion_sensor_living_room_night_brightness").state
        == "15.0"
    )


async def test_manage_modes_adds_reorders_and_deletes(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """One list handles adding, ordering and deleting."""
    result = await _manage_modes(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODES: [
                # Reordered, "away" deleted, a new row without a key added.
                {"key": "night", "name": "Night"},
                {"name": "Vacation"},
                {"key": "home", "name": "Home"},
                {"key": "window_open", "name": "Window open"},
            ]
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert [row["key"] for row in _modes_of(motion)] == [
        "night",
        "vacation",
        "home",
        "window_open",
    ]
    # The order is also the order of the select options.
    assert hass.states.get("select.house_mode_active_mode").attributes["options"] == [
        "Night",
        "Vacation",
        "Home",
        "Window open",
    ]
    # The deleted mode takes its editor entities with it.
    assert hass.states.get("number.motion_sensor_living_room_away_brightness") is None
    assert hass.states.get("number.motion_sensor_living_room_vacation_brightness")


async def test_a_new_mode_never_takes_the_key_of_a_renamed_one(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A key is only free once no row keeps it, wherever that row sits.

    Adding "Night" above the mode that is renamed to "Evening" in the very
    same submit used to hand the new row the key the old one keeps: two modes
    with the key "night", sharing their values and colliding in their unique
    ids.
    """
    result = await _manage_modes(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODES: [
                {"key": "home", "name": "Home"},
                # New row, named like the mode two rows below it.
                {"name": "Night"},
                {"key": "away", "name": "Away"},
                {"key": "night", "name": "Evening"},
                {"key": "window_open", "name": "Window open"},
            ]
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    keys = [row["key"] for row in _modes_of(motion)]
    assert len(keys) == len(set(keys))
    assert keys == ["home", "night_2", "away", "night", "window_open"]

    # Both modes got an editor entity of their own. They are checked by unique
    # id: the renamed mode keeps the entity id it already had, so the new
    # "Night" is the one that has to move out of the way.
    registry = er.async_get(hass)
    unique_ids = {
        item.unique_id
        for item in er.async_entries_for_config_entry(
            registry, motion.entry("presets").entry_id
        )
    }
    cfg = f"{PRESET_ID}_{UID_CONFIG}"
    assert f"{cfg}_night{UID_SEPARATOR}brightness" in unique_ids
    assert f"{cfg}_night_2{UID_SEPARATOR}brightness" in unique_ids


async def test_two_rows_with_the_same_mode_key_are_refused(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The key field is read_only in the form, but not in its YAML editor."""
    result = await _manage_modes(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODES: [
                {"key": "home", "name": "Home"},
                {"key": "home", "name": "Copy of home"},
            ]
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MODES: "duplicate_mode_key"}


async def test_manage_modes_sets_conditions(hass: HomeAssistant, motion: Hubs) -> None:
    """Conditions are set in the same list, and drive the preset mode."""
    hass.states.async_set("binary_sensor.window", "on")

    result = await _manage_modes(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_MODES: [
                {
                    "key": "window_open",
                    "name": "Window open",
                    "conditions": [
                        {
                            "condition": "state",
                            "entity_id": "binary_sensor.window",
                            "state": "on",
                        }
                    ],
                },
                {"key": "home", "name": "Home"},
            ]
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    # Conditions turn the preset mode automatic.
    assert hass.states.get("switch.house_mode_automatic").state == "on"
    assert hass.states.get("sensor.house_mode_mode").state == "Window open"

    hass.states.async_set("binary_sensor.window", "off")
    await hass.async_block_till_done()
    # Nothing matches any more -> the default mode takes over.
    assert hass.states.get("sensor.house_mode_mode").state == "Home"


async def test_manage_modes_rejects_an_empty_list(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """At least one mode has to remain."""
    result = await _manage_modes(hass, motion)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MODES: []}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MODES: "no_modes"}


async def test_create_preset_in_the_presets_hub(hass: HomeAssistant) -> None:
    """A preset names the preset mode it follows; it is not inside one."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(
                title="Window State",
                modes=[
                    {"key": "closed", "name": "Closed"},
                    {"key": "open", "name": "Open"},
                ],
            )
        ],
        presets=[],
    )

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    assert result["step_id"] == "user"
    # No blueprint field: there is none to follow.
    assert set(result["data_schema"].schema) == {"name", CONF_PRESET_MODE}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Shutter Living Room", CONF_PRESET_MODE: PRESET_MODE_ID},
    )
    assert result["step_id"] == "manage_parameters"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: [{"name": "Position", "type": "number"}]}
    )
    # A new row goes straight into its type specific details.
    assert result["step_id"] == "parameter_details"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"default": 50}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(
        item
        for item in hubs.entry("presets").subentries.values()
        if item.title == "Shutter Living Room"
    )
    assert subentry.data[CONF_PARAMETERS][0]["key"] == "position"

    # It follows the window state preset mode and covers every mode of it.
    assert hass.states.get("sensor.shutter_living_room_active_mode").state == "Closed"
    assert hass.states.get("number.shutter_living_room_open_position") is not None
    assert hass.states.get("number.shutter_living_room_closed_position") is not None


async def test_a_preset_without_a_preset_mode_waits_for_one(
    hass: HomeAssistant,
) -> None:
    """A preset mode is offered, not required."""
    hubs = await async_setup_hubs(hass, preset_modes=[make_preset_mode()], presets=[])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": "Shutter", CONF_PRESET_MODE: "__none__"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: [{"name": "Position", "type": "number"}]}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"default": 50}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(hubs.entry("presets").subentries.values()))
    assert CONF_PRESET_MODE not in subentry.data
    # It has no modes, so it has no editors and no active mode either - but it
    # exists, and assigning a preset mode brings all of that with it.
    assert hass.states.get("sensor.shutter_active_mode").state == "unknown"
    assert hass.states.get("number.shutter_home_position") is None


async def test_assigning_another_preset_mode_keeps_everything(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """A preset follows its preset mode by reference, so this is a field.

    It used to be a move between two config entries, with the subentry
    removed here and re-created there; now nothing about the preset changes
    but the id it points at.
    """
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(),
            make_preset_mode(
                title="Window State",
                modes=[
                    {"key": "closed", "name": "Closed"},
                    {"key": "night", "name": "Night"},
                ],
                subentry_id="2" * 32,
            ),
        ],
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    hubs.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    before = entity_registry.async_get("number.heating_night_brightness")
    entity_registry.async_update_entity(before.entity_id, name="My name")
    assert hass.states.get("number.heating_night_brightness").state == "15.0"

    result = await _reconfigure_preset(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_preset_mode"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRESET_MODE: "2" * 32}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert subentry.data[CONF_PRESET_MODE] == "2" * 32

    # It follows the window state preset mode now.
    assert hass.states.get("sensor.heating_active_mode").state == "Closed"
    # The value of the "night" mode survived, and so did the registry entry.
    assert hass.states.get("number.heating_night_brightness").state == "15.0"
    after = entity_registry.async_get("number.heating_night_brightness")
    assert after.id == before.id
    assert after.name == "My name"
    # "away" belongs to the old preset mode and is gone.
    assert hass.states.get("number.heating_away_brightness") is None


async def test_a_preset_left_without_a_preset_mode_keeps_its_editors(
    hass: HomeAssistant,
) -> None:
    """Clearing the preset mode keeps the modes it had, as a snapshot.

    The editors are one entity per mode and parameter; an entity that stops
    being expected is removed from the registry with its name, its area and
    its icon, so the modes have to outlive the assignment.
    """
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating", [BRIGHTNESS])],
    )
    hubs.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    result = await _reconfigure_preset(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_preset_mode"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PRESET_MODE: "__none__"}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert CONF_PRESET_MODE not in subentry.data
    assert [item["key"] for item in subentry.data[CONF_MODES]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]
    assert hass.states.get("number.heating_night_brightness").state == "15.0"
    # Nothing decides the active mode any more.
    assert hass.states.get("sensor.heating_active_mode").state == "unknown"


async def _manage_parameters(
    hass: HomeAssistant, hubs: Hubs, subentry_id: str = PRESET_ID
) -> dict:
    """Open the parameter list of a preset."""
    result = await _reconfigure_preset(hass, hubs, subentry_id)
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )


def _preset_id(hubs: Hubs) -> str:
    """Return the subentry id of the single preset."""
    return next(iter(hubs.entry("presets").subentries))


async def test_preset_add_and_remove_parameter(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """One list handles adding and deleting parameters."""
    preset_id = _preset_id(motion)

    result = await _manage_parameters(hass, motion, preset_id)
    assert result["step_id"] == "manage_parameters"

    # The list is seeded with the current parameters, keys included.
    schema = result["data_schema"].schema
    key = next(item for item in schema if str(item) == CONF_PARAMETERS)
    seeded = key.description["suggested_value"]
    assert [row["key"] for row in seeded] == [
        "brightness",
        "color_temperature",
        "off_delay",
    ]

    rows = [dict(row) for row in seeded if row["key"] != "off_delay"]
    rows.append({"name": "Active", "type": "boolean"})
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: rows}
    )
    # Only the new row needs its details.
    assert result["step_id"] == "parameter_details"
    assert result["description_placeholders"]["parameter"] == "Active"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"default": True}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert (
        hass.states.get("binary_sensor.motion_sensor_living_room_active").state == "on"
    )
    assert hass.states.get("sensor.motion_sensor_living_room_off_delay") is None
    assert hass.states.get("number.motion_sensor_living_room_night_off_delay") is None


async def test_renaming_a_parameter_keeps_its_values(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A renamed row keeps its key, and therefore its stored values."""
    coordinator = next(iter(motion.runtime.presets.values()))
    coordinator.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    result = await _manage_parameters(hass, motion, _preset_id(motion))
    schema = result["data_schema"].schema
    key = next(item for item in schema if str(item) == CONF_PARAMETERS)
    rows = [dict(row) for row in key.description["suggested_value"]]
    rows[0]["name"] = "Dim level"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: rows}
    )
    # Nothing was retyped, so the flow is done without a detail step.
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert (
        hass.states.get("number.motion_sensor_living_room_night_brightness").state
        == "15.0"
    )


async def test_changing_the_type_drops_the_stored_values(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The old values of a retyped parameter no longer fit and are dropped."""
    coordinator = next(iter(motion.runtime.presets.values()))
    coordinator.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    result = await _manage_parameters(hass, motion, _preset_id(motion))
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                {"key": "brightness", "name": "Brightness", "type": "select"}
            ]
        },
    )
    assert result["step_id"] == "parameter_details"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"options": ["low", "high"], "default": "low"}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    # The editor is a select now, and the stored 15 is gone.
    assert async_get_store(hass).get_value(PRESET_ID, "night", "brightness") is None
    assert (
        hass.states.get("select.motion_sensor_living_room_night_brightness").state
        == "low"
    )


async def test_two_rows_with_the_same_parameter_key_are_refused(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Two parameters with one key would share their values and unique ids."""
    result = await _manage_parameters(hass, motion, PRESET_ID)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                {"key": "brightness", "name": "Brightness", "type": "number"},
                {"key": "brightness", "name": "Copy", "type": "number"},
            ]
        },
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_PARAMETERS: "duplicate_parameter_key"}


async def test_a_new_parameter_never_takes_the_key_of_a_renamed_one(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Same rule as for the modes, in the parameter list."""
    result = await _manage_parameters(hass, motion, PRESET_ID)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                # New row named like the parameter below it, which is renamed.
                {"name": "Brightness", "type": "boolean"},
                {"key": "brightness", "name": "Dim level", "type": "number"},
            ]
        },
    )
    # The new row needs its type specific details; the number keeps its own.
    assert result["step_id"] == "parameter_details"
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = motion.entry("presets").subentries[PRESET_ID]
    keys = [row["key"] for row in subentry.data[CONF_PARAMETERS]]
    assert len(keys) == len(set(keys))
    assert keys == ["brightness_2", "brightness"]


async def test_edit_details_of_an_existing_parameter(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The field below the list opens the details of one parameter."""
    result = await _manage_parameters(hass, motion, _preset_id(motion))
    schema = result["data_schema"].schema
    key = next(item for item in schema if str(item) == CONF_PARAMETERS)
    rows = [dict(row) for row in key.description["suggested_value"]]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: rows, "parameter": "brightness"}
    )
    assert result["step_id"] == "parameter_details"
    assert result["description_placeholders"]["parameter"] == "Brightness"
    # The form is seeded with the current details.
    suggested = {
        str(item): (item.description or {}).get("suggested_value")
        for item in result["data_schema"].schema
    }
    assert suggested["maximum"] == 100

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"minimum": 0, "maximum": 255, "step": 1, "unit": "%"}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = motion.entry("presets").subentries[_preset_id(motion)]
    assert subentry.data[CONF_PARAMETERS][0]["maximum"] == 255


async def test_an_empty_parameter_list_is_refused(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A preset without parameters would have nothing to publish."""
    result = await _manage_parameters(hass, motion, _preset_id(motion))
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: []}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_PARAMETERS: "no_parameters"}


async def test_parameter_details_defaults(hass: HomeAssistant) -> None:
    """Leaving the range empty applies the defaults of the type."""
    hubs = await async_setup_one(hass, presets=[])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Kitchen Light", CONF_PRESET_MODE: PRESET_MODE_ID},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: [{"name": "Brightness", "type": "number"}]}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"unit": "%"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY

    parameter = result["data"][CONF_PARAMETERS][0]
    assert parameter["minimum"] == 0
    assert parameter["maximum"] == 100
    assert parameter["step"] == 1
    assert parameter["display_mode"] == "box"
    assert parameter["unit"] == "%"


async def test_invalid_parameter_range(hass: HomeAssistant) -> None:
    """An invalid range is refused."""
    hubs = await async_setup_one(hass, presets=[])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Test"},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_PARAMETERS: [{"name": "Value", "type": "number"}]}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"minimum": 100, "maximum": 10}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "invalid_range"}


async def test_unit_has_to_fit_the_device_class(hass: HomeAssistant) -> None:
    """A unit the device class does not accept is refused."""
    hubs = await async_setup_one(hass, presets=[])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Test"},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_PARAMETERS: [{"name": "Temperature", "type": "number"}]},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"minimum": 0, "maximum": 100, "device_class": "temperature"}
    )
    assert result["errors"] == {"base": "invalid_unit"}
    # The message names the units that would work.
    assert result["description_placeholders"]["units"] == "K, \u00b0C, \u00b0F"
    # What was entered survives the error instead of being reset.
    schema = result["data_schema"].schema
    suggested = {
        str(key): (key.description or {}).get("suggested_value") for key in schema
    }
    assert suggested["device_class"] == "temperature"
    assert suggested["maximum"] == 100

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"device_class": "temperature", "unit": "\u00b0C"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_create_a_time_parameter(hass: HomeAssistant) -> None:
    """A time parameter needs no further configuration."""
    hubs = await async_setup_one(hass, presets=[])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Alarm Clock"},
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {CONF_PARAMETERS: [{"name": "Wake up", "type": "time", "icon": "mdi:alarm"}]},
    )
    # The icon is a field of the list row, so only the default value is left.
    assert set(result["data_schema"].schema) == {"default"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"default": "06:30:00"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_PARAMETERS][0] == {
        "key": "wake_up",
        "name": "Wake up",
        "type": "time",
        "default": "06:30:00",
        "icon": "mdi:alarm",
    }


# Applying a change without a reload --------------------------------------------


async def test_a_rename_does_not_reload_the_hub(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A reload takes every entity of the hub down; a rename must not.

    With one preset that is invisible. With twenty it means every value in the
    house goes unavailable for a moment because one of them was renamed.
    """
    with patch.object(
        hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
    ) as reload:
        result = await _reconfigure_preset(hass, motion)
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"next_step_id": "rename"}
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"name": "Motion Sensor Hall"}
        )
        assert result["type"] is FlowResultType.ABORT
        await hass.async_block_till_done()

        assert reload.call_args_list == []

    # The device carries the new name, and the entity ids stay as they were.
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, PRESET_ID)})
    assert device.name == "Motion Sensor Hall"
    assert hass.states.get("number.motion_sensor_living_room_night_brightness")


async def test_a_new_parameter_does_reload_the_hub(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Adding an entity is the one thing only a fresh setup can do."""
    with patch.object(
        hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
    ) as reload:
        result = await _manage_parameters(hass, motion)
        schema = result["data_schema"].schema
        key = next(item for item in schema if str(item) == CONF_PARAMETERS)
        rows = [dict(row) for row in key.description["suggested_value"]]
        rows.append({"name": "Active", "type": "boolean"})
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {CONF_PARAMETERS: rows}
        )
        result = await hass.config_entries.subentries.async_configure(
            result["flow_id"], {"default": True}
        )
        await hass.async_block_till_done()

        assert reload.call_count == 1

    assert hass.states.get("binary_sensor.motion_sensor_living_room_active")


async def test_changed_conditions_take_effect_when_they_are_saved(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The source is rebuilt in place, so nothing has to change first."""
    hass.states.async_set("binary_sensor.window", "on")

    result = await _manage_modes(hass, motion)
    # "Home" is only valid while the window is closed; the modes below it
    # carry no conditions and therefore match anything.
    modes = _modes_of(motion)
    modes[0] = {
        **modes[0],
        CONF_CONDITIONS: [
            {
                "condition": "state",
                "entity_id": "binary_sensor.window",
                "state": "off",
            }
        ],
    }
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_MODES: modes}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    # No state change of the window was needed to get there.
    assert hass.states.get("sensor.house_mode_mode").state == "Away"


# One rename, everywhere the same ----------------------------------------------


@pytest.mark.parametrize(
    ("kind", "subentry_type", "subentry_id", "name"),
    [
        ("preset_modes", SUBENTRY_TYPE_PRESET_MODE, PRESET_MODE_ID, "Window State"),
        ("presets", SUBENTRY_TYPE_PRESET, PRESET_ID, "Motion Sensor Hall"),
        ("blueprints", SUBENTRY_TYPE_BLUEPRINT, BLUEPRINT_ID, "Cooling"),
    ],
)
async def test_every_object_is_renamed_the_same_way(
    hass: HomeAssistant,
    kind: str,
    subentry_type: str,
    subentry_id: str,
    name: str,
) -> None:
    """Renaming sits in the same place in every menu, and it is its own step.

    It used to be a field on the settings of the one kind that had settings,
    and the first step of the blueprint editor for another - so the way to
    rename something depended on what it was.
    """
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        blueprints=[make_blueprint()],
        presets=[make_preset("Motion Sensor Living Room", [BRIGHTNESS])],
    )

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry(kind).entry_id, subentry_type),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": subentry_id,
        },
    )
    assert result["type"] is FlowResultType.MENU
    # Always the second entry: what the object is comes first, its name second.
    assert result["menu_options"][1] == "rename"

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "rename"}
    )
    assert result["step_id"] == "rename"
    assert set(result["data_schema"].schema) == {"name"}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"name": name}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert hubs.entry(kind).subentries[subentry_id].title == name


async def test_the_blueprint_menu_opens_its_parameters_directly(
    hass: HomeAssistant,
) -> None:
    """The first entry is the parameter list, not a name form in front of it."""
    hubs = await async_setup_hubs(hass, blueprints=[make_blueprint()])

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("blueprints").entry_id, SUBENTRY_TYPE_BLUEPRINT),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": BLUEPRINT_ID,
        },
    )
    assert result["menu_options"] == [
        "manage_parameters",
        "rename",
        "assign_presets",
        "duplicate",
    ]

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )
    assert result["step_id"] == "manage_parameters"

    # And saving from there keeps the name it has.
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                {
                    "key": "target_temperature",
                    "name": "Target temperature",
                    "type": "number",
                }
            ]
        },
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    assert hubs.entry("blueprints").subentries[BLUEPRINT_ID].title == "Heating"
