"""Tests for serving the dashboard card.

The card is committed as a built bundle and registered by the integration
itself, so there are two things to get wrong: shipping a release without the
build, and loading last week's card against this week's websocket command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from homeassistant.components.lovelace import LovelaceData
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import (
    RESOURCE_STORAGE_KEY,
    ResourceStorageCollection,
    ResourceYAMLCollection,
)
from homeassistant.core import HomeAssistant

from custom_components.preset_manager import frontend
from custom_components.preset_manager.const import DOMAIN

BUNDLE = (
    Path(__file__).parent.parent
    / "custom_components"
    / "preset_manager"
    / "www"
    / frontend.CARD_FILENAME
)


class _Http:
    """Stand-in for ``hass.http``, which a bare test instance has not got."""

    def __init__(self) -> None:
        self.paths: list[Any] = []

    async def async_register_static_paths(self, configs: list[Any]) -> None:
        self.paths.extend(configs)


@pytest.fixture
def registered(hass: HomeAssistant, monkeypatch: pytest.MonkeyPatch) -> _Http:
    """Pretend this instance serves a frontend, and record what is registered."""
    hass.config.components.add("frontend")
    http = _Http()
    monkeypatch.setattr(hass, "http", http, raising=False)
    return http


@pytest.fixture
def urls(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the URLs handed to ``add_extra_js_url``."""
    collected: list[str] = []
    monkeypatch.setattr(
        frontend,
        "add_extra_js_url",
        lambda hass, url: collected.append(url),
    )
    return collected


@pytest.fixture
def lovelace(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> ResourceStorageCollection:
    """A real Lovelace resource collection, backed by an empty store."""
    hass_storage[RESOURCE_STORAGE_KEY] = {
        "version": 1,
        "key": RESOURCE_STORAGE_KEY,
        "data": {"items": []},
    }
    collection = ResourceStorageCollection(hass, None)
    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="storage",
        dashboards={},
        resources=collection,
        yaml_dashboards={},
    )
    return collection


def _urls(collection: ResourceStorageCollection) -> list[str]:
    return [item["url"] for item in collection.async_items()]


def test_the_built_bundle_is_committed() -> None:
    """A release without the build would ship an integration with no card."""
    assert BUNDLE.is_file()
    # Small enough to be a stub, and the CI build step would have caught it.
    assert BUNDLE.stat().st_size > 10_000
    assert "customCards" in BUNDLE.read_text(encoding="utf-8")


async def test_serves_the_bundle_and_loads_it(
    hass: HomeAssistant, registered: _Http, urls: list[str]
) -> None:
    """The folder is served and the card is added to every dashboard."""
    await frontend.async_register_card(hass)

    assert len(registered.paths) == 1
    path = registered.paths[0]
    assert path.url_path == frontend.URL_BASE
    assert Path(path.path) == BUNDLE.parent
    assert len(urls) == 1
    assert urls[0].startswith(f"{frontend.URL_BASE}/{frontend.CARD_FILENAME}?v=")


async def test_the_url_carries_the_version_of_the_integration(
    hass: HomeAssistant, registered: _Http, urls: list[str]
) -> None:
    """Without it a browser keeps a card older than the command it calls."""
    await frontend.async_register_card(hass)

    integration = await frontend.async_get_integration(hass, DOMAIN)
    assert urls[0].endswith(f"?v={integration.version}")


async def test_says_so_when_the_bundle_was_not_built(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """A source checkout: the integration works, the card is absent."""
    monkeypatch.setattr(frontend, "CARD_FILENAME", "not-built.js")

    await frontend.async_register_card(hass)

    assert not registered.paths
    assert not urls
    assert "not built" in caplog.text


async def test_says_where_the_card_was_registered(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The log has to answer "did it register, and under which URL".

    From the browser a card that never registered and a card that failed to
    load look the same: Home Assistant says "custom element not found" for
    both. This line is what tells them apart.
    """
    with caplog.at_level("INFO", logger="custom_components.preset_manager.frontend"):
        await frontend.async_register_card(hass)

    assert urls[0] in caplog.text


async def test_leaves_a_headless_instance_alone(
    hass: HomeAssistant, urls: list[str], caplog: pytest.LogCaptureFixture
) -> None:
    """No frontend, no card - and no failure to set the integration up."""
    assert "frontend" not in hass.config.components

    await frontend.async_register_card(hass)

    assert not urls
    # Silent would be wrong: the bundle is sitting right there unserved.
    assert "frontend integration is not set up" in caplog.text


async def test_adds_the_card_to_the_lovelace_resources(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    lovelace: ResourceStorageCollection,
) -> None:
    """The way every HACS card arrives, and the way this one has to as well.

    A resource is fetched by the frontend from its resource list at runtime,
    not from the page - which the service worker caches, once per browser and
    once per phone.
    """
    await frontend.async_register_card(hass)

    items = lovelace.async_items()
    assert len(items) == 1
    assert items[0]["type"] == "module"
    assert items[0]["url"].startswith(
        f"{frontend.URL_BASE}/{frontend.CARD_FILENAME}?v="
    )


async def test_brings_an_existing_entry_up_to_date(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    lovelace: ResourceStorageCollection,
) -> None:
    """A release changes the version in the URL, not the number of entries."""
    await lovelace.async_load()
    lovelace.loaded = True
    await lovelace.async_create_item(
        {
            "res_type": "module",
            "url": f"{frontend.URL_BASE}/{frontend.CARD_FILENAME}?v=0.0.1",
        }
    )

    await frontend.async_register_card(hass)

    assert len(lovelace.async_items()) == 1
    assert "0.0.1" not in _urls(lovelace)[0]


async def test_leaves_other_resources_alone(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    lovelace: ResourceStorageCollection,
) -> None:
    """The user's own cards are none of this integration's business."""
    await lovelace.async_load()
    lovelace.loaded = True
    await lovelace.async_create_item(
        {"res_type": "module", "url": "/hacsfiles/flower-card/flower-card.js"}
    )

    await frontend.async_register_card(hass)
    await frontend.async_remove_resource(hass)

    assert _urls(lovelace) == ["/hacsfiles/flower-card/flower-card.js"]


async def test_takes_the_resource_back_out(
    hass: HomeAssistant,
    registered: _Http,
    urls: list[str],
    lovelace: ResourceStorageCollection,
) -> None:
    """What setup added, removal takes away - no entry left pointing nowhere."""
    await frontend.async_register_card(hass)
    assert lovelace.async_items()

    await frontend.async_remove_resource(hass)

    assert lovelace.async_items() == []


async def test_adds_nothing_to_resources_declared_in_yaml(
    hass: HomeAssistant, registered: _Http, urls: list[str]
) -> None:
    """A YAML dashboard owns its resource list; the script tag still applies."""
    hass.data[LOVELACE_DATA] = LovelaceData(
        resource_mode="yaml",
        dashboards={},
        resources=ResourceYAMLCollection([]),
        yaml_dashboards={},
    )

    await frontend.async_register_card(hass)

    assert urls, "the script tag is what covers a YAML dashboard"


async def test_survives_lovelace_not_being_there(
    hass: HomeAssistant, registered: _Http, urls: list[str]
) -> None:
    """Registering the card must not depend on a dashboard existing."""
    assert LOVELACE_DATA not in hass.data

    await frontend.async_register_card(hass)

    assert urls
