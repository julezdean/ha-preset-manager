"""Tests for the services of the integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import voluptuous as vol
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

from custom_components.preset_manager.const import (
    DOMAIN,
    SERVICE_GET_VALUES,
    SERVICE_SET_ACTIVE_MODE,
    SERVICE_SET_VALUE,
)
from custom_components.preset_manager.services import (
    GET_VALUES_SCHEMA,
    SET_VALUE_SCHEMA,
)

from .conftest import (
    PRESET_ID,
    PRESET_MODE_ID,
    Hubs,
    async_activate_mode,
    async_add_object,
    async_setup_hubs,
    async_setup_one,
    make_preset,
    make_preset_mode,
    runtime_of,
)

NIGHT_BRIGHTNESS = "number.motion_sensor_living_room_night_brightness"
PRESET_SENSOR = "sensor.motion_sensor_living_room_active_mode"

#: Fields Home Assistant adds to every service that takes a target. They are
#: part of the schema but not of the ``fields`` block of services.yaml.
TARGET_FIELDS = {"entity_id", "device_id", "area_id", "floor_id", "label_id"}

BRIGHTNESS_PARAM = {
    "key": "brightness",
    "name": "Brightness",
    "type": "number",
    "minimum": 0,
    "maximum": 100,
    "step": 1,
}


def _preset_device(hass: HomeAssistant, subentry_id: str) -> dr.DeviceEntry:
    """Return the device of one preset."""
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, subentry_id)})
    assert device is not None
    return device


async def test_set_value_by_entity(hass: HomeAssistant, motion: Hubs) -> None:
    """A value can be written by targeting an entity of the preset."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {"mode": "Night", "parameter": "brightness", "value": 15},
        target={"entity_id": PRESET_SENSOR},
        blocking=True,
    )
    assert hass.states.get(NIGHT_BRIGHTNESS).state == "15.0"


async def test_set_value_by_device(
    hass: HomeAssistant, motion: Hubs, subentry_id: str
) -> None:
    """A value can be written by targeting the preset device."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {"mode": "night", "parameter": "off_delay", "value": 30},
        target={"device_id": _preset_device(hass, subentry_id).id},
        blocking=True,
    )
    assert (
        hass.states.get("number.motion_sensor_living_room_night_off_delay").state
        == "30.0"
    )


async def test_set_value_by_area(
    hass: HomeAssistant,
    motion: Hubs,
    subentry_id: str,
    area_registry: ar.AreaRegistry,
) -> None:
    """Home Assistant expands an area down to the preset device for us."""
    area = area_registry.async_create("Living room")
    device = _preset_device(hass, subentry_id)
    dr.async_get(hass).async_update_device(device.id, area_id=area.id)

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {"mode": "night", "parameter": "brightness", "value": 42},
        target={"area_id": area.id},
        blocking=True,
    )
    assert hass.states.get(NIGHT_BRIGHTNESS).state == "42.0"


async def test_the_preset_mode_device_addresses_no_preset(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """Only a preset carries values; its preset mode is not a target."""
    device = _preset_device(hass, PRESET_MODE_ID)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {"mode": "night", "parameter": "brightness", "value": 15},
            target={"device_id": device.id},
            blocking=True,
        )


async def test_set_value_without_a_target_is_refused(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A call that names no preset must not guess at one."""
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {"mode": "night", "parameter": "brightness", "value": 15},
            blocking=True,
        )


async def test_set_value_errors(hass: HomeAssistant, motion: Hubs) -> None:
    """Unknown modes and parameters are reported."""
    for data in (
        {"mode": "Party", "parameter": "brightness", "value": 15},
        {"mode": "Night", "parameter": "volume", "value": 15},
    ):
        with pytest.raises(ServiceValidationError):
            await hass.services.async_call(
                DOMAIN,
                SERVICE_SET_VALUE,
                data,
                target={"entity_id": PRESET_SENSOR},
                blocking=True,
            )


@pytest.mark.parametrize(
    ("parameter", "sent", "expected"),
    [
        # A string that looks like a number stays a string wherever the
        # parameter says so; only a number parameter turns it into one.
        ({"key": "note", "name": "Note", "type": "text"}, "15", "15"),
        (
            {
                "key": "scene",
                "name": "Scene",
                "type": "select",
                "options": ["15", "30"],
            },
            "15",
            "15",
        ),
        (
            {"key": "level", "name": "Level", "type": "number", "maximum": 100},
            "15",
            15.0,
        ),
        ({"key": "active", "name": "Active", "type": "boolean"}, True, True),
    ],
)
async def test_set_value_keeps_the_type_of_the_parameter(
    hass: HomeAssistant, parameter: dict, sent: object, expected: object
) -> None:
    """The service must not coerce a value before the parameter is known.

    Coercing to float in the schema stored "15.0" in a text parameter and made
    a select parameter with numeric options unreachable.
    """
    hubs = await async_setup_one(hass, presets=[make_preset("Lamp", [parameter])])

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {"mode": "night", "parameter": parameter["key"], "value": sent},
        target={"entity_id": "sensor.lamp_active_mode"},
        blocking=True,
    )

    store = hubs.runtime.store
    assert store.get_value(PRESET_ID, "night", parameter["key"]) == expected


async def test_set_value_applies_to_every_target_or_to_none(
    hass: HomeAssistant,
) -> None:
    """A mode one of the targeted presets does not know aborts the whole call.

    The write used to happen while walking the targets, so the first preset
    was already changed when the second one raised.
    """
    await async_setup_hubs(
        hass,
        preset_modes=[
            make_preset_mode(),
            make_preset_mode(
                title="Window State",
                modes=[{"key": "closed", "name": "Closed"}],
                subentry_id="2" * 32,
            ),
        ],
        presets=[
            make_preset("Heating", [BRIGHTNESS_PARAM], subentry_id="a" * 32),
            make_preset(
                "Shutter",
                [BRIGHTNESS_PARAM],
                subentry_id="b" * 32,
                preset_mode="2" * 32,
            ),
        ],
    )

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {"mode": "night", "parameter": "brightness", "value": 15},
            target={
                "entity_id": [
                    "sensor.heating_active_mode",
                    "sensor.shutter_active_mode",
                ]
            },
            blocking=True,
        )

    store = runtime_of(hass).store
    # "night" exists in the house mode, but the shutter never heard of it -
    # so nothing at all was written.
    assert store.get_value("a" * 32, "night", "brightness") is None


async def test_get_values(hass: HomeAssistant, motion: Hubs) -> None:
    """The response service returns the values of a preset."""
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {"mode": "Night", "parameter": "brightness", "value": 15},
        target={"entity_id": PRESET_SENSOR},
        blocking=True,
    )
    await async_activate_mode(hass, "night")

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_VALUES,
        {},
        target={"entity_id": PRESET_SENSOR},
        blocking=True,
        return_response=True,
    )
    assert response["mode"] == "night"
    assert response["values"]["brightness"] == 15.0

    response = await hass.services.async_call(
        DOMAIN,
        SERVICE_GET_VALUES,
        {"mode": "Home"},
        target={"entity_id": PRESET_SENSOR},
        blocking=True,
        return_response=True,
    )
    assert response["mode"] == "home"
    assert response["values"]["brightness"] is None


async def test_get_values_needs_exactly_one_preset(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """A response carries the values of one preset, so two are refused."""
    await async_add_object(
        hass,
        motion,
        "preset_modes",
        make_preset_mode(title="Window State", subentry_id="2" * 32),
    )
    await async_add_object(
        hass,
        motion,
        "presets",
        make_preset(
            "Shutter",
            [BRIGHTNESS_PARAM],
            subentry_id="b" * 32,
            preset_mode="2" * 32,
        ),
    )

    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_GET_VALUES,
            {},
            target={"entity_id": [PRESET_SENSOR, "sensor.shutter_active_mode"]},
            blocking=True,
            return_response=True,
        )


async def test_value_services_without_setup(hass: HomeAssistant) -> None:
    """Calling a service without a loaded entry raises a clear error."""
    from custom_components.preset_manager.services import async_setup_services

    async_setup_services(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN,
            SERVICE_SET_VALUE,
            {"mode": "night", "parameter": "brightness", "value": 1},
            target={"entity_id": PRESET_SENSOR},
            blocking=True,
        )


async def test_set_active_mode_is_an_entity_service_of_a_preset(
    hass: HomeAssistant, motion: Hubs
) -> None:
    """It is aimed at the selector of a preset, and a preset mode has none.

    Setting a mode by hand is something a single preset does; a preset mode
    gets its mode from its conditions or from the entity it follows, so there
    is nothing there for this service to be aimed at.
    """
    assert hass.services.has_service(DOMAIN, SERVICE_SET_ACTIVE_MODE)
    registry = er.async_get(hass)
    assert registry.async_get("select.house_mode_active_mode") is None
    assert (
        registry.async_get("select.motion_sensor_living_room_mode_selection")
        is not None
    )


def _schema_keys(schema: vol.Schema) -> set[str]:
    """Return the field names a service schema accepts, without the target."""
    return {str(key.schema) for key in schema.schema} - TARGET_FIELDS


@pytest.mark.parametrize(
    ("service", "schema"),
    [
        (SERVICE_SET_VALUE, SET_VALUE_SCHEMA),
        (SERVICE_GET_VALUES, GET_VALUES_SCHEMA),
    ],
)
def test_services_yaml_matches_the_schema(service: str, schema: vol.Schema) -> None:
    """Every field offered in the UI has to be one the service accepts.

    services.yaml drives the form Home Assistant renders; the voluptuous schema
    decides what the call may contain. When they drift apart the service works
    from a script and fails from the UI, which is how a leftover field named
    "mode" survived a rename.
    """
    path = Path(__file__).parent.parent / "custom_components" / DOMAIN
    described = yaml.safe_load((path / "services.yaml").read_text())
    assert set(described[service].get("fields", {})) == _schema_keys(schema)


def test_every_service_takes_a_target() -> None:
    """A service without a target would be addressed by name again."""
    path = Path(__file__).parent.parent / "custom_components" / DOMAIN
    described = yaml.safe_load((path / "services.yaml").read_text())
    for service, spec in described.items():
        assert spec.get("target"), f"{service} has no target"


@pytest.mark.parametrize("language", ["strings", "en", "de"])
def test_every_service_field_is_translated(language: str) -> None:
    """A field without a translation shows up as a raw key in the UI."""
    path = Path(__file__).parent.parent / "custom_components" / DOMAIN
    described = yaml.safe_load((path / "services.yaml").read_text())
    source = (
        path / "strings.json"
        if language == "strings"
        else path / "translations" / f"{language}.json"
    )
    translated = json.loads(source.read_text())["services"]

    for service, spec in described.items():
        assert set(spec.get("fields", {})) == set(translated[service]["fields"])
