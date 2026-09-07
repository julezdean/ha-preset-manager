"""Tests for the setup of the integration."""

from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager import (
    PLATFORMS,
    _async_remove_stale_entities,
)
from custom_components.preset_manager.const import (
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_VERSION,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
    STORAGE_KEY,
    STORAGE_VERSION,
    SUBENTRY_TYPE_PRESET,
)
from custom_components.preset_manager.entity import async_expected_preset_ids
from custom_components.preset_manager.sources import ConditionSource
from custom_components.preset_manager.store import _ValueFileStore, async_get_store

from .conftest import (
    BRIGHTNESS,
    MODES,
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_setup_hubs,
    make_hub,
    make_preset,
    make_preset_mode,
)


async def test_setup_creates_entities(hass: HomeAssistant, motion: Hubs) -> None:
    """The preset mode and preset entities are created."""
    assert hass.states.get("select.house_mode_active_mode") is not None
    assert hass.states.get("sensor.house_mode_mode") is not None
    assert hass.states.get("sensor.motion_sensor_living_room_active_mode") is not None
    assert hass.states.get("sensor.motion_sensor_living_room_brightness") is not None


async def test_the_two_devices_stand_side_by_side(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A preset is not a part of its preset mode.

    It follows one, outlives its deletion and may have none at all, so it
    carries no ``via_device``: the two hubs are set up in either order, and a
    device pointing at one that is not there yet is a warning today and an
    error in a coming Home Assistant version.
    """
    registry = dr.async_get(hass)
    preset_mode = registry.async_get_device(identifiers={(DOMAIN, PRESET_MODE_ID)})
    preset = registry.async_get_device(identifiers={(DOMAIN, PRESET_ID)})
    assert preset_mode is not None
    assert preset is not None
    assert preset.via_device_id is None
    assert preset.primary_config_entry == motion.entry("presets").entry_id
    assert preset_mode.primary_config_entry == motion.entry("preset_modes").entry_id


async def test_no_entity_is_stale_right_after_a_setup(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """The cleanup and the platforms have to agree on every unique id.

    They did not: the cleanup expected "<subentry>_mode" for the active mode
    sensor of a preset while the platform registered "<subentry>_active_mode",
    so that entity was removed and restored on every single setup.
    """
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Lamp", [BRIGHTNESS])],
    )
    entry = hubs.entry("presets")

    def unique_ids() -> set[str]:
        return {
            item.unique_id
            for item in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
        }

    before = unique_ids()
    assert before  # the test would pass on an empty registry otherwise
    _async_remove_stale_entities(hass, entry, async_expected_preset_ids(hubs.runtime))
    assert unique_ids() == before


async def test_the_first_object_creates_its_hub(hass: HomeAssistant) -> None:
    """The user adds an object; the hub of that kind appears with it."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "user"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "preset_mode"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "House Mode", "modes": ["Home", "Night"]}
    )
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert [entry.unique_id for entry in entries] == [HUB_PRESET_MODES]
    subentry = next(iter(entries[0].subentries.values()))
    assert subentry.title == "House Mode"
    assert [item["key"] for item in subentry.data[CONF_MODES]] == ["home", "night"]


# Migration --------------------------------------------------------------------


def _legacy_preset_mode() -> MockConfigEntry:
    """Build a 0.1.0 preset mode entry with one preset in it."""
    preset: dict[str, Any] = {
        "data": {CONF_PARAMETERS: [BRIGHTNESS]},
        "subentry_id": PRESET_ID,
        "subentry_type": SUBENTRY_TYPE_PRESET,
        "title": "Motion Sensor Living Room",
        "unique_id": None,
    }
    return MockConfigEntry(
        domain=DOMAIN,
        title="House Mode",
        entry_id=PRESET_MODE_ID,
        data={CONF_MODES: [dict(item) for item in MODES]},
        version=1,
        minor_version=1,
        subentries_data=[ConfigSubentryData(**preset)],
    )


async def test_migration_moves_the_objects_into_the_hubs(
    hass: HomeAssistant,
) -> None:
    """A 0.1.0 entry is dissolved into subentries, and containment becomes a
    reference."""
    legacy = _legacy_preset_mode()
    legacy.add_to_hass(hass)

    await hass.config_entries.async_setup(legacy.entry_id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    entries = {
        entry.unique_id: entry for entry in hass.config_entries.async_entries(DOMAIN)
    }
    # The legacy entry is gone, and nothing else was created.
    assert set(entries) == {HUB_PRESET_MODES, HUB_PRESETS}
    # Every object keeps the id it had, which is what the entity unique ids,
    # the device identifiers and the value store are built from.
    assert PRESET_MODE_ID in entries[HUB_PRESET_MODES].subentries
    preset = entries[HUB_PRESETS].subentries[PRESET_ID]
    assert preset.data[CONF_PRESET_MODE] == PRESET_MODE_ID
    assert hass.states.get("select.house_mode_active_mode") is not None


async def test_migration_keeps_what_the_user_configured(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Entities survive the migration with their id and their settings.

    They are not re-created: the platforms register the same unique ids, and
    Home Assistant moves the existing registry entry to the hub that provides
    it now. Getting the order wrong here would strip every entity of its name,
    its area, its icon and its history.
    """
    legacy = _legacy_preset_mode()
    legacy.add_to_hass(hass)

    editor = entity_registry.async_get_or_create(
        "number",
        DOMAIN,
        f"{PRESET_ID}_cfg_home-brightness",
        config_entry=legacy,
        config_subentry_id=PRESET_ID,
        suggested_object_id="motion_sensor_living_room_home_brightness",
    )
    entity_registry.async_update_entity(editor.entity_id, name="Cosy")

    await hass.config_entries.async_setup(legacy.entry_id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    kept = entity_registry.async_get(editor.entity_id)
    assert kept is not None
    assert kept.name == "Cosy"
    presets = next(
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if entry.unique_id == HUB_PRESETS
    )
    assert kept.config_entry_id == presets.entry_id
    assert kept.config_subentry_id == PRESET_ID


async def test_migration_moves_a_blueprint_too(hass: HomeAssistant) -> None:
    """A blueprint was an entry of its own and becomes a subentry."""
    legacy = MockConfigEntry(
        domain=DOMAIN,
        title="Heating",
        data={"entry_type": "blueprint", CONF_PARAMETERS: [BRIGHTNESS]},
        version=1,
        minor_version=1,
    )
    legacy.add_to_hass(hass)

    await hass.config_entries.async_setup(legacy.entry_id)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    entries = hass.config_entries.async_entries(DOMAIN)
    assert [entry.unique_id for entry in entries] == [HUB_BLUEPRINTS]
    subentry = entries[0].subentries[legacy.entry_id]
    assert subentry.title == "Heating"
    assert subentry.data[CONF_PARAMETERS] == [BRIGHTNESS]


# Deleting ---------------------------------------------------------------------


async def test_removing_the_presets_hub_drops_the_stored_values(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Deleting every preset deletes what was stored for them."""
    motion.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    store = async_get_store(hass)
    assert store.get_value(PRESET_ID, "night", "brightness") == 15.0

    assert await hass.config_entries.async_remove(motion.entry("presets").entry_id)
    await hass.async_block_till_done()

    assert store.get_value(PRESET_ID, "night", "brightness") is None


async def test_removing_the_preset_modes_hub_keeps_the_presets(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """The presets outlive their dimension, values and all."""
    motion.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_remove(motion.entry("preset_modes").entry_id)
    await hass.async_block_till_done()

    store = async_get_store(hass)
    assert store.get_value(PRESET_ID, "night", "brightness") == 15.0
    assert store.active_mode(PRESET_MODE_ID) is None
    preset = motion.entry("presets").subentries[PRESET_ID]
    assert CONF_PRESET_MODE not in preset.data
    assert [item["key"] for item in preset.data[CONF_MODES]] == [
        item["key"] for item in MODES
    ]


# Versions ---------------------------------------------------------------------


async def test_current_entry_needs_no_migration(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """An entry written by this version sets up without being touched."""
    entry = motion.entry("preset_modes")
    assert entry.version == ENTRY_VERSION
    assert entry.minor_version == ENTRY_MINOR_VERSION
    assert entry.state is ConfigEntryState.LOADED


async def test_entry_from_a_newer_version_is_refused(hass: HomeAssistant) -> None:
    """A downgrade must fail loudly instead of guessing at unknown keys."""
    entry = make_hub(HUB_PRESET_MODES, [make_preset_mode()], version=ENTRY_VERSION + 1)
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.MIGRATION_ERROR


async def test_store_reads_the_current_format(hass: HomeAssistant) -> None:
    """The migration hook passes data of the current version through."""
    store = _ValueFileStore(
        hass, STORAGE_VERSION, "test_preset_manager.values", atomic_writes=True
    )
    data = {"active_modes": {"a": "night"}, "automatic": {}, "values": {}}
    assert await store._async_migrate_func(STORAGE_VERSION, 1, data) == data


async def test_store_refuses_a_newer_file(hass: HomeAssistant) -> None:
    """A file from a newer version must not be read as if it fitted."""
    store = _ValueFileStore(
        hass, STORAGE_VERSION, "test_preset_manager.values", atomic_writes=True
    )
    with pytest.raises(ValueError, match="newer version"):
        await store._async_migrate_func(STORAGE_VERSION + 1, 1, {})


# Unload and reload ------------------------------------------------------------


def _state(entity: str, state: str) -> list[dict]:
    """A single state condition."""
    return [{"condition": "state", "entity_id": entity, "state": state}]


async def _async_following(hass: HomeAssistant, entity: str) -> Hubs:
    """A preset mode whose every mode has a condition on one entity."""
    return await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(
                conditions={
                    key: _state(entity, name)
                    for key, name in (
                        ("home", "Home"),
                        ("away", "Away"),
                        ("night", "Night"),
                        ("window_open", "Window open"),
                    )
                }
            )
        ],
        presets=[make_preset("Lamp", [BRIGHTNESS])],
    )


async def test_unload_flushes_the_pending_values(
    hass: HomeAssistant, hass_storage: dict
) -> None:
    """A value must reach the disk on unload, not two seconds later.

    Writes are debounced by SAVE_DELAY so a slider does not hit the disk on
    every pixel; the flush on unload is what turns that into "a restart never
    loses values". Values are the one thing a user cannot reproduce.
    """
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Lamp", [BRIGHTNESS])],
    )

    hubs.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()
    # Still only scheduled - nothing has been written yet.
    assert STORAGE_KEY not in hass_storage

    assert await hass.config_entries.async_unload(hubs.entry("presets").entry_id)
    await hass.async_block_till_done()

    stored = hass_storage[STORAGE_KEY]["data"]
    assert stored["values"][PRESET_ID]["night"]["brightness"] == 15.0


async def test_unload_stops_evaluating_the_conditions(hass: HomeAssistant) -> None:
    """Nothing may keep listening once the hub is gone.

    A leaked subscription is invisible from the states - it would recompute
    against a runtime that is no longer set up - so it is counted instead.
    """
    hass.states.async_set("sensor.mode_source", "Home")
    hubs = await _async_following(hass, "sensor.mode_source")

    evaluations = 0
    original = ConditionSource._evaluate

    def counting(self: ConditionSource) -> None:
        nonlocal evaluations
        evaluations += 1
        original(self)

    with patch.object(ConditionSource, "_evaluate", counting):
        hass.states.async_set("sensor.mode_source", "Night")
        await hass.async_block_till_done()
        assert evaluations == 1
        assert hass.states.get("sensor.house_mode_mode").state == "Night"

        assert await hass.config_entries.async_unload(
            hubs.entry("preset_modes").entry_id
        )
        await hass.async_block_till_done()

        evaluations = 0
        hass.states.async_set("sensor.mode_source", "Away")
        await hass.async_block_till_done()
        assert evaluations == 0


async def test_reload_does_not_double_the_subscriptions(hass: HomeAssistant) -> None:
    """A reload has to replace the subscriptions, not add to them.

    A second listener on the same entity would be invisible: it recomputes the
    same mode and changes no state. It would only grow, one per reload.
    """
    hass.states.async_set("sensor.mode_source", "Home")
    hubs = await _async_following(hass, "sensor.mode_source")

    await hass.config_entries.async_reload(hubs.entry("preset_modes").entry_id)
    await hass.async_block_till_done()

    evaluations = 0
    original = ConditionSource._evaluate

    def counting(self: ConditionSource) -> None:
        nonlocal evaluations
        evaluations += 1
        original(self)

    with patch.object(ConditionSource, "_evaluate", counting):
        hass.states.async_set("sensor.mode_source", "Night")
        await hass.async_block_till_done()

    assert evaluations == 1
    assert hass.states.get("sensor.house_mode_mode").state == "Night"


async def test_a_failed_platform_unload_still_flushes_and_stops(
    hass: HomeAssistant, hass_storage: dict
) -> None:
    """A failed unload must not leave the hub half alive.

    Home Assistant marks such an entry as failed and never retries it, so a
    mode source left running would keep evaluating against a torn down
    runtime, and pending values would never reach the disk.
    """
    hass.states.async_set("sensor.mode_source", "Home")
    hubs = await _async_following(hass, "sensor.mode_source")

    hubs.preset.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()
    assert STORAGE_KEY not in hass_storage

    evaluations = 0
    original = ConditionSource._evaluate

    def counting(self: ConditionSource) -> None:
        nonlocal evaluations
        evaluations += 1
        original(self)

    with (
        patch.object(
            hass.config_entries,
            "async_unload_platforms",
            AsyncMock(return_value=False),
        ),
        patch.object(ConditionSource, "_evaluate", counting),
    ):
        await hass.config_entries.async_unload(hubs.entry("preset_modes").entry_id)
        await hass.async_block_till_done()

        # The failure is still reported, ...
        assert hubs.entry("preset_modes").state is ConfigEntryState.FAILED_UNLOAD
        # ... but nothing is left listening.
        hass.states.async_set("sensor.mode_source", "Night")
        await hass.async_block_till_done()
        assert evaluations == 0

    await hass.config_entries.async_unload(hubs.entry("presets").entry_id)
    await hass.async_block_till_done()

    # And the pending value reached the disk anyway.
    stored = hass_storage[STORAGE_KEY]["data"]
    assert stored["values"][PRESET_ID]["night"]["brightness"] == 15.0


def test_every_platform_declares_parallel_updates() -> None:
    """Left undeclared, the default is derived rather than stated.

    Home Assistant falls back to 1 - serialised - for a platform whose
    entities have a synchronous ``update`` method. None of these do today, so
    the effective value is already 0; declaring it says so, and keeps it that
    way if an entity here ever grows one.
    """
    for platform in {item for platforms in PLATFORMS.values() for item in platforms}:
        module = importlib.import_module(
            f"custom_components.preset_manager.{platform.value}"
        )
        assert getattr(module, "PARALLEL_UPDATES", None) == 0, platform.value
