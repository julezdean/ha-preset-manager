"""Serves the dashboard card that ships with the integration.

The card is built from ``frontend/`` and committed as a single bundle next to
this file. It is registered here rather than installed separately, which is
what keeps the two from ever drifting apart: HACS knows one category per
repository, so a second repository for the card would be a second version
number, a second install step and a second thing to keep in step with the
websocket command it talks to. Shipped this way, a user cannot have one
without the other.

**It is offered twice, on purpose**, because the two ways Home Assistant loads
frontend code fail in different situations:

* ``add_extra_js_url`` puts a ``<script>`` into the Home Assistant page. It
  needs nothing from the user's configuration - and it lives in the page, which
  the service worker caches. A client holding a copy from before the card
  existed keeps serving it, across restarts of Home Assistant and past a hard
  reload, once per browser and once per phone. That is not a theory: it is what
  happened, on two clients, and it is indistinguishable from a broken card.
* A **Lovelace resource** is fetched by the frontend at runtime from the
  resource list, not from the cached page, so it is immune to that. It is how
  every card installed through HACS arrives, which is why those kept working
  while this one did not. The cost is a line in the user's Lovelace resources,
  which this module keeps up to date and removes with the last hub.

Both name the same URL, so the browser fetches the module once either way and
whichever arrives first defines the element. Together they also cover the case
neither covers alone: a dashboard in YAML mode declares its resources in YAML
and refuses to be written to, and there ``add_extra_js_url`` is the only way in.

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
from typing import Any

from homeassistant.components.frontend import add_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.lovelace.const import LOVELACE_DATA
from homeassistant.components.lovelace.resources import ResourceStorageCollection
from homeassistant.core import HomeAssistant
from homeassistant.loader import async_get_integration

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

#: Where the bundle is served from. Not under ``/local``: that is the user's
#: own ``www`` folder and nothing of ours belongs in it.
URL_BASE = f"/{DOMAIN}/frontend"
CARD_FILENAME = "preset-manager-card.js"


async def async_register_card(hass: HomeAssistant) -> None:
    """Serve the card bundle and load it into every dashboard.

    Every path out of here says which one it took. A card that does not appear
    is diagnosed from the browser, where the only symptom is Home Assistant's
    own "custom element not found" - it cannot tell "never registered" from
    "registered and failed to load", and neither can the person reading it. One
    line in the log tells the two apart, so it is worth the line.
    """
    bundle = Path(__file__).parent / "www" / CARD_FILENAME

    if not bundle.is_file():
        # A source checkout without a build step, or an install that did not
        # bring the folder. The integration itself works in full.
        _LOGGER.warning(
            "The dashboard card is not built: %s is missing, so the card is "
            "not available. The rest of the integration works without it",
            bundle,
        )
        return

    if "frontend" not in hass.config.components:
        # A headless instance has no dashboards and no use for a card. That the
        # bundle is right here and still goes unserved is unusual enough to say
        # out loud rather than hide at debug level.
        _LOGGER.warning(
            "The frontend integration is not set up, so the dashboard card is "
            "not registered"
        )
        return

    await hass.http.async_register_static_paths(
        [StaticPathConfig(URL_BASE, str(bundle.parent), False)]
    )

    integration = await async_get_integration(hass, DOMAIN)
    # The version turns an upgrade into a different URL. Without it a browser
    # would keep last week's card against this week's websocket command.
    url = f"{URL_BASE}/{CARD_FILENAME}?v={integration.version}"
    add_extra_js_url(hass, url)
    await _async_register_resource(hass, url)
    _LOGGER.info("Dashboard card registered at %s", url)


async def _async_resources(
    hass: HomeAssistant,
) -> ResourceStorageCollection | None:
    """Return the Lovelace resources, if they can be written to."""
    if (lovelace := hass.data.get(LOVELACE_DATA)) is None:
        return None
    resources = lovelace.resources
    if not isinstance(resources, ResourceStorageCollection):
        # A dashboard in YAML mode declares its resources in YAML. Nothing to
        # add there, and nothing broken either - the script tag still applies.
        return None
    if not resources.loaded:
        await resources.async_load()
        resources.loaded = True
    return resources


def _is_ours(resource: dict[str, Any]) -> bool:
    """Return whether a resource is the card, at whatever version."""
    url = resource.get("url")
    return isinstance(url, str) and url.startswith(f"{URL_BASE}/{CARD_FILENAME}")


async def _async_register_resource(hass: HomeAssistant, url: str) -> None:
    """Add the card to the Lovelace resources, or bring the entry up to date.

    Matched by path rather than by the whole URL: the version in the query
    string changes with every release, and a new entry per release would leave
    the user with a list of dead ones.
    """
    resources = await _async_resources(hass)
    if resources is None:
        _LOGGER.debug("No writable Lovelace resources; the script tag stands alone")
        return

    existing = next((item for item in resources.async_items() if _is_ours(item)), None)
    if existing is None:
        await resources.async_create_item({"res_type": "module", "url": url})
        _LOGGER.debug("Added the card to the Lovelace resources")
        return
    if existing.get("url") != url:
        await resources.async_update_item(existing["id"], {"url": url})
        _LOGGER.debug("Updated the Lovelace resource of the card to %s", url)


async def async_remove_resource(hass: HomeAssistant) -> None:
    """Take the card out of the Lovelace resources again.

    Called when the last hub is removed: what this module added on setup it
    takes away on removal, so uninstalling leaves no entry pointing at a path
    nothing serves any more.
    """
    resources = await _async_resources(hass)
    if resources is None:
        return
    for item in list(resources.async_items()):
        if _is_ours(item):
            await resources.async_delete_item(item["id"])
            _LOGGER.debug("Removed the Lovelace resource of the card")
