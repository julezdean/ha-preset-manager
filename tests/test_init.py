"""Tests for the setup of the integration."""

from __future__ import annotations

import importlib
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager import (
    PLATFORMS,
    _async_remove_stale_entities,
    blueprints,
)
from custom_components.preset_manager.const import (
    CONF_ENTRY_TYPE,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_TYPE_PRESET_MODE,
    ENTRY_VERSION,
    STORAGE_KEY,
    STORAGE_VERSION,
)
from custom_components.preset_manager.sources import ConditionSource
from custom_components.preset_manager.store import _ValueFileStore, async_get_store

from .conftest import BRIGHTNESS, PRESET_ID, PRESET_MODE_ID, make_entry, make_preset


async def test_setup_creates_entities(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """The preset mode and preset entities are created."""
    assert hass.states.get("select.house_mode_active_mode") is not None
    assert hass.states.get("sensor.house_mode_mode") is not None
    assert hass.states.get("sensor.motion_sensor_living_room_active_mode") is not None
    assert hass.states.get("sensor.motion_sensor_living_room_brightness") is not None


async def test_preset_device_hangs_below_the_preset_mode(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """The preset device is attached to its preset mode device."""
    registry = dr.async_get(hass)
    preset_mode = registry.async_get_device(identifiers={(DOMAIN, PRESET_MODE_ID)})
    instance = registry.async_get_device(identifiers={(DOMAIN, PRESET_ID)})
    assert preset_mode is not None
    assert instance is not None
    assert instance.via_device_id == preset_mode.id


async def test_no_entity_is_stale_right_after_a_setup(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """The cleanup and the platforms have to agree on every unique id.

    They did not: the cleanup expected "<subentry>_mode" for the active mode
    sensor of a preset while the platform registered "<subentry>_active_mode",
    so that entity was removed and restored on every single setup.
    """
    entry = make_entry(presets=[make_preset("Lamp", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    def unique_ids() -> set[str]:
        return {
            item.unique_id
            for item in er.async_entries_for_config_entry(
                entity_registry, entry.entry_id
            )
        }

    before = unique_ids()
    assert before  # the test would pass on an empty registry otherwise
    _async_remove_stale_entities(hass, entry, entry.runtime_data)
    assert unique_ids() == before


async def test_a_new_entry_records_its_type(hass: HomeAssistant) -> None:
    """The kind of an entry is written, not derived from a missing key."""
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

    assert result["data"][CONF_ENTRY_TYPE] == ENTRY_TYPE_PRESET_MODE
    assert not blueprints.is_blueprint(hass.config_entries.async_entries(DOMAIN)[0])


async def test_an_entry_without_a_type_is_a_preset_mode(hass: HomeAssistant) -> None:
    """Reading stays tolerant, so a missing marker still means preset mode."""
    entry = make_entry()
    assert CONF_ENTRY_TYPE not in entry.data
    assert blueprints.entry_type(entry) == ENTRY_TYPE_PRESET_MODE
    assert not blueprints.is_blueprint(entry)


async def test_removing_a_preset_mode_drops_its_stored_values(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """Deleting a preset mode deletes the values of its presets."""
    coordinator = next(iter(motion_entry.runtime_data.presets.values()))
    coordinator.async_set_value("night", "brightness", 15)
    await hass.async_block_till_done()

    store = async_get_store(hass)
    assert store.get_value(PRESET_ID, "night", "brightness") == 15.0

    assert await hass.config_entries.async_remove(motion_entry.entry_id)
    await hass.async_block_till_done()

    assert store.get_value(PRESET_ID, "night", "brightness") is None
    assert store.active_mode(motion_entry.entry_id) is None


async def test_current_entry_needs_no_migration(
    hass: HomeAssistant, motion_entry: MockConfigEntry
) -> None:
    """An entry written by this version sets up without being touched."""
    assert motion_entry.version == ENTRY_VERSION
    assert motion_entry.minor_version == ENTRY_MINOR_VERSION
    assert motion_entry.state is ConfigEntryState.LOADED


async def test_an_entry_below_the_current_schema_still_loads(
    hass: HomeAssistant,
) -> None:
    """An older entry has to be let through, not refused.

    This is the whole reason ``async_migrate_entry`` exists from 0.1.0 on,
    before it has a single step to run: without the handler Home Assistant
    logs "Migration handler not found" and refuses an entry whose *major*
    version is lower than the flow's. A lower minor version alone is tolerated
    without a handler, so only a lower major version exercises the guard.

    There is no such entry in the wild yet - the first release writes 1.1 -
    which is exactly why the path is worth a test before it is needed.
    """
    entry = make_entry(version=ENTRY_VERSION - 1)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.house_mode_mode").state == "Home"


async def test_entry_from_a_newer_version_is_refused(hass: HomeAssistant) -> None:
    """A downgrade must fail loudly instead of guessing at unknown keys."""
    entry = make_entry(version=ENTRY_VERSION + 1)
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


def _following(entity: str) -> MockConfigEntry:
    """A preset mode whose every mode has a condition on one entity."""
    return make_entry(
        conditions={
            key: _state(entity, name)
            for key, name in (
                ("home", "Home"),
                ("away", "Away"),
                ("night", "Night"),
                ("window_open", "Window open"),
            )
        },
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
    entry = make_entry(presets=[make_preset("Lamp", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    next(iter(entry.runtime_data.presets.values())).async_set_value(
        "night", "brightness", 15
    )
    await hass.async_block_till_done()
    # Still only scheduled - nothing has been written yet.
    assert STORAGE_KEY not in hass_storage

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    stored = hass_storage[STORAGE_KEY]["data"]
    assert stored["values"][PRESET_ID]["night"]["brightness"] == 15.0


async def test_unload_stops_evaluating_the_conditions(hass: HomeAssistant) -> None:
    """Nothing may keep listening once the entry is gone.

    A leaked subscription is invisible from the states - it would recompute
    against a runtime that is no longer set up - so it is counted instead.
    """
    hass.states.async_set("sensor.mode_source", "Home")
    entry = _following("sensor.mode_source")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
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

        assert await hass.config_entries.async_unload(entry.entry_id)
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
    entry = _following("sensor.mode_source")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    await hass.config_entries.async_reload(entry.entry_id)
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
    """A failed unload must not leave the entry half alive.

    Home Assistant marks such an entry as failed and never retries it, so a
    mode source left running would keep evaluating against a torn down
    runtime, and pending values would never reach the disk.
    """
    hass.states.async_set("sensor.mode_source", "Home")
    entry = _following("sensor.mode_source")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    next(iter(entry.runtime_data.presets.values())).async_set_value(
        "night", "brightness", 15
    )
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
        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

        # The failure is still reported, ...
        assert entry.state is ConfigEntryState.FAILED_UNLOAD
        # ... but nothing is left listening.
        hass.states.async_set("sensor.mode_source", "Night")
        await hass.async_block_till_done()
        assert evaluations == 0

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
    for platform in PLATFORMS:
        module = importlib.import_module(
            f"custom_components.preset_manager.{platform.value}"
        )
        assert getattr(module, "PARALLEL_UPDATES", None) == 0, platform.value
