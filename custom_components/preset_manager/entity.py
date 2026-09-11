"""Shared entity base classes."""

from __future__ import annotations

from typing import Any

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity import Entity, EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    UID_ACTIVE_MODE,
    UID_AUTOMATIC,
    UID_CONFIG,
    UID_MODE_SELECTION,
    UID_PRESET_MODE_SENSOR,
    UID_SEPARATOR,
    UID_VALUE,
)
from .coordinator import (
    PresetCoordinator,
    PresetManagerRuntime,
    PresetModeCoordinator,
    PresetState,
)
from .models import ModeDef, ParameterDef
from .parameter_types import get_parameter_type

MANUFACTURER = "Preset Mode"
MODEL_PRESET_MODE = "Preset mode"
MODEL_PRESET = "Preset"


class StableObjectIdMixin(Entity):
    """Keeps the entity id independent of the Home Assistant UI language.

    Entities whose name comes from a translation key would otherwise get a
    localised entity id (``sensor.<device>_profil`` on a Germa preset,
    ``sensor.<device>_mode`` on an English one). Home Assistant derives the
    object id from :attr:`suggested_object_id`, so returning a fixed English
    name here gives a stable, English entity id while ``name`` stays translated.
    """

    #: English name used for the entity id; ``None`` keeps the default.
    #: Derived from ``Entity`` so that ``super().suggested_object_id`` has
    #: something to resolve to - the mixin is only ever mixed into entities,
    #: and without a base a type checker cannot see that.
    _object_id_name: str | None = None

    @property
    def suggested_object_id(self) -> str | None:
        """Return the language independent base of the entity id."""
        if self._object_id_name is not None:
            return self._object_id_name
        return super().suggested_object_id


def preset_mode_device_info(preset_mode: PresetModeCoordinator) -> DeviceInfo:
    """Return the device of a preset mode."""
    return DeviceInfo(
        identifiers={(DOMAIN, preset_mode.config.subentry_id)},
        name=preset_mode.config.name,
        manufacturer=MANUFACTURER,
        model=MODEL_PRESET_MODE,
        entry_type=DeviceEntryType.SERVICE,
    )


class PresetModeEntity(StableObjectIdMixin, CoordinatorEntity[PresetModeCoordinator]):
    """Base class for entities that belong to a preset mode device."""

    _attr_has_entity_name = True

    def __init__(self, preset_mode: PresetModeCoordinator, key: str) -> None:
        """Initialise the preset mode entity."""
        super().__init__(preset_mode)
        self._attr_unique_id = f"{preset_mode.config.subentry_id}_{key}"
        self._attr_device_info = preset_mode_device_info(preset_mode)

    @property
    def preset_mode(self) -> PresetModeCoordinator:
        """Return the preset mode."""
        return self.coordinator


class PresetEntity(StableObjectIdMixin, CoordinatorEntity[PresetCoordinator]):
    """Base class for entities that belong to one preset device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: PresetCoordinator, key: str) -> None:
        """Initialise the preset entity."""
        super().__init__(coordinator)
        subentry_id = coordinator.config.subentry_id
        self._attr_unique_id = f"{subentry_id}_{key}"
        # No ``via_device``: a preset is not part of its preset mode, it
        # follows one - it outlives its deletion, it may have none at all, and
        # the two live in different hubs that are set up in either order. A
        # device pointing at one that is not there yet is a warning today and
        # an error in a coming Home Assistant version.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, subentry_id)},
            name=coordinator.config.name,
            manufacturer=MANUFACTURER,
            model=MODEL_PRESET,
        )

    @property
    def state_data(self) -> PresetState:
        """Return the resolved state of the preset."""
        return self.coordinator.data


class ParameterValueEntity(PresetEntity):
    """Base class for the entity exposing the currently valid value."""

    def __init__(self, coordinator: PresetCoordinator, parameter: ParameterDef) -> None:
        """Initialise the value entity."""
        super().__init__(coordinator, f"{UID_VALUE}_{parameter.key}")
        self.parameter = parameter
        self._attr_name = parameter.name
        self._attr_icon = parameter.icon

    @property
    def resolved_value(self) -> Any:
        """Return the value of the parameter in the effective mode."""
        return self.state_data.values.get(self.parameter.key)


class ModeValueEditorEntity(PresetEntity):
    """Base class for the per mode editor entities.

    These are configuration entities: they write into the value store instead of
    controlling a device.
    """

    _attr_entity_category = EntityCategory.CONFIG

    def __init__(
        self,
        coordinator: PresetCoordinator,
        mode: ModeDef,
        parameter: ParameterDef,
    ) -> None:
        """Initialise the editor entity."""
        super().__init__(
            coordinator, f"{UID_CONFIG}_{mode.key}{UID_SEPARATOR}{parameter.key}"
        )
        self.mode_def = mode
        self.parameter = parameter
        self._attr_name = f"{mode.name} {parameter.name}"
        self._attr_icon = parameter.icon

    async def async_added_to_hass(self) -> None:
        """Subscribe to changes of this one stored value."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self.coordinator.async_add_raw_listener(
                self.mode_def.key, self.parameter.key, self.async_write_ha_state
            )
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Ignore the resolved state of the preset.

        An editor shows the value stored for its own mode, which does not
        depend on which mode is active or on what that mode resolves to. Taking
        the push would rewrite the state of every editor of the preset whenever
        a value of the *active* mode changed - with five parameters over four
        modes, 19 of those 20 writes carry the value the entity already had.
        The raw listener above is the only signal this entity needs.
        """

    @property
    def raw_value(self) -> Any:
        """Return the configured value of this mode/parameter combination."""
        return self.coordinator.get_raw_value(self.mode_def.key, self.parameter)

    def _write_value(self, value: Any) -> None:
        """Persist a new value.

        The state is written by the raw listener of this very entity, so
        writing it here as well only wrote it twice.
        """
        self.coordinator.async_set_value(self.mode_def.key, self.parameter.key, value)


@callback
def async_expected_preset_mode_ids(runtime: PresetManagerRuntime) -> set[str]:
    """Return every unique id the loaded preset modes produce.

    This is the single source of truth for "which entities may exist": the
    platforms build their entities from the same suffix constants, and
    ``_async_remove_stale_entities`` cleans up against this set. Spelling the
    suffixes out in both places is what let them disagree about the active
    mode sensor of a preset, which was then removed and restored on every
    single setup.
    """
    # One entity, and only one: a preset mode says which mode is active and
    # is not operated. Everything a hand reaches sits on the presets.
    return {
        f"{subentry_id}_{UID_PRESET_MODE_SENSOR}"
        for subentry_id in runtime.preset_modes
    }


@callback
def async_expected_preset_ids(runtime: PresetManagerRuntime) -> set[str]:
    """Return every unique id the loaded presets produce."""
    expected: set[str] = set()
    for subentry_id, coordinator in runtime.presets.items():
        expected.add(f"{subentry_id}_{UID_ACTIVE_MODE}")
        # Both exist on every preset, whatever its preset mode can do: the
        # automatic switched here is the one between preset and dimension.
        expected.add(f"{subentry_id}_{UID_MODE_SELECTION}")
        expected.add(f"{subentry_id}_{UID_AUTOMATIC}")
        for parameter in coordinator.config.parameters:
            expected.add(f"{subentry_id}_{UID_VALUE}_{parameter.key}")
            if get_parameter_type(parameter.type).editor_platform is None:
                continue
            for mode in coordinator.modes:
                expected.add(
                    f"{subentry_id}_{UID_CONFIG}_{mode.key}"
                    f"{UID_SEPARATOR}{parameter.key}"
                )
    return expected
