"""Services of the Preset Mode.

Only the operations that cannot be expressed with the entities themselves are
implemented as services:

* ``set_active_mode`` accepts a stable mode *key* (the select entity only
  works with the localised display name). It is an **entity service** on that
  very selector, so it is targeted the way every other service in Home
  Assistant is,
* ``set_value`` writes a value without going through the editor entities,
* ``get_values`` returns all values of a preset as a service response.

Both value services take a standard ``target``: a preset is addressed by its
device, its entities, its area, floor or label - never by its display name.
A name is the user's own text and is meant to stay changeable; a service that
resolved it would have frozen it after all, because renaming a preset would
then silently break other people's scripts.

Creating, renaming or deleting modes/parameters is configuration and is done
in the config/options flows, not through services.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.core import (
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
    SupportsResponse,
    callback,
)
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers import target as target_helper

from .blueprints import is_blueprint
from .const import (
    ATTR_MODE,
    ATTR_PARAMETER,
    ATTR_PRESET,
    ATTR_VALUE,
    ATTR_VALUES,
    DOMAIN,
    SERVICE_GET_VALUES,
    SERVICE_SET_VALUE,
)
from .coordinator import PresetCoordinator, PresetModeRuntime


def _scalar(value: Any) -> Any:
    """Return ``value`` untouched, rejecting containers.

    Which type a value has to fit is only known once the parameter behind it is
    resolved, and ``coerce_value`` does exactly that. Coercing here instead
    turned ``"15"`` into ``15.0``, which stored ``"15.0"`` in a text parameter
    and made every select parameter with numeric options unreachable.
    """
    if isinstance(value, (list, dict, set, tuple)):
        raise vol.Invalid("value has to be a single value, not a list")
    return value


SET_VALUE_SCHEMA = vol.Schema(
    {
        **cv.TARGET_SERVICE_FIELDS,
        vol.Required(ATTR_MODE): cv.string,
        vol.Required(ATTR_PARAMETER): cv.string,
        vol.Required(ATTR_VALUE): _scalar,
    }
)

GET_VALUES_SCHEMA = vol.Schema(
    {**cv.TARGET_SERVICE_FIELDS, vol.Optional(ATTR_MODE): cv.string}
)


def _runtimes(hass: HomeAssistant) -> list[PresetModeRuntime]:
    """Return the runtime of every loaded preset mode."""
    entries = [
        entry
        for entry in hass.config_entries.async_loaded_entries(DOMAIN)
        # A blueprint is a config entry of this domain as well, but it has
        # no runtime: it is configuration for the presets following it, and
        # there is nothing about it a service could address.
        if not is_blueprint(entry)
    ]
    if not entries:
        raise ServiceValidationError(
            translation_domain=DOMAIN, translation_key="not_loaded"
        )
    return [entry.runtime_data for entry in entries]


def _all_presets(hass: HomeAssistant) -> dict[str, PresetCoordinator]:
    """Return every preset of every loaded preset mode, keyed by subentry id."""
    return {
        preset_id: coordinator
        for runtime in _runtimes(hass)
        for preset_id, coordinator in runtime.presets.items()
    }


def _resolve_presets(hass: HomeAssistant, call: ServiceCall) -> list[PresetCoordinator]:
    """Resolve the presets a service call targets.

    Home Assistant expands areas, floors and labels down to devices and
    entities for us, so every way of picking a preset ends up here.
    """
    presets = _all_presets(hass)
    selection = target_helper.TargetSelection(call.data)
    selected = target_helper.async_extract_referenced_entity_ids(hass, selection)
    found: dict[str, PresetCoordinator] = {}

    # A device picked directly resolves even when all of its entities are
    # disabled - the preset is its device, not its entities.
    device_registry = dr.async_get(hass)
    for device_id in selected.referenced_devices:
        device = device_registry.async_get(device_id)
        if device is None:
            continue
        for domain, identifier in device.identifiers:
            if domain == DOMAIN and identifier in presets:
                found[identifier] = presets[identifier]

    entity_registry = er.async_get(hass)
    for entity_id in selected.referenced | selected.indirectly_referenced:
        entity = entity_registry.async_get(entity_id)
        if entity is None or entity.platform != DOMAIN:
            continue
        # Only the entities of a preset carry a subentry; the entities of the
        # preset mode itself carry none and address no preset.
        subentry_id = entity.config_subentry_id
        if subentry_id is not None and (preset := presets.get(subentry_id)) is not None:
            found[subentry_id] = preset

    if not found:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_preset",
            translation_placeholders={
                "presets": ", ".join(
                    coordinator.config.name for coordinator in presets.values()
                )
            },
        )
    return list(found.values())


def _resolve_mode(coordinator: PresetCoordinator, raw_mode: str) -> str:
    """Return the mode key ``raw_mode`` names for one preset."""
    mode = coordinator.preset_mode.resolve_mode(raw_mode)
    if mode is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="unsupported_mode",
            translation_placeholders={
                "mode": raw_mode,
                "preset": coordinator.config.name,
                "modes": ", ".join(item.name for item in coordinator.modes),
            },
        )
    return mode.key


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register the services of the integration.

    ``set_active_mode`` is not here: it belongs to the mode selector and is
    registered as an entity service by the select platform.
    """

    async def async_set_value(call: ServiceCall) -> None:
        """Set a value of a mode."""
        raw_mode = call.data[ATTR_MODE]
        # Every target is resolved before the first write: a call either
        # applies everywhere or nowhere, never half, so a mode that one of
        # several targeted presets does not know cannot leave the others
        # written and the user with a partial result and an error.
        targets = [
            (coordinator, _resolve_mode(coordinator, raw_mode))
            for coordinator in _resolve_presets(hass, call)
        ]
        for coordinator, mode_key in targets:
            coordinator.async_set_value(
                mode_key, call.data[ATTR_PARAMETER], call.data[ATTR_VALUE]
            )

    async def async_get_values(call: ServiceCall) -> ServiceResponse:
        """Return the values of a preset."""
        presets = _resolve_presets(hass, call)
        if len(presets) != 1:
            raise ServiceValidationError(
                translation_domain=DOMAIN, translation_key="single_preset_required"
            )
        coordinator = presets[0]
        mode_key: str | None
        if raw_mode := call.data.get(ATTR_MODE):
            # Never None here - _resolve_mode raises instead.
            requested = _resolve_mode(coordinator, raw_mode)
            values: dict[str, Any] = {
                parameter.key: coordinator.get_raw_value(requested, parameter)
                for parameter in coordinator.config.parameters
            }
            mode_key = requested
        else:
            state = coordinator.data
            values = dict(state.values)
            mode_key = state.mode_key

        return {
            ATTR_PRESET: coordinator.config.name,
            ATTR_MODE: mode_key,
            ATTR_VALUES: values,
        }

    hass.services.async_register(
        DOMAIN, SERVICE_SET_VALUE, async_set_value, schema=SET_VALUE_SCHEMA
    )
    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_VALUES,
        async_get_values,
        schema=GET_VALUES_SCHEMA,
        supports_response=SupportsResponse.ONLY,
    )
