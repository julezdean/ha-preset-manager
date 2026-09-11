"""Fixtures for the Preset Manager tests."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

import pytest
from homeassistant.config_entries import ConfigSubentry, ConfigSubentryData
from homeassistant.core import HomeAssistant
from homeassistant.util.ulid import ulid_now
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.preset_manager.const import (
    CONF_BLUEPRINT,
    CONF_CONDITIONS,
    CONF_MODES,
    CONF_PARAMETERS,
    CONF_PRESET_MODE,
    CONF_SOURCE_ENTITY,
    DOMAIN,
    ENTRY_MINOR_VERSION,
    ENTRY_VERSION,
    HUB_BLUEPRINTS,
    HUB_PRESET_MODES,
    HUB_PRESETS,
    HUB_SUBENTRY_TYPES,
    HUB_TITLES,
    SERVICE_SET_ACTIVE_MODE,
)
from custom_components.preset_manager.coordinator import (
    PresetManagerRuntime,
    async_get_runtime,
)

#: Subentry id of the preset mode created by :func:`make_preset_mode`.
PRESET_MODE_ID = "11111111111111111111111111111111"
PRESET_ID = "0123456789abcdef0123456789abcdef"
#: Subentry id of the blueprint created by :func:`make_blueprint`.
BLUEPRINT_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"

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
    "unit": "°C",
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


def _subentry(
    kind: str, subentry_id: str | None, title: str, data: dict[str, Any]
) -> ConfigSubentryData:
    """Build the subentry data of one object."""
    subentry: dict[str, Any] = {
        "data": data,
        "subentry_type": HUB_SUBENTRY_TYPES[kind],
        "title": title,
        "unique_id": None,
    }
    if subentry_id is not None:
        subentry["subentry_id"] = subentry_id
    return ConfigSubentryData(**subentry)


def make_preset(
    title: str,
    parameters: Iterable[dict[str, Any]],
    *,
    subentry_id: str | None = PRESET_ID,
    blueprint: str | None = None,
    preset_mode: str | None = PRESET_MODE_ID,
    modes: list[dict[str, Any]] | None = None,
) -> ConfigSubentryData:
    """Build the subentry data of one preset.

    With ``blueprint`` the preset follows one and has no parameters of its own,
    which is exactly how the flow stores it. With ``preset_mode=None`` it
    follows no preset mode and carries ``modes`` of its own - the state a
    preset is left in when its preset mode is deleted.
    """
    data: dict[str, Any] = (
        {CONF_BLUEPRINT: blueprint}
        if blueprint is not None
        else {CONF_PARAMETERS: list(parameters)}
    )
    if preset_mode is not None:
        data[CONF_PRESET_MODE] = preset_mode
    if modes is not None:
        data[CONF_MODES] = [dict(item) for item in modes]
    return _subentry(HUB_PRESETS, subentry_id, title, data)


def make_preset_mode(
    *,
    title: str = "House Mode",
    modes: list[dict[str, Any]] | None = None,
    source_entity: str | None = None,
    conditions: dict[str, list[dict[str, Any]]] | None = None,
    subentry_id: str | None = PRESET_MODE_ID,
) -> ConfigSubentryData:
    """Build the subentry data of one preset mode.

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
    return _subentry(HUB_PRESET_MODES, subentry_id, title, data)


def make_blueprint(
    *,
    title: str = "Heating",
    parameters: Iterable[dict[str, Any]] | None = None,
    subentry_id: str | None = BLUEPRINT_ID,
) -> ConfigSubentryData:
    """Build the subentry data of one blueprint."""
    items = parameters if parameters is not None else [TARGET_TEMPERATURE]
    return _subentry(
        HUB_BLUEPRINTS,
        subentry_id,
        title,
        {CONF_PARAMETERS: [dict(item) for item in items]},
    )


def to_subentry(data: ConfigSubentryData) -> ConfigSubentry:
    """Turn subentry data into a subentry, for adding one to a live hub."""
    return ConfigSubentry(
        data=MappingProxyType(dict(data["data"])),
        subentry_id=data.get("subentry_id", ulid_now()),
        subentry_type=data["subentry_type"],
        title=data["title"],
        unique_id=data.get("unique_id"),
    )


def make_hub(
    kind: str,
    subentries: Iterable[ConfigSubentryData],
    *,
    version: int = ENTRY_VERSION,
    minor_version: int = ENTRY_MINOR_VERSION,
) -> MockConfigEntry:
    """Create the config entry of one hub."""
    return MockConfigEntry(
        domain=DOMAIN,
        title=HUB_TITLES[kind],
        unique_id=kind,
        data={},
        version=version,
        minor_version=minor_version,
        subentries_data=list(subentries),
    )


@dataclass
class Hubs:
    """The three config entries of a set up integration."""

    preset_modes: MockConfigEntry | None = None
    presets: MockConfigEntry | None = None
    blueprints: MockConfigEntry | None = None

    def entry(self, kind: str) -> MockConfigEntry:
        """Return one hub, which the test expects to exist."""
        hub = getattr(self, kind)
        assert hub is not None
        return hub

    @property
    def runtime(self) -> PresetManagerRuntime:
        """Return the runtime of the domain."""
        for hub in (self.preset_modes, self.presets, self.blueprints):
            if hub is not None:
                return hub.runtime_data
        raise AssertionError("nothing was set up")

    @property
    def preset_mode(self) -> Any:
        """Return the coordinator of the only preset mode."""
        return next(iter(self.runtime.preset_modes.values()))

    @property
    def preset(self) -> Any:
        """Return the coordinator of the only preset."""
        return next(iter(self.runtime.presets.values()))


async def async_setup_hubs(
    hass: HomeAssistant,
    *,
    preset_modes: Iterable[ConfigSubentryData] | None = None,
    presets: Iterable[ConfigSubentryData] | None = None,
    blueprints: Iterable[ConfigSubentryData] | None = None,
) -> Hubs:
    """Set up the hubs the test needs, in the order the integration expects."""
    hubs = Hubs()
    for kind, objects, attribute in (
        (HUB_PRESET_MODES, preset_modes, "preset_modes"),
        (HUB_BLUEPRINTS, blueprints, "blueprints"),
        (HUB_PRESETS, presets, "presets"),
    ):
        if objects is None:
            continue
        hub = make_hub(kind, objects)
        hub.add_to_hass(hass)
        assert await hass.config_entries.async_setup(hub.entry_id)
        await hass.async_block_till_done()
        setattr(hubs, attribute, hub)
    return hubs


async def async_add_object(
    hass: HomeAssistant, hubs: Hubs, kind: str, data: ConfigSubentryData
) -> None:
    """Add one object to a hub that is already set up."""
    hass.config_entries.async_add_subentry(hubs.entry(kind), to_subentry(data))
    await hass.async_block_till_done()


async def async_setup_one(
    hass: HomeAssistant,
    *,
    presets: Iterable[ConfigSubentryData] | None = None,
    blueprints: Iterable[ConfigSubentryData] | None = None,
    **preset_mode: Any,
) -> Hubs:
    """Set up one preset mode, with the presets that follow it."""
    return await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode(**preset_mode)],
        presets=presets,
        blueprints=blueprints,
    )


@pytest.fixture
async def motion(hass: HomeAssistant) -> Hubs:
    """Set up a manual preset mode with the "Motion Sensor Living Room" preset."""
    return await async_setup_hubs(
        hass,
        preset_modes=[make_preset_mode()],
        presets=[
            make_preset(
                "Motion Sensor Living Room",
                [BRIGHTNESS, COLOR_TEMPERATURE, OFF_DELAY],
            )
        ],
    )


@pytest.fixture
def subentry_id(motion: Hubs) -> str:
    """Return the subentry id of the motion sensor preset."""
    return PRESET_ID


def runtime_of(hass: HomeAssistant) -> PresetManagerRuntime:
    """Return the runtime of the domain."""
    runtime = async_get_runtime(hass)
    assert runtime is not None
    return runtime


async def async_activate_mode(
    hass: HomeAssistant, mode: str, *, subentry_id: str = PRESET_MODE_ID
) -> None:
    """Move a preset mode onto ``mode``.

    There is no service for this and no entity to write to: a preset mode gets
    its mode from its conditions or from the entity it follows. Tests that only
    need the dimension to be somewhere say so directly; the ones about *how* it
    gets there drive a source entity or a condition instead.
    """
    runtime_of(hass).preset_modes[subentry_id].async_apply_mode(mode)
    await hass.async_block_till_done()


async def async_set_preset_mode(hass: HomeAssistant, entity_id: str, mode: str) -> None:
    """Call ``set_active_mode`` on the selector of one preset.

    The one place the mode is set by hand, and only while that preset is not
    following its preset mode.
    """
    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_ACTIVE_MODE,
        {"entity_id": entity_id, "mode": mode},
        blocking=True,
    )
