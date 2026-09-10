"""Constants for the Preset Manager integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "preset_manager"

# Config entry / subentry structure -------------------------------------------------

#: The integration owns exactly three config entries, one per kind of object,
#: and every object is a subentry of the hub that collects its kind. What an
#: entry is stands in its ``unique_id``: it is the only field Home Assistant
#: keeps unique per domain for us, so "there is one hub of each kind" is
#: enforced by the config flow rather than by our own bookkeeping.
HUB_PRESET_MODES: Final = "preset_modes"
HUB_PRESETS: Final = "presets"
HUB_BLUEPRINTS: Final = "blueprints"

#: A preset mode: a set of modes plus the rule picking the active one.
SUBENTRY_TYPE_PRESET_MODE: Final = "preset_mode"
#: A preset: the parameters of one device, with one value per mode.
SUBENTRY_TYPE_PRESET: Final = "preset"
#: A blueprint: parameter definitions shared by any number of presets.
SUBENTRY_TYPE_BLUEPRINT: Final = "blueprint"

#: The one subentry type each hub holds, and the title it is created with.
#: Titles are stored strings, not translations - the user may rename a hub,
#: and renaming it back is not our business.
HUB_SUBENTRY_TYPES: Final[dict[str, str]] = {
    HUB_PRESET_MODES: SUBENTRY_TYPE_PRESET_MODE,
    HUB_PRESETS: SUBENTRY_TYPE_PRESET,
    HUB_BLUEPRINTS: SUBENTRY_TYPE_BLUEPRINT,
}
HUB_TITLES: Final[dict[str, str]] = {
    HUB_PRESET_MODES: "Preset Modes",
    HUB_PRESETS: "Presets",
    HUB_BLUEPRINTS: "Preset Blueprints",
}

# Preset mode (config entry) keys
CONF_MODES: Final = "modes"
#: Conditions of a mode; the first mode whose conditions match wins.
CONF_CONDITIONS: Final = "conditions"
#: An entity whose state names the active mode. Set it and the preset mode is
#: driven entirely from outside: no conditions, no automatic, no selector.
CONF_SOURCE_ENTITY: Final = "source_entity"

#: Condition types that cannot announce themselves through state changes and
#: therefore need a periodic re-evaluation.
TIME_DEPENDENT_CONDITIONS: Final = frozenset({"time", "sun"})
CONF_MODE: Final = "mode"

# Mode definition keys
CONF_KEY: Final = "key"
CONF_NAME: Final = "name"
CONF_ICON: Final = "icon"

# Preset (subentry) keys
#: Subentry id of the preset mode a preset follows, or absent while it follows
#: none. A preset is not contained in its preset mode: it survives the deletion
#: of one and waits to be assigned another.
CONF_PRESET_MODE: Final = "preset_mode"
CONF_PARAMETERS: Final = "parameters"
#: The presets following one preset mode or one blueprint, in the step that
#: edits the same reference from the other side.
CONF_PRESETS: Final = "presets"
#: Subentry id of the blueprint a preset follows. While it is set the preset
#: has no parameters of its own: they are resolved from the blueprint on every setup,
#: and its parameter editor stays closed.
CONF_BLUEPRINT: Final = "blueprint"

#: Name of the copy in the duplicate step of every object.
CONF_COPY_NAME: Final = "copy_name"

# Parameter definition keys
CONF_TYPE: Final = "type"
CONF_MIN: Final = "minimum"
CONF_MAX: Final = "maximum"
CONF_STEP: Final = "step"
CONF_UNIT: Final = "unit"
CONF_OPTIONS: Final = "options"
CONF_DEFAULT: Final = "default"
CONF_DEVICE_CLASS: Final = "device_class"
#: Named "display_mode" and not "mode": "mode" is this integration's own
#: dimension, and Home Assistant uses it for its entity modes as well.
CONF_DISPLAY_MODE: Final = "display_mode"
CONF_MIN_LENGTH: Final = "min_length"
CONF_MAX_LENGTH: Final = "max_length"
CONF_PATTERN: Final = "pattern"

# Storage ---------------------------------------------------------------------------

DATA_STORE: Final = "store"
#: The runtime of the whole domain, see ``coordinator.PresetManagerRuntime``.
DATA_RUNTIME: Final = "runtime"

STORAGE_KEY: Final = f"{DOMAIN}.values"
#: Bumped when the shape of the value store changes; see
#: ``PresetValueStore`` for the migration path.
STORAGE_VERSION: Final = 1
#: Bumped for changes an older version could still read. 2 added the two
#: keys below, which an older version simply does not find.
STORAGE_MINOR_VERSION: Final = 2
#: Config entry version. 1 was one entry per preset mode and per blueprint,
#: 2 is the three hubs. Every bump needs a step in ``async_migrate_entry``;
#: the step from 1 to 2 is not one - such an entry is refused, see there.
ENTRY_VERSION: Final = 2
#: Bumped for additive changes to the entry data, which an older version of the
#: integration can still load.
ENTRY_MINOR_VERSION: Final = 1
SAVE_DELAY: Final = 2.0

STORE_ACTIVE_MODES: Final = "active_modes"
STORE_AUTOMATIC: Final = "automatic"
#: The mode a preset was set to by hand, per preset. Only read while that
#: preset's automatic is off; it is rewritten with the mode in effect the
#: moment the automatic is switched off.
STORE_MANUAL_MODES: Final = "manual_modes"
#: Whether a preset follows the mode of its preset mode, per preset.
STORE_PRESET_AUTOMATIC: Final = "preset_automatic"
STORE_VALUES: Final = "values"

# Unique id suffixes -----------------------------------------------------------------

#: Once anybody has this integration installed these must not change: the
#: entity registry keys off the unique ids built from them, so a changed suffix
#: orphans the old entry - its name, area, hidden/disabled flag and history are
#: lost, and the entity comes back with a "_2" suffix, which the user can
#: neither see the cause of nor repair. They are defined once and never spelled
#: out again - the entities are built from them and
#: ``entity.async_expected_unique_ids`` cleans up against them, so the two
#: cannot drift apart the way they did when both spelled them out.
UID_PRESET_MODE_SENSOR: Final = "mode"
UID_ACTIVE_MODE: Final = "active_mode"
#: The mode selector of a *preset*. Not ``active_mode``: that suffix is the
#: preset's own mode sensor, and the two would collide.
UID_MODE_SELECTION: Final = "mode_selection"
UID_AUTOMATIC: Final = "automatic"
UID_VALUE: Final = "value"
UID_CONFIG: Final = "cfg"
#: Separates the two variable fields of an editor's unique id. It must be a
#: character ``slugify`` cannot produce, because both fields are slugs that may
#: contain underscores: mode "night_mode" with parameter "brightness" and mode
#: "night" with parameter "mode_brightness" would otherwise build the same id,
#: and Home Assistant would drop one of the two editors with an "already
#: exists" error the user can neither see the cause of nor repair.
UID_SEPARATOR: Final = "-"

# Attributes ------------------------------------------------------------------------

ATTR_MODE: Final = "mode"
ATTR_MODE_KEY: Final = "mode_key"
ATTR_VALUES: Final = "values"
ATTR_PARAMETER: Final = "parameter"
ATTR_VALUE: Final = "value"
ATTR_MODES: Final = "modes"
#: Names the preset mode a preset belongs to. Deliberately not "preset_mode":
#: a ``climate`` entity carries that attribute with the *active value* in it,
#: while this one names the dimension.
ATTR_MODE_SOURCE: Final = "mode_source"
ATTR_AUTOMATIC: Final = "automatic"
#: Only on a preset mode that follows another entity.
ATTR_SOURCE_ENTITY: Final = "source_entity"
#: Also a key of the ``get_values`` response, which is frozen surface.
ATTR_PRESET: Final = "preset"
#: Only on a preset that follows a blueprint.
ATTR_BLUEPRINT: Final = "blueprint"

# Services --------------------------------------------------------------------------

SERVICE_SET_ACTIVE_MODE: Final = "set_active_mode"
SERVICE_SET_VALUE: Final = "set_value"
SERVICE_GET_VALUES: Final = "get_values"

# Defaults --------------------------------------------------------------------------

DEFAULT_MODE_NAMES: Final = ["Home", "Away", "Night"]
DEFAULT_PRESET_MODE_NAME: Final = "House Mode"
#: Value of the blueprint selector standing for "no blueprint".
BLUEPRINT_NONE: Final = "__none__"
#: Value of the preset mode selector standing for "no preset mode".
PRESET_MODE_NONE: Final = "__none__"

# Repairs ---------------------------------------------------------------------------

#: Issue id of a preset whose preset mode was deleted, per preset.
ISSUE_ORPHANED_PRESET: Final = "orphaned_preset"
