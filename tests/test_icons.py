"""Tests for the icon translations.

Icons live in ``icons.json``, next to the names in ``strings.json`` and keyed
by the same ``translation_key``. Home Assistant resolves them in the frontend,
so nothing about them shows up in a state - which is exactly why they need
tests of their own: a typo or a missing entry is invisible from the states.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml
from homeassistant.core import HomeAssistant
from homeassistant.helpers import icon as icon_helper

from custom_components.preset_manager.const import DOMAIN

from .conftest import BRIGHTNESS, make_entry, make_preset

COMPONENT = Path(__file__).parent.parent / "custom_components" / DOMAIN


def _load(name: str) -> dict:
    return json.loads((COMPONENT / name).read_text())


def test_every_named_entity_has_an_icon() -> None:
    """An entity with a name but no icon falls back to a generic one.

    Both mode sensors used to do exactly that and showed ``mdi:eye``.
    """
    named = {
        (domain, key)
        for domain, entities in _load("strings.json")["entity"].items()
        for key in entities
    }
    with_icon = {
        (domain, key)
        for domain, entities in _load("icons.json")["entity"].items()
        for key in entities
    }
    assert named == with_icon


def test_every_service_has_an_icon() -> None:
    """A service without an icon shows a grey placeholder in the UI."""
    described = yaml.safe_load((COMPONENT / "services.yaml").read_text())
    assert set(described) == set(_load("icons.json")["services"])


@pytest.mark.parametrize("category", ["entity", "services"])
async def test_home_assistant_loads_the_icons(
    hass: HomeAssistant, category: str
) -> None:
    """The file has to be readable by Home Assistant, not just by json.load."""
    entry = make_entry(presets=[make_preset("Lamp", [BRIGHTNESS])])
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    icons = await icon_helper.async_get_icons(hass, category, integrations=[DOMAIN])
    assert icons[DOMAIN] == _load("icons.json")[category]


async def test_the_automatic_switch_has_an_icon_per_state(
    hass: HomeAssistant,
) -> None:
    """Off has to be distinguishable from on without reading the state."""
    automatic = _load("icons.json")["entity"]["switch"]["automatic"]
    assert automatic["default"] != automatic["state"]["off"]
