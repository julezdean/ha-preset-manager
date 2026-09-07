"""Sensor platform: active mode per preset mode and resolved values."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.event import async_track_time_change

from .const import (
    ATTR_AUTOMATIC,
    ATTR_BLUEPRINT,
    ATTR_MODE_KEY,
    ATTR_MODE_SOURCE,
    ATTR_MODES,
    ATTR_SOURCE_ENTITY,
    ATTR_VALUES,
    UID_ACTIVE_MODE,
    UID_PRESET_MODE_SENSOR,
)
from .coordinator import (
    PresetCoordinator,
    PresetModeConfigEntry,
    PresetModeCoordinator,
)
from .entity import (
    ParameterValueEntity,
    PresetEntity,
    PresetModeEntity,
)
from .models import ParameterDef
from .parameter_types import (
    TEMPORAL_TYPES,
    TYPE_TIME,
    as_timestamp,
    get_parameter_type,
    sensor_device_class,
    sensor_state_class,
)

#: Nothing on these platforms does I/O: a value is resolved in memory and
#: written to a debounced store, so there is no device to overwhelm and no
#: reason to serialise. Declared rather than left to the default, which would
#: quietly become 1 the day an entity here grew a synchronous update method.
PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant,
    entry: PresetModeConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the sensor entities of every preset mode and preset."""
    runtime = entry.runtime_data

    async_add_entities([ActiveModeSensor(runtime.preset_mode)])

    for subentry_id, coordinator in runtime.presets.items():
        entities: list[SensorEntity] = [PresetActiveModeSensor(coordinator)]
        entities.extend(
            ParameterValueSensor(coordinator, parameter)
            for parameter in coordinator.config.parameters
            if get_parameter_type(parameter.type).value_platform is Platform.SENSOR
        )
        async_add_entities(entities, config_subentry_id=subentry_id)


class ActiveModeSensor(PresetModeEntity, SensorEntity):
    """Shows the active mode of a preset mode.

    This entity exists in every preset mode, so automations and templates
    read the active mode the same way whether it is set by hand or computed.
    """

    _attr_translation_key = "mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _object_id_name = "mode"

    def __init__(self, preset_mode: PresetModeCoordinator) -> None:
        """Initialise the preset mode mode sensor."""
        super().__init__(preset_mode, UID_PRESET_MODE_SENSOR)
        self._attr_options = [mode.name for mode in preset_mode.modes]

    @property
    def native_value(self) -> str | None:
        """Return the name of the active mode."""
        mode = self.preset_mode.active_mode
        return mode.name if mode else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the preset mode and the source of the active mode."""
        config = self.preset_mode.config
        attributes: dict[str, Any] = {
            ATTR_MODE_KEY: self.preset_mode.active_mode_key,
            ATTR_MODES: [item.name for item in config.modes],
        }
        if config.source_entity is not None:
            # There is no automatic to report: the entity is the automatic.
            attributes[ATTR_SOURCE_ENTITY] = config.source_entity
        else:
            attributes[ATTR_AUTOMATIC] = self.preset_mode.automatic
        return attributes


class PresetActiveModeSensor(PresetEntity, SensorEntity):
    """Shows which mode is effective for this preset."""

    _attr_translation_key = "active_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    #: Not just "mode": a parameter a user calls "Mode" would otherwise want the
    #: same entity id and be pushed to a "_2" suffix.
    _object_id_name = "active_mode"

    def __init__(self, coordinator: PresetCoordinator) -> None:
        """Initialise the active mode sensor."""
        super().__init__(coordinator, UID_ACTIVE_MODE)
        self._attr_options = [mode.name for mode in coordinator.modes]

    @property
    def native_value(self) -> str | None:
        """Return the name of the effective mode."""
        return self.state_data.mode_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return details about the resolution of the mode."""
        state = self.state_data
        config = self.coordinator.config
        preset_mode = self.coordinator.preset_mode
        attributes: dict[str, Any] = {
            ATTR_MODE_KEY: state.mode_key,
            ATTR_MODE_SOURCE: preset_mode.config.name if preset_mode else None,
            ATTR_MODES: [mode.name for mode in self.coordinator.modes],
            ATTR_VALUES: {
                parameter.key: state.values.get(parameter.key)
                for parameter in config.parameters
            },
        }
        if config.blueprint is not None:
            # Where the parameters come from is not visible anywhere else on
            # the preset - its own parameter editor is closed while it follows
            # a set.
            entry = self.hass.config_entries.async_get_entry(config.blueprint)
            attributes[ATTR_BLUEPRINT] = entry.title if entry is not None else None
        return attributes


class ParameterValueSensor(ParameterValueEntity, SensorEntity):
    """Publishes the currently valid value of one parameter."""

    def __init__(self, coordinator: PresetCoordinator, parameter: ParameterDef) -> None:
        """Initialise the value sensor."""
        super().__init__(coordinator, parameter)
        self._attr_device_class = sensor_device_class(parameter)
        if self._attr_device_class is SensorDeviceClass.ENUM:
            self._attr_options = list(parameter.options)
        elif self._attr_device_class is not SensorDeviceClass.TIMESTAMP:
            self._attr_state_class = sensor_state_class(parameter)
            self._attr_native_unit_of_measurement = parameter.unit
            if get_parameter_type(parameter.type).numeric:
                self._attr_suggested_display_precision = parameter.display_precision

    async def async_added_to_hass(self) -> None:
        """Re-publish a time-of-day value when the day rolls over.

        A time has no date of its own, so the timestamp it resolves to points at
        today. Without this the sensor would keep yesterday's timestamp.
        """
        await super().async_added_to_hass()
        if self.parameter.type != TYPE_TIME:
            return
        self.async_on_remove(
            async_track_time_change(
                self.hass,
                self._async_day_changed,
                hour=0,
                minute=0,
                second=0,
            )
        )

    @callback
    def _async_day_changed(self, now: datetime) -> None:
        """Recompute the timestamp of a time-of-day value."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the resolved value."""
        value = self.resolved_value
        if self.parameter.type in TEMPORAL_TYPES:
            return as_timestamp(value, self.parameter.type)
        return value
