"""Determines the active mode of a preset mode.

A preset mode that names a source entity is driven entirely from outside: the state
of that entity is the mode, and nothing else is evaluated. Otherwise the
preset mode runs on its own as soon as at least one of its modes has
conditions. The modes are then checked from top to bottom and the first one
whose conditions match becomes active. A mode without conditions always
matches, so it catches everything below it - that is how a preset mode gets a
fallback mode, at the position the user put it. If nothing matches, no
mode is active. A preset_mode whose modes have no conditions at all is purely
manual.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import CALLBACK_TYPE, Event, EventStateChangedData, callback
from homeassistant.helpers.event import (
    TrackTemplate,
    async_track_state_change_event,
    async_track_template_result,
    async_track_time_change,
)
from homeassistant.helpers.template import result_as_boolean
from homeassistant.helpers.typing import ConfigType

from . import conditions as condition_helper

if TYPE_CHECKING:
    from .coordinator import PresetModeCoordinator

_LOGGER = logging.getLogger(__name__)


class ModeSource:
    """Base class of a mode source.

    The default implementation is the manual one: it neither evaluates nor
    subscribes to anything.
    """

    def __init__(self, preset_mode: PresetModeCoordinator) -> None:
        """Initialise the source."""
        self.preset_mode = preset_mode
        self._unsubscribes: list[CALLBACK_TYPE] = []

    async def async_start(self) -> None:
        """Evaluate once and subscribe to future changes."""

    async def async_refresh(self) -> None:
        """Evaluate again on demand, e.g. when automatic is switched back on."""

    @callback
    def async_stop(self) -> None:
        """Release all subscriptions."""
        while self._unsubscribes:
            self._unsubscribes.pop()()


class ManualSource(ModeSource):
    """The mode is set by the user through the select entity."""


class EntitySource(ModeSource):
    """The state of another entity names the active mode.

    Anything the entity says is resolved against the modes by key, display
    name or slug; a state that matches nothing - and `unknown`/`unavailable`
    alike - leaves the preset mode without an active mode. This source is not
    switchable: a preset mode that follows an entity has no automatic switch and no
    selector, so there is nothing to be off.
    """

    @property
    def _entity_id(self) -> str:
        return self.preset_mode.config.source_entity or ""

    async def async_start(self) -> None:
        """Read the entity once and follow it from then on."""
        self._unsubscribes.append(
            async_track_state_change_event(
                self.preset_mode.hass, [self._entity_id], self._handle_change
            )
        )
        self._evaluate()

    async def async_refresh(self) -> None:
        """Read the entity again."""
        self._evaluate()

    @callback
    def _handle_change(self, event: Event[EventStateChangedData]) -> None:
        self._evaluate()

    @callback
    def _evaluate(self) -> None:
        """Map the state of the entity onto a mode."""
        state = self.preset_mode.hass.states.get(self._entity_id)
        if state is None or state.state in (STATE_UNKNOWN, STATE_UNAVAILABLE):
            self.preset_mode.async_apply_from_source(None)
            return
        mode = self.preset_mode.resolve_mode(state.state)
        if mode is None:
            _LOGGER.warning(
                "'%s' is %s, which is not a mode of '%s'. Known modes: %s",
                self._entity_id,
                state.state,
                self.preset_mode.config.name,
                ", ".join(item.name for item in self.preset_mode.modes),
            )
            self.preset_mode.async_apply_from_source(None)
            return
        self.preset_mode.async_apply_from_source(mode.key)


class ConditionSource(ModeSource):
    """The first mode whose conditions match becomes active."""

    def __init__(self, preset_mode: PresetModeCoordinator) -> None:
        """Initialise the condition source."""
        super().__init__(preset_mode)
        #: Mode key -> checker; ``None`` is a mode without conditions,
        #: which always matches.
        self._checkers: list[tuple[str, Any]] = []

    async def async_start(self) -> None:
        """Build the checkers and subscribe to everything they reference."""
        config = self.preset_mode.config
        validated: list[ConfigType] = []
        for mode in config.modes:
            if not mode.conditions:
                # No conditions: this mode catches everything below it.
                self._checkers.append((mode.key, None))
                continue
            try:
                checker, configs = await condition_helper.async_build_checker(
                    self.preset_mode.hass, mode.conditions
                )
            except Exception as err:
                _LOGGER.error(
                    "Conditions of mode '%s' in '%s' are invalid and will be "
                    "ignored: %s",
                    mode.name,
                    config.name,
                    err,
                )
                continue
            self._checkers.append((mode.key, checker))
            validated.extend(configs)

        if entities := condition_helper.extract_entities(validated):
            self._unsubscribes.append(
                async_track_state_change_event(
                    self.preset_mode.hass, sorted(entities), self._handle_change
                )
            )
        if templates := condition_helper.extract_templates(validated):
            info = async_track_template_result(
                self.preset_mode.hass,
                [TrackTemplate(template, None) for template in templates],
                self._handle_template,
            )
            self._unsubscribes.append(info.async_remove)
            info.async_refresh()
        if condition_helper.needs_time_refresh(validated):
            self._unsubscribes.append(
                async_track_time_change(
                    self.preset_mode.hass, self._handle_time, second=0
                )
            )
        self._evaluate()

    async def async_refresh(self) -> None:
        """Evaluate the conditions again."""
        self._evaluate()

    @callback
    def _handle_change(self, event: Event[EventStateChangedData]) -> None:
        self._evaluate()

    @callback
    def _handle_time(self, now: datetime) -> None:
        self._evaluate()

    @callback
    def _handle_template(
        self, event: Event[EventStateChangedData] | None, updates: list[Any]
    ) -> None:
        self._evaluate()

    @callback
    def _evaluate(self) -> None:
        """Activate the first mode whose conditions match."""
        hass = self.preset_mode.hass
        for mode_key, checker in self._checkers:
            if checker is None:
                # A mode without conditions catches everything below it.
                self.preset_mode.async_apply_from_source(mode_key)
                return
            try:
                matched = result_as_boolean(checker(hass, {}))
            except Exception as err:
                _LOGGER.warning(
                    "Conditions of mode '%s' in '%s' failed: %s",
                    mode_key,
                    self.preset_mode.config.name,
                    err,
                )
                continue
            if matched:
                self.preset_mode.async_apply_from_source(mode_key)
                return
        # Nothing matched and nothing caught it: no mode is active.
        self.preset_mode.async_apply_from_source(None)


def create_source(preset_mode: PresetModeCoordinator) -> ModeSource:
    """Return the source matching the configuration of ``preset_mode``."""
    if preset_mode.config.is_external:
        return EntitySource(preset_mode)
    if preset_mode.config.has_conditions:
        return ConditionSource(preset_mode)
    return ManualSource(preset_mode)
