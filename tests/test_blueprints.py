"""Tests for blueprints and the presets that follow them."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager.const import (
    BLUEPRINT_NONE,
    CONF_BLUEPRINT,
    CONF_ENTRY_TYPE,
    CONF_PARAMETERS,
    DOMAIN,
    ENTRY_TYPE_BLUEPRINT,
    SUBENTRY_TYPE_PRESET,
)
from custom_components.preset_manager.store import async_get_store

from .conftest import (
    BLUEPRINT_ID,
    BOOST_DURATION,
    BRIGHTNESS,
    PRESET_ID,
    TARGET_TEMPERATURE,
    make_blueprint,
    make_entry,
    make_preset,
)


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> MockConfigEntry:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def _bound_setup(
    hass: HomeAssistant, *, parameters: list[dict] | None = None
) -> tuple[MockConfigEntry, MockConfigEntry]:
    """Set up a blueprint with one preset following it."""
    blueprint = await _setup(hass, make_blueprint(parameters=parameters))
    preset_mode = await _setup(
        hass,
        make_entry(
            modes=[
                {"key": "home", "name": "Home"},
                {"key": "night", "name": "Night"},
            ],
            presets=[make_preset("Heating Living Room", [], blueprint=BLUEPRINT_ID)],
        ),
    )
    return blueprint, preset_mode


async def _reconfigure(hass: HomeAssistant, preset_mode: MockConfigEntry) -> dict:
    """Open the reconfiguration menu of the preset."""
    return await hass.config_entries.subentries.async_init(
        (preset_mode.entry_id, SUBENTRY_TYPE_PRESET),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": PRESET_ID,
        },
    )


# Creating a blueprint -----------------------------------------------------


async def test_config_flow_creates_a_blueprint(hass: HomeAssistant) -> None:
    """A blueprint is a config entry of its own, holding only parameters."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "blueprint"}
    )
    assert result["step_id"] == "blueprint"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Heating"}
    )
    assert result["step_id"] == "manage_parameters"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PARAMETERS: [{"name": "Target temperature", "type": "number"}]},
    )
    assert result["step_id"] == "parameter_details"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"minimum": 5, "maximum": 30, "step": 0.5, "default": 21}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert entry.data[CONF_ENTRY_TYPE] == ENTRY_TYPE_BLUEPRINT
    assert entry.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    # It is configuration and nothing else: no device, no entities.
    assert not hass.states.async_entity_ids(DOMAIN)
    assert entry.state is config_entries.ConfigEntryState.LOADED


async def test_a_blueprint_takes_no_presets(hass: HomeAssistant) -> None:
    """Presets are added to a preset mode, not to a blueprint."""
    from custom_components.preset_manager.config_flow import PresetModeConfigFlow

    blueprint = await _setup(hass, make_blueprint())
    preset_mode = await _setup(hass, make_entry())

    assert PresetModeConfigFlow.async_get_supported_subentry_types(blueprint) == {}
    assert (
        SUBENTRY_TYPE_PRESET
        in PresetModeConfigFlow.async_get_supported_subentry_types(preset_mode)
    )


# Following a blueprint ----------------------------------------------------


async def test_preset_is_created_from_a_blueprint(hass: HomeAssistant) -> None:
    """Picking a blueprint skips the parameter editor for good."""
    await _setup(hass, make_blueprint(parameters=[TARGET_TEMPERATURE]))
    preset_mode = await _setup(hass, make_entry())

    result = await hass.config_entries.subentries.async_init(
        (preset_mode.entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    assert set(result["data_schema"].schema) == {"name", CONF_BLUEPRINT}

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {"name": "Heating Living Room", CONF_BLUEPRINT: BLUEPRINT_ID},
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(preset_mode.subentries.values()))
    # The parameters are not copied - the set is the only place they live.
    assert dict(subentry.data) == {CONF_BLUEPRINT: BLUEPRINT_ID}
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature")
        is not None
    )
    assert hass.states.get("sensor.heating_living_room_target_temperature") is not None


async def test_changing_the_set_reaches_every_preset(hass: HomeAssistant) -> None:
    """A parameter added to the set appears in every preset following it."""
    blueprint, preset_mode = await _bound_setup(hass)
    coordinator = next(iter(preset_mode.runtime_data.presets.values()))
    coordinator.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(blueprint.entry_id)
    assert result["step_id"] == "manage_parameters"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                {
                    "key": "target_temperature",
                    "name": "Target temperature",
                    "type": "number",
                },
                {"name": "Boost duration", "type": "number"},
            ]
        },
    )
    # Only the new row needs its details.
    assert result["step_id"] == "parameter_details"
    assert result["description_placeholders"]["parameter"] == "Boost duration"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"minimum": 0, "maximum": 120, "step": 5}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    # The preset followed along without being touched itself.
    assert (
        hass.states.get("number.heating_living_room_night_boost_duration") is not None
    )
    subentry = next(iter(preset_mode.subentries.values()))
    assert dict(subentry.data) == {CONF_BLUEPRINT: BLUEPRINT_ID}
    # Its values survived the update.
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )


async def test_removing_a_parameter_from_the_set_removes_its_entities(
    hass: HomeAssistant,
) -> None:
    """What the set drops disappears from every preset following it."""
    blueprint, _preset_mode = await _bound_setup(
        hass, parameters=[TARGET_TEMPERATURE, BOOST_DURATION]
    )
    assert hass.states.get("number.heating_living_room_home_boost_duration")

    result = await hass.config_entries.options.async_init(blueprint.entry_id)
    result = await hass.config_entries.options.async_configure(
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
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    assert hass.states.get("number.heating_living_room_home_boost_duration") is None
    assert hass.states.get("number.heating_living_room_home_target_temperature")


async def test_retyping_in_the_set_drops_the_stored_values(
    hass: HomeAssistant,
) -> None:
    """A retyped parameter keeps its key, so its values have to go."""
    blueprint, preset_mode = await _bound_setup(hass)
    coordinator = next(iter(preset_mode.runtime_data.presets.values()))
    coordinator.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(blueprint.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            CONF_PARAMETERS: [
                {
                    "key": "target_temperature",
                    "name": "Target temperature",
                    "type": "text",
                }
            ]
        },
    )
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    store = async_get_store(hass)
    assert not store.has_value(PRESET_ID, "night", "target_temperature")
    assert hass.states.get("text.heating_living_room_night_target_temperature")


async def test_preset_sensor_names_its_blueprint(hass: HomeAssistant) -> None:
    """Where the parameters come from is readable from the preset sensor."""
    _blueprint, _preset_mode = await _bound_setup(hass)

    state = hass.states.get("sensor.heating_living_room_active_mode")
    assert state.attributes["blueprint"] == "Heating"

    free = hass.states.get("sensor.house_mode_mode")
    assert "blueprint" not in free.attributes


async def test_values_stay_per_preset(hass: HomeAssistant) -> None:
    """Two presets share the definitions of a set, never its values."""
    await _setup(hass, make_blueprint())
    preset_mode = await _setup(
        hass,
        make_entry(
            modes=[{"key": "home", "name": "Home"}],
            presets=[
                make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID),
                make_preset(
                    "Heating Bedroom",
                    [],
                    blueprint=BLUEPRINT_ID,
                    subentry_id="b" * 32,
                ),
            ],
        ),
    )
    bath, bedroom = preset_mode.runtime_data.presets.values()
    bath.async_set_value("home", "target_temperature", 23)
    bedroom.async_set_value("home", "target_temperature", 18)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heating_bath_target_temperature").state == "23.0"
    assert hass.states.get("sensor.heating_bedroom_target_temperature").state == "18.0"


# The lock ---------------------------------------------------------------------


async def test_bound_preset_has_no_parameter_editor(hass: HomeAssistant) -> None:
    """The parameters of a bound preset are edited in its set, nowhere else."""
    _blueprint, preset_mode = await _bound_setup(hass)

    result = await _reconfigure(hass, preset_mode)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == [
        "blueprint",
        "rename_preset",
        "assign_preset_mode",
    ]


async def test_parameter_editor_refuses_a_preset_bound_meanwhile(
    hass: HomeAssistant,
) -> None:
    """The lock is on the step, not only on the menu that leads to it."""
    await _setup(hass, make_blueprint())
    preset_mode = await _setup(
        hass, make_entry(presets=[make_preset("Heating Bath", [BRIGHTNESS])])
    )

    # The menu is opened while the preset is still free ...
    result = await _reconfigure(hass, preset_mode)
    assert "manage_parameters" in result["menu_options"]

    # ... and the preset is handed to a set before the editor is picked.
    hass.config_entries.async_update_subentry(
        preset_mode,
        preset_mode.subentries[PRESET_ID],
        data={CONF_BLUEPRINT: BLUEPRINT_ID},
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "blueprint_locked"


async def test_free_preset_keeps_its_editor(hass: HomeAssistant) -> None:
    """A preset that follows no set is edited as before."""
    await _setup(hass, make_blueprint())
    preset_mode = await _setup(
        hass, make_entry(presets=[make_preset("Motion Sensor", [BRIGHTNESS])])
    )

    result = await _reconfigure(hass, preset_mode)
    assert result["menu_options"] == [
        "manage_parameters",
        "blueprint",
        "rename_preset",
        "assign_preset_mode",
    ]


async def test_menu_hides_the_template_step_without_any_set(
    hass: HomeAssistant,
) -> None:
    """Without a blueprint there is nothing to attach a preset to."""
    preset_mode = await _setup(
        hass, make_entry(presets=[make_preset("Motion Sensor", [BRIGHTNESS])])
    )

    result = await _reconfigure(hass, preset_mode)
    assert result["menu_options"] == [
        "manage_parameters",
        "rename_preset",
        "assign_preset_mode",
    ]


# Attaching and detaching ------------------------------------------------------


async def test_attaching_replaces_the_parameters(hass: HomeAssistant) -> None:
    """An existing preset can be handed over to a blueprint."""
    await _setup(hass, make_blueprint())
    preset_mode = await _setup(
        hass, make_entry(presets=[make_preset("Heating Bath", [BRIGHTNESS])])
    )
    assert hass.states.get("number.heating_bath_home_brightness")

    result = await _reconfigure(hass, preset_mode)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "blueprint"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_BLUEPRINT: BLUEPRINT_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = preset_mode.subentries[PRESET_ID]
    assert dict(subentry.data) == {CONF_BLUEPRINT: BLUEPRINT_ID}
    assert hass.states.get("number.heating_bath_home_brightness") is None
    assert hass.states.get("number.heating_bath_home_target_temperature")


async def test_detaching_keeps_the_parameters_and_the_values(
    hass: HomeAssistant,
) -> None:
    """Leaving a set turns its parameters into the preset's own."""
    _blueprint, preset_mode = await _bound_setup(hass)
    coordinator = next(iter(preset_mode.runtime_data.presets.values()))
    coordinator.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await _reconfigure(hass, preset_mode)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "blueprint"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_BLUEPRINT: BLUEPRINT_NONE}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = preset_mode.subentries[PRESET_ID]
    assert CONF_BLUEPRINT not in subentry.data
    assert subentry.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )

    # The parameter editor is open again.
    result = await _reconfigure(hass, preset_mode)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )
    assert result["step_id"] == "manage_parameters"


async def test_deleting_the_set_leaves_the_presets_working(
    hass: HomeAssistant,
) -> None:
    """A deleted set costs its presets the lock, not their configuration."""
    blueprint, preset_mode = await _bound_setup(hass)
    coordinator = next(iter(preset_mode.runtime_data.presets.values()))
    coordinator.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_remove(blueprint.entry_id)
    await hass.async_block_till_done()

    subentry = preset_mode.subentries[PRESET_ID]
    assert CONF_BLUEPRINT not in subentry.data
    assert subentry.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )


async def test_a_set_that_disappeared_leaves_the_preset_empty(
    hass: HomeAssistant,
) -> None:
    """A binding pointing nowhere is logged, it does not break the setup."""
    preset_mode = await _setup(
        hass,
        make_entry(
            presets=[make_preset("Heating Bath", [], blueprint="does-not-exist")]
        ),
    )

    assert preset_mode.state is config_entries.ConfigEntryState.LOADED
    coordinator = next(iter(preset_mode.runtime_data.presets.values()))
    assert coordinator.config.parameters == ()
    assert hass.states.get("sensor.heating_bath_active_mode").state == "Home"


async def test_services_ignore_the_blueprint_entry(hass: HomeAssistant) -> None:
    """A set is a config entry too, but not one a service can address."""
    _blueprint, _preset_mode = await _bound_setup(hass)

    await hass.services.async_call(
        DOMAIN,
        "set_value",
        {"mode": "night", "parameter": "target_temperature", "value": 17},
        target={"entity_id": "sensor.heating_living_room_active_mode"},
        blocking=True,
    )
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )
