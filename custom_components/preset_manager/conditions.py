"""Helpers for the condition based preset mode.

Home Assistant's condition validation turns ``value_template`` fields into
:class:`~homeassistant.helpers.template.Template` objects, which cannot be
stored in a config subentry (config entries have to stay JSON serialisable).
Conditions are therefore kept in their raw form and re-validated whenever the
integration is set up.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers import condition
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType

from .const import TIME_DEPENDENT_CONDITIONS

_LOGGER = logging.getLogger(__name__)


def to_storage(value: Any) -> Any:
    """Return a JSON serialisable copy of a validated condition config."""
    if isinstance(value, Template):
        return value.template
    if isinstance(value, Mapping):
        return {key: to_storage(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_storage(item) for item in value]
    return value


async def async_validate(
    hass: HomeAssistant, conditions: Sequence[ConfigType]
) -> list[ConfigType]:
    """Validate raw conditions and return the runtime configs.

    ``cv.CONDITIONS_SCHEMA`` has to run first: it is what turns a stored
    ``value_template`` string back into a :class:`Template`.
    ``async_validate_condition_config`` alone leaves it a string, and the
    condition would then fail at evaluation time.
    """
    schema_validated = cv.CONDITIONS_SCHEMA(list(conditions))
    return [
        await condition.async_validate_condition_config(hass, item)
        for item in schema_validated
    ]


async def async_build_checker(
    hass: HomeAssistant, conditions: Sequence[ConfigType]
) -> tuple[condition.ConditionCheckerTypeOptional | None, list[ConfigType]]:
    """Build a checker for a list of conditions.

    Returns the checker and the validated configs. ``None`` as the checker means
    "no conditions", which is treated as always true so that a mode without
    conditions acts as the catch-all at the end of the list.

    The checker itself may answer ``None`` - a condition that cannot decide -
    which is why ``sources.py`` runs its result through ``result_as_boolean``.
    Home Assistant has an alias for exactly that: ``ConditionCheckerType``
    promises a ``bool``, ``ConditionCheckerTypeOptional`` is what
    ``async_from_config`` actually returns.
    """
    if not conditions:
        return None, []
    validated = await async_validate(hass, conditions)
    checker = await condition.async_from_config(
        hass, {"condition": "and", "conditions": validated}
    )
    return checker, validated


def extract_entities(conditions: Iterable[ConfigType]) -> set[str]:
    """Return all entity ids referenced by the given validated conditions."""
    entities: set[str] = set()
    for item in conditions:
        try:
            entities |= condition.async_extract_entities(item)
        except Exception:
            _LOGGER.debug("Could not extract entities from %s", item)
    return entities


def extract_templates(conditions: Any) -> list[Template]:
    """Return every template used inside the given validated conditions.

    ``async_extract_entities`` cannot see through a template, so the entities a
    template condition depends on have to be tracked separately.
    """
    if isinstance(conditions, Template):
        return [conditions]
    if isinstance(conditions, Mapping):
        return [
            item for value in conditions.values() for item in extract_templates(value)
        ]
    if isinstance(conditions, (list, tuple, set)):
        return [item for value in conditions for item in extract_templates(value)]
    return []


def needs_time_refresh(conditions: Any) -> bool:
    """Return whether any condition has to be re-evaluated periodically.

    Time and sun conditions do not announce themselves through state changes.
    Templates are excluded on purpose: they are tracked separately, and Home
    Assistant's template tracking already handles ``now()``.
    """
    if isinstance(conditions, Mapping):
        if conditions.get("condition") in TIME_DEPENDENT_CONDITIONS:
            return True
        return any(needs_time_refresh(item) for item in conditions.values())
    if isinstance(conditions, (list, tuple, set)):
        return any(needs_time_refresh(item) for item in conditions)
    return False
