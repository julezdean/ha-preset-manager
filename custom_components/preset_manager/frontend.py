"""Serves the dashboard card that ships with the integration.

The card is built from ``frontend/`` and committed as a single bundle next to
this file. It is registered here rather than installed separately, which is
what keeps the two from ever drifting apart: HACS knows one category per
repository, so a second repository for the card would be a second version
number, a second install step and a second thing to keep in step with the
websocket command it talks to. Shipped this way, a user cannot have one
without the other.

``add_extra_js_url`` loads it for every dashboard, the way a resource added by
hand would - so the card is available without the user adding a resource, and
without this integration writing into their Lovelace configuration.

``frontend`` is an *after* dependency rather than a real one. A Home Assistant
that serves a dashboard has it, and then the ordering is what this needs; one
that does not is a headless instance where the integration itself works exactly
as before and only the card is beside the point. Making it a hard dependency
would instead mean this integration could not be set up at all without the
frontend package installed.
"""

from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

#: Where the bundle is served from. Not under ``/local``: that is the user's
#: own ``www`` folder and nothing of ours belongs in it.
URL_BASE = f"/{DOMAIN}/frontend"
CARD_FILENAME = "preset-manager-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card bundle and load it into every dashboard."""
    if "frontend" not in hass.config.components:
        _LOGGER.debug("No frontend on this instance; the card is not registered")
        return

    folder = Path(__file__).parent / "www"
    if not (folder / CARD_FILENAME).is_file():
        # A source checkout without a build step. The integration itself works
        # in full; only the card is missing, and saying so beats a 404 in the
        # browser console of a dashboard that never mentions this.
        _LOGGER.warning(
            "The dashboard card is not built; %s is missing. The integration "
            "works without it",
            folder / CARD_FILENAME,
        )
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(folder), False)]
    )

    integration = await async_get_integration(hass, DOMAIN)
    # The version turns an upgrade into a different URL. Without it a browser
    # would keep last week's card against this week's websocket command.
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILENAME}?v={integration.version}")
