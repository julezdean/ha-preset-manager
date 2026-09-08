"""Tests for blueprints and the presets that follow them."""

from __future__ import annotations

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.preset_manager.config_flow import PresetManagerConfigFlow
from custom_components.preset_manager.const import (
    BLUEPRINT_NONE,
    CONF_BLUEPRINT,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    DOMAIN,
    HUB_BLUEPRINTS,
    SUBENTRY_TYPE_BLUEPRINT,
    SUBENTRY_TYPE_PRESET,
)
from custom_components.preset_manager.store import async_get_store

from .conftest import (
    BLUEPRINT_ID,
    BOOST_DURATION,
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

TWO_MODES = [{"key": "home", "name": "Home"}, {"key": "night", "name": "Night"}]


async def _bound_setup(
    hass: HomeAssistant, *, parameters: list[dict] | None = None
) -> Hubs:
    """Set up a blueprint with one preset following it."""
    return await async_setup_hubs(
        hass,
        blueprints=[make_blueprint(parameters=parameters)],
        preset_modes=[make_preset_mode(modes=TWO_MODES)],
        presets=[make_preset("Heating Living Room", [], blueprint=BLUEPRINT_ID)],
    )


async def _reconfigure_preset(hass: HomeAssistant, hubs: Hubs) -> dict:
    """Open the reconfiguration menu of the preset."""
    return await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": PRESET_ID,
        },
    )


async def _edit_blueprint(hass: HomeAssistant, hubs: Hubs) -> dict:
    """Open the parameter editor of the blueprint."""
    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("blueprints").entry_id, SUBENTRY_TYPE_BLUEPRINT),
        context={
            "source": config_entries.SOURCE_RECONFIGURE,
            "subentry_id": BLUEPRINT_ID,
        },
    )
    assert result["type"] is FlowResultType.MENU
    return await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )


# Creating a blueprint -----------------------------------------------------


async def test_config_flow_creates_a_blueprint(hass: HomeAssistant) -> None:
    """A blueprint is a subentry of its hub, holding only parameters."""
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
    assert entry.unique_id == HUB_BLUEPRINTS
    blueprint = next(iter(entry.subentries.values()))
    assert blueprint.title == "Heating"
    assert blueprint.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    # It is configuration and nothing else: no device, no entities.
    assert not hass.states.async_entity_ids(DOMAIN)
    assert entry.state is config_entries.ConfigEntryState.LOADED


async def test_a_second_blueprint_joins_the_hub(hass: HomeAssistant) -> None:
    """The hub is created once and collects every blueprint after that."""
    hubs = await async_setup_hubs(hass, blueprints=[make_blueprint()])

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "blueprint"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Shutters"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PARAMETERS: [{"name": "Position", "type": "number"}]},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"minimum": 0, "maximum": 100, "step": 1}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "blueprints_added"
    await hass.async_block_till_done()

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    titles = {item.title for item in hubs.entry("blueprints").subentries.values()}
    assert titles == {"Heating", "Shutters"}


async def test_each_hub_takes_only_its_own_kind(hass: HomeAssistant) -> None:
    """A blueprint hub holds blueprints; presets go to the presets hub."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [BRIGHTNESS])],
    )

    for kind, subentry_type in (
        ("blueprints", SUBENTRY_TYPE_BLUEPRINT),
        ("presets", SUBENTRY_TYPE_PRESET),
    ):
        supported = PresetManagerConfigFlow.async_get_supported_subentry_types(
            hubs.entry(kind)
        )
        assert list(supported) == [subentry_type]


# Following a blueprint ----------------------------------------------------


async def test_preset_is_created_from_a_blueprint(hass: HomeAssistant) -> None:
    """Picking a blueprint skips the parameter editor for good."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint(parameters=[TARGET_TEMPERATURE])],
        preset_modes=[make_preset_mode()],
        presets=[],
    )

    result = await hass.config_entries.subentries.async_init(
        (hubs.entry("presets").entry_id, SUBENTRY_TYPE_PRESET),
        context={"source": config_entries.SOURCE_USER},
    )
    assert set(result["data_schema"].schema) == {
        "name",
        CONF_PRESET_MODE,
        CONF_BLUEPRINT,
    }

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"],
        {
            "name": "Heating Living Room",
            CONF_PRESET_MODE: PRESET_MODE_ID,
            CONF_BLUEPRINT: BLUEPRINT_ID,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()

    subentry = next(iter(hubs.entry("presets").subentries.values()))
    # Neither the parameters nor the modes are copied - they are read from
    # what the preset follows, on every setup.
    assert dict(subentry.data) == {
        CONF_PRESET_MODE: PRESET_MODE_ID,
        CONF_BLUEPRINT: BLUEPRINT_ID,
    }
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature")
        is not None
    )
    assert hass.states.get("sensor.heating_living_room_target_temperature") is not None


async def test_changing_the_blueprint_reaches_every_preset(
    hass: HomeAssistant,
) -> None:
    """A parameter added to a blueprint appears in every preset following it."""
    hubs = await _bound_setup(hass)
    hubs.preset.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await _edit_blueprint(hass, hubs)
    assert result["step_id"] == "manage_parameters"

    result = await hass.config_entries.subentries.async_configure(
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

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"minimum": 0, "maximum": 120, "step": 5}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    # The preset followed along without being touched itself.
    assert (
        hass.states.get("number.heating_living_room_night_boost_duration") is not None
    )
    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert dict(subentry.data) == {
        CONF_PRESET_MODE: PRESET_MODE_ID,
        CONF_BLUEPRINT: BLUEPRINT_ID,
    }
    # Its values survived the update.
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )


async def test_removing_a_parameter_removes_its_entities(
    hass: HomeAssistant,
) -> None:
    """What the blueprint drops disappears from every preset following it."""
    hubs = await _bound_setup(hass, parameters=[TARGET_TEMPERATURE, BOOST_DURATION])
    assert hass.states.get("number.heating_living_room_home_boost_duration")

    result = await _edit_blueprint(hass, hubs)
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

    assert hass.states.get("number.heating_living_room_home_boost_duration") is None
    assert hass.states.get("number.heating_living_room_home_target_temperature")


async def test_retyping_drops_the_stored_values(hass: HomeAssistant) -> None:
    """A retyped parameter keeps its key, so its values have to go."""
    hubs = await _bound_setup(hass)
    hubs.preset.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await _edit_blueprint(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
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
    result = await hass.config_entries.subentries.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    store = async_get_store(hass)
    assert not store.has_value(PRESET_ID, "night", "target_temperature")
    assert hass.states.get("text.heating_living_room_night_target_temperature")


async def test_preset_sensor_names_its_blueprint(hass: HomeAssistant) -> None:
    """Where the parameters come from is readable from the preset sensor."""
    await _bound_setup(hass)

    state = hass.states.get("sensor.heating_living_room_active_mode")
    assert state.attributes["blueprint"] == "Heating"

    free = hass.states.get("sensor.house_mode_mode")
    assert "blueprint" not in free.attributes


async def test_values_stay_per_preset(hass: HomeAssistant) -> None:
    """Two presets share the definitions of a blueprint, never its values."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode(modes=[{"key": "home", "name": "Home"}])],
        presets=[
            make_preset("Heating Bath", [], blueprint=BLUEPRINT_ID),
            make_preset(
                "Heating Bedroom",
                [],
                blueprint=BLUEPRINT_ID,
                subentry_id="b" * 32,
            ),
        ],
    )
    bath, bedroom = hubs.runtime.presets.values()
    bath.async_set_value("home", "target_temperature", 23)
    bedroom.async_set_value("home", "target_temperature", 18)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.heating_bath_target_temperature").state == "23.0"
    assert hass.states.get("sensor.heating_bedroom_target_temperature").state == "18.0"


# The lock ---------------------------------------------------------------------


async def test_bound_preset_has_no_parameter_editor(hass: HomeAssistant) -> None:
    """The parameters of a bound preset are edited in its blueprint."""
    hubs = await _bound_setup(hass)

    result = await _reconfigure_preset(hass, hubs)
    assert result["type"] is FlowResultType.MENU
    assert result["menu_options"] == [
        "rename",
        "assign_preset_mode",
        "assign_blueprint",
        "duplicate",
    ]


async def test_parameter_editor_refuses_a_preset_bound_meanwhile(
    hass: HomeAssistant,
) -> None:
    """The lock is on the step, not only on the menu that leads to it."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [BRIGHTNESS])],
    )

    # The menu is opened while the preset is still free ...
    result = await _reconfigure_preset(hass, hubs)
    assert "manage_parameters" in result["menu_options"]

    # ... and the preset is handed to a blueprint before the editor is picked.
    presets = hubs.entry("presets")
    hass.config_entries.async_update_subentry(
        presets,
        presets.subentries[PRESET_ID],
        data={CONF_PRESET_MODE: PRESET_MODE_ID, CONF_BLUEPRINT: BLUEPRINT_ID},
    )
    await hass.async_block_till_done()

    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "blueprint_locked"


async def test_free_preset_keeps_its_editor(hass: HomeAssistant) -> None:
    """A preset that follows no blueprint is edited as before."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Motion Sensor", [BRIGHTNESS])],
    )

    result = await _reconfigure_preset(hass, hubs)
    assert result["menu_options"] == [
        "manage_parameters",
        "rename",
        "assign_preset_mode",
        "assign_blueprint",
        "duplicate",
    ]


async def test_menu_hides_the_blueprint_step_without_any(
    hass: HomeAssistant,
) -> None:
    """Without a blueprint there is nothing to attach a preset to."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Motion Sensor", [BRIGHTNESS])],
    )

    result = await _reconfigure_preset(hass, hubs)
    assert result["menu_options"] == [
        "manage_parameters",
        "rename",
        "assign_preset_mode",
        "duplicate",
    ]


# Attaching and detaching ------------------------------------------------------


async def test_attaching_replaces_the_parameters(hass: HomeAssistant) -> None:
    """An existing preset can be handed over to a blueprint."""
    hubs = await async_setup_hubs(
        hass,
        blueprints=[make_blueprint()],
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [BRIGHTNESS])],
    )
    assert hass.states.get("number.heating_bath_home_brightness")

    result = await _reconfigure_preset(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_blueprint"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_BLUEPRINT: BLUEPRINT_ID}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert dict(subentry.data) == {
        CONF_PRESET_MODE: PRESET_MODE_ID,
        CONF_BLUEPRINT: BLUEPRINT_ID,
    }
    assert hass.states.get("number.heating_bath_home_brightness") is None
    assert hass.states.get("number.heating_bath_home_target_temperature")


async def test_detaching_keeps_the_parameters_and_the_values(
    hass: HomeAssistant,
) -> None:
    """Leaving a blueprint turns its parameters into the preset's own."""
    hubs = await _bound_setup(hass)
    hubs.preset.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    result = await _reconfigure_preset(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "assign_blueprint"}
    )
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {CONF_BLUEPRINT: BLUEPRINT_NONE}
    )
    assert result["type"] is FlowResultType.ABORT
    await hass.async_block_till_done()

    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert CONF_BLUEPRINT not in subentry.data
    assert subentry.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )

    # The parameter editor is open again.
    result = await _reconfigure_preset(hass, hubs)
    result = await hass.config_entries.subentries.async_configure(
        result["flow_id"], {"next_step_id": "manage_parameters"}
    )
    assert result["step_id"] == "manage_parameters"


async def test_deleting_the_blueprint_leaves_the_presets_working(
    hass: HomeAssistant,
) -> None:
    """A deleted blueprint costs its presets the lock, not their configuration.

    Home Assistant offers no hook for the removal of a subentry, so the
    parameters handed over here come from the runtime - the last place they
    still exist while the update listener runs.
    """
    hubs = await _bound_setup(hass)
    hubs.preset.async_set_value("night", "target_temperature", 17)
    await hass.async_block_till_done()

    hass.config_entries.async_remove_subentry(hubs.entry("blueprints"), BLUEPRINT_ID)
    await hass.async_block_till_done()

    subentry = hubs.entry("presets").subentries[PRESET_ID]
    assert CONF_BLUEPRINT not in subentry.data
    assert subentry.data[CONF_PARAMETERS][0]["key"] == "target_temperature"
    assert (
        hass.states.get("number.heating_living_room_night_target_temperature").state
        == "17.0"
    )


async def test_a_blueprint_that_disappeared_leaves_the_preset_empty(
    hass: HomeAssistant,
) -> None:
    """A reference pointing nowhere is logged, it does not break the setup."""
    hubs = await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[make_preset("Heating Bath", [], blueprint="does-not-exist")],
    )

    assert hubs.entry("presets").state is config_entries.ConfigEntryState.LOADED
    assert hubs.preset.config.parameters == ()
    assert hass.states.get("sensor.heating_bath_active_mode").state == "Home"


async def test_services_ignore_the_blueprints_hub(hass: HomeAssistant) -> None:
    """The blueprints hub is a config entry too, but addresses no preset."""
    await _bound_setup(hass)

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
