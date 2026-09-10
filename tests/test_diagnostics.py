"""Tests for the diagnostics download."""

from __future__ import annotations

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from custom_components.preset_manager.const import HUB_PRESET_MODES
from custom_components.preset_manager.diagnostics import (
    REDACTED,
    async_get_config_entry_diagnostics,
)

from .conftest import (
    BLUEPRINT_ID,
    BRIGHTNESS,
    PRESET_ID,
    PRESET_MODE_ID,
    TARGET_TEMPERATURE,
    Hubs,
    async_setup_one,
    make_blueprint,
    make_hub,
    make_preset,
    make_preset_mode,
)


async def _preset_report(hass: HomeAssistant, hubs: Hubs) -> dict:
    """Return the report of the only preset."""
    report = await async_get_config_entry_diagnostics(hass, hubs.entry("presets"))
    return next(iter(report["presets"].values()))


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
    motion: Hubs,
) -> None:
    """The report has to come out of Home Assistant's own endpoint.

    Calling the function directly proves nothing about whether Home Assistant
    finds it, nor whether what it returns survives being serialised to JSON.
    """
    assert await async_setup_component(hass, "diagnostics", {})
    await hass.async_block_till_done()

    report = await get_diagnostics_for_config_entry(
        hass, hass_client, motion.entry("preset_modes")
    )

    assert report["entry"]["hub"] == "preset_modes"
    assert report["entry"]["state"] == "loaded"
    preset_mode = report["preset_modes"][PRESET_MODE_ID]
    assert [mode["key"] for mode in preset_mode["modes"]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]
    assert preset_mode["source_kind"] == "StaticSource"
    assert preset_mode["active_mode"] == "home"
    assert preset_mode["presets"] == ["Motion Sensor Living Room"]

    presets = await get_diagnostics_for_config_entry(
        hass, hass_client, motion.entry("presets")
    )
    assert len(presets["presets"]) == 1


async def test_the_report_carries_the_values_and_the_resolution(
    hass: HomeAssistant,
) -> None:
    """Everything needed to explain an "unknown" has to be in there."""
    hubs = await async_setup_one(hass, presets=[make_preset("Lamp", [BRIGHTNESS])])

    hubs.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    preset = await _preset_report(hass, hubs)

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
    hubs = await async_setup_one(
        hass, presets=[make_preset("Lamp", [SECRET, BRIGHTNESS])]
    )

    coordinator = hubs.preset
    coordinator.async_set_value("home", "token", "s3cret")
    coordinator.async_set_value("home", "brightness", 40)
    await hass.async_block_till_done()

    report = await async_get_config_entry_diagnostics(hass, hubs.entry("presets"))
    preset = report["presets"][PRESET_ID]
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
    entry = make_hub(HUB_PRESET_MODES, [make_preset_mode()], version=99)
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.MIGRATION_ERROR

    report = await async_get_config_entry_diagnostics(hass, entry)

    assert report["entry"]["version"] == 99
    assert report["entry"]["state"] == "migration_error"
    # The stored data is what a migration problem would show.
    stored = report["stored_objects"][0]
    assert [mode["key"] for mode in stored["data"]["modes"]] == [
        "home",
        "away",
        "night",
        "window_open",
    ]


async def test_a_blueprint_reports_who_follows_it(hass: HomeAssistant) -> None:
    """A blueprint has no runtime, so it reports its list and its followers."""
    hubs = await async_setup_one(
        hass,
        blueprints=[make_blueprint()],
        presets=[make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID)],
    )

    report = await async_get_config_entry_diagnostics(hass, hubs.entry("blueprints"))
    assert report["entry"]["hub"] == "blueprints"
    blueprint = report["blueprints"][0]
    assert [item["key"] for item in blueprint["parameters"]] == [
        TARGET_TEMPERATURE["key"]
    ]
    assert blueprint["followed_by"] == ["Heating Bath"]

    # And the bound preset says where its parameters come from.
    preset = await _preset_report(hass, hubs)
    assert preset["blueprint"]["exists"] is True
    assert preset["blueprint"]["title"] == "Heating"


async def test_a_missing_blueprint_is_named_as_missing(hass: HomeAssistant) -> None:
    """A backup restored without the blueprint leaves the preset empty."""
    hubs = await async_setup_one(
        hass, presets=[make_preset("Heating Bath", [], blueprint="c" * 32)]
    )

    preset = await _preset_report(hass, hubs)
    assert preset["blueprint"] == {
        "subentry_id": "c" * 32,
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
    hubs = await async_setup_one(hass, source_entity=source_entity)

    report = await async_get_config_entry_diagnostics(hass, hubs.entry("preset_modes"))
    preset_mode = report["preset_modes"][PRESET_MODE_ID]
    assert preset_mode["source_kind"] == "EntitySource"
    assert preset_mode["source_entity"] == source_entity
    assert preset_mode["source_entity_state"] == state
    assert preset_mode["active_mode"] == active_mode
