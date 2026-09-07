"""Tests for the diagnostics download."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.preset_manager.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)

from .conftest import (
    BRIGHTNESS,
    TARGET_TEMPERATURE,
    make_blueprint,
    make_entry,
    make_preset,
)

SECRET = {
    "key": "token",
    "name": "Token",
    "type": "text",
    "display_mode": "password",
    "default": "hunter2",
}


async def test_the_download_works_end_to_end(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    motion_entry: MockConfigEntry,
) -> None:
    """The report has to come out of Home Assistant's own endpoint.

    Calling the function directly proves nothing about whether Home Assistant
    finds it, nor whether what it returns survives being serialised to JSON.
    """
    assert await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()

    report = await get_diagnostics_for_config_entry(hass, hass_client, motion_entry)

    assert report["entry"]["entry_type"] == "preset_mode"
    assert report["entry"]["state"] == "loaded"
    assert [mode["key"] for mode in report["preset_mode"]["modes"]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]
    assert report["preset_mode"]["source_kind"] == "ManualSource"
    assert report["preset_mode"]["active_mode"] == "home"
    assert len(report["presets"]) == 1


async def test_the_report_carries_the_values_and_the_resolution(
    hass: HomeAssistant,
) -> None:
    """Everything needed to explain an "unknown" has to be in there."""
    entry = make_entry(presets=[make_preset("Lamp", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    next(iter(entry.runtime_data.presets.values())).async_set_value(
        "night", "brightness", 15
    )
    await hass.async_block_till_done()

    report = await async_get_config_entry_diagnostics(hass, entry)
    preset = report["presets"][0]

    assert preset["name"] == "Lamp"
    assert [item["key"] for item in preset["parameters"]] == ["brightness"]
    # "Home" is active and has no value, which is why the sensor is unknown.
    assert preset["state"]["mode_key"] == "home"
    assert preset["state"]["unset_parameters"] == ["brightness"]
    # The value that *is* stored, and the mode it belongs to.
    assert preset["stored_values"]["night"] == {"brightness": 15.0}
    assert preset["stored_values"]["home"] == {}


async def test_a_password_parameter_is_redacted(hass: HomeAssistant) -> None:
    """A value the user chose to hide must not be handed out in a report."""
    entry = make_entry(presets=[make_preset("Lamp", [SECRET, BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = next(iter(entry.runtime_data.presets.values()))
    coordinator.async_set_value("home", "token", "s3cret")
    coordinator.async_set_value("home", "brightness", 40)
    await hass.async_block_till_done()

    report = await async_get_config_entry_diagnostics(hass, entry)
    preset = report["presets"][0]
    token = next(item for item in preset["parameters"] if item["key"] == "token")

    assert token["default"] == REDACTED
    assert preset["state"]["values"]["token"] == REDACTED
    assert preset["stored_values"]["home"]["token"] == REDACTED
    # The definition itself stays, and other parameters are untouched.
    assert token["display_mode"] == "password"
    assert preset["stored_values"]["home"]["brightness"] == 40.0

    # Nowhere in the whole report, not just in the places checked above.
    assert "s3cret" not in str(report)
    assert "hunter2" not in str(report)


async def test_an_entry_that_did_not_load_still_reports(hass: HomeAssistant) -> None:
    """A failed setup is when a report is needed most.

    Home Assistant offers the download whatever the state of the entry, and
    there is no runtime to read then - reaching for one would raise.
    """
    entry = make_entry(version=99)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.MIGRATION_ERROR

    report = await async_get_config_entry_diagnostics(hass, entry)

    assert report["entry"]["version"] == 99
    assert report["entry"]["state"] == "migration_error"
    # The stored data is what a migration problem would show.
    assert [mode["key"] for mode in report["stored_data"]["modes"]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]


async def test_a_blueprint_reports_who_follows_it(hass: HomeAssistant) -> None:
    """A blueprint has no runtime, so it reports its list and its followers."""
    blueprint = make_blueprint()
    blueprint.add_to_hass(hass)
    assert await hass.config_entries.async_setup(blueprint.entry_id)

    entry = make_entry(
        presets=[make_preset("Heating Bath", [], blueprint=blueprint.entry_id)]
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    report = await async_get_config_entry_diagnostics(hass, blueprint)
    assert report["entry"]["entry_type"] == "blueprint"
    assert [item["key"] for item in report["parameters"]] == [TARGET_TEMPERATURE["key"]]
    assert report["bound_presets"] == [
        {"preset_mode": "House Mode", "preset": "Heating Bath"}
    ]

    # And the bound preset says where its parameters come from.
    preset = (await async_get_config_entry_diagnostics(hass, entry))["presets"][0]
    assert preset["blueprint"]["exists"] is True
    assert preset["blueprint"]["title"] == "Heating"


async def test_a_missing_blueprint_is_named_as_missing(hass: HomeAssistant) -> None:
    """A backup restored without the blueprint leaves the preset empty."""
    entry = make_entry(presets=[make_preset("Heating Bath", [], blueprint="c" * 32)])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    preset = (await async_get_config_entry_diagnostics(hass, entry))["presets"][0]
    assert preset["blueprint"] == {
        "entry_id": "c" * 32,
        "exists": False,
        "title": None,
    }
    assert preset["parameters"] == []


@pytest.mark.parametrize(
    ("state", "active_mode"),
    [
        # A state that names a mode, and one that names none - the second is
        # the case a user opens an issue about, and the report has to show
        # both the state and that nothing resolved from it.
        ("Night", "night"),
        ("Party", None),
    ],
)
async def test_an_external_preset_mode_reports_the_state_it_follows(
    hass: HomeAssistant, state: str, active_mode: str | None
) -> None:
    """The state against the mode names is the whole question there."""
    source_entity = "input_select.house"
    hass.states.async_set(source_entity, state)
    entry = make_entry(source_entity=source_entity)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    preset_mode = (await async_get_config_entry_diagnostics(hass, entry))["preset_mode"]
    assert preset_mode["source_kind"] == "EntitySource"
    assert preset_mode["source_entity"] == source_entity
    assert preset_mode["source_entity_state"] == state
    assert preset_mode["active_mode"] == active_mode
