"""Fixtures for the Preset Mode tests."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentryData
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager.const import (
    CONF_BLUEPRINT,
    CONF_CONDITIONS,
    CONF_ENTRY_TYPE,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_TYPE_BLUEPRINT,
    ENTRY_VERSION,
    SERVICE_SET_ACTIVE_MODE,
    SUBENTRY_TYPE_PRESET,
)

#: Entry id of the preset mode created by :func:`make_entry`.
PRESET_MODE_ID = "11111111111111111111111111111111"
PRESET_ID = "0123456789abcdef0123456789abcdef"
#: Entry id of the blueprint created by :func:`make_blueprint`.
BLUEPRINT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
#: Mode selector of the preset mode created by :func:`make_entry`.
PRESET_MODE_SELECT = "select.house_mode_active_mode"

MODES = [
    {"key": "home", "name": "Home"},
    {"key": "away", "name": "Away"},
    {"key": "night", "name": "Night"},
    {"key": "window_open", "name": "Window open"},
]

BRIGHTNESS = {
    "key": "brightness",
    "name": "Brightness",
    "type": "number",
    "minimum": 0,
    "maximum": 100,
    "step": 1,
    "unit": "%",
}
COLOR_TEMPERATURE = {
    "key": "color_temperature",
    "name": "Color temperature",
    "type": "number",
    "minimum": 2000,
    "maximum": 6500,
    "step": 50,
    "unit": "K",
}
OFF_DELAY = {
    "key": "off_delay",
    "name": "Off delay",
    "type": "number",
    "minimum": 0,
    "maximum": 3600,
    "step": 1,
    "unit": "s",
    "device_class": "duration",
}


TARGET_TEMPERATURE = {
    "key": "target_temperature",
    "name": "Target temperature",
    "type": "number",
    "minimum": 5,
    "maximum": 30,
    "step": 0.5,
    "unit": "\u00b0C",
    "device_class": "temperature",
}
BOOST_DURATION = {
    "key": "boost_duration",
    "name": "Boost duration",
    "type": "number",
    "minimum": 0,
    "maximum": 120,
    "step": 5,
    "unit": "min",
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading of the custom integration in every test."""
    return None


def make_preset(
    title: str,
    parameters: Iterable[dict[str, Any]],
    *,
    subentry_id: str | None = PRESET_ID,
    blueprint: str | None = None,
) -> ConfigSubentryData:
    """Build the subentry data of one preset.

    With ``blueprint`` the preset follows one and has no parameters
    of its own, which is exactly how the flow stores it.
    """
    data: dict[str, Any] = (
        {CONF_BLUEPRINT: blueprint}
        if blueprint is not None
        else {CONF_PARAMETERS: list(parameters)}
    )
    subentry: dict[str, Any] = {
        "data": data,
        "subentry_type": SUBENTRY_TYPE_PRESET,
        "title": title,
        "unique_id": None,
    }
    if subentry_id is not None:
        subentry["subentry_id"] = subentry_id
    return ConfigSubentryData(**subentry)


def make_entry(
    *,
    title: str = "House Mode",
    modes: list[dict[str, Any]] | None = None,
    source_entity: str | None = None,
    conditions: dict[str, list[dict[str, Any]]] | None = None,
    presets: Iterable[ConfigSubentryData] | None = None,
    entry_id: str = PRESET_MODE_ID,
    version: int = ENTRY_VERSION,
    minor_version: int = ENTRY_MINOR_VERSION,
) -> MockConfigEntry:
    """Create the config entry of one preset mode.

    ``conditions`` maps a mode key to its conditions, for readability in the
    tests; they are stored on the mode itself.
    """
    items = [dict(item) for item in (modes if modes is not None else MODES)]
    for item in items:
        if conditions and conditions.get(item["key"]):
            item[CONF_CONDITIONS] = conditions[item["key"]]

    data: dict[str, Any] = {CONF_MODES: items}
    if source_entity is not None:
        data[CONF_SOURCE_ENTITY] = source_entity

    return MockConfigEntry(
        domain=DOMAIN,
        title=title,
        entry_id=entry_id,
        data=data,
        version=version,
        minor_version=minor_version,
        subentries_data=list(presets) if presets is not None else [],
    )


def make_blueprint(
    *,
    title: str = "Heating",
    parameters: Iterable[dict[str, Any]] | None = None,
    entry_id: str = BLUEPRINT_ID,
) -> MockConfigEntry:
    """Create the config entry of one blueprint."""
    items = parameters if parameters is not None else [TARGET_TEMPERATURE]
    return MockConfigEntry(
        domain=DOMAIN,
        title=title,
        entry_id=entry_id,
        data={
            CONF_ENTRY_TYPE: ENTRY_TYPE_BLUEPRINT,
            CONF_PARAMETERS: [dict(item) for item in items],
        },
        version=ENTRY_VERSION,
        minor_version=ENTRY_MINOR_VERSION,
    )


@pytest.fixture
async def motion_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Set up a manual preset mode with the "Motion Sensor Living Room" preset."""
    entry = make_entry(
        presets=[
            make_preset(
                "Motion Sensor Living Room",
                [BRIGHTNESS, COLOR_TEMPERATURE, OFF_DELAY],
            )
        ]
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
def subentry_id(motion_entry: MockConfigEntry) -> str:
    """Return the subentry id of the motion sensor preset."""
    return PRESET_ID


async def async_set_active_mode(
    hass: HomeAssistant, mode: str, *, entity_id: str = PRESET_MODE_SELECT
) -> None:
    """Call ``set_active_mode`` on a mode selector.

    The service is an entity service, so the preset mode is addressed by its
    selector rather than by its display name.
    """
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_ACTIVE_MODE,
        {"entity_id": entity_id, "mode": mode},
        blocking=True,
    )
