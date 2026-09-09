"""Tests for serving the dashboard card.

The card is committed as a built bundle and registered by the integration
itself, so there are two things to get wrong: shipping a release without the
build, and loading last week's card against this week's websocket command.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
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


async def test_leaves_a_headless_instance_alone(
    hass: HomeAssistant, urls: list[str]
) -> None:
    """No frontend, no card - and no failure to set the integration up."""
    assert "frontend" not in hass.config.components

    await frontend.async_register_card(hass)

    assert not urls
