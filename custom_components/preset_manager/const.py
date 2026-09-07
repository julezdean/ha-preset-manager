"""Constants for the Preset Manager integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "preset_manager"

# Config entry / subentry structure -------------------------------------------------

#: One config entry is one preset mode: a set of modes plus the rule
#: picking the active one. Its presets are its subentries, which is what gives
#: the integration page its hierarchy.
#: A "preset" holds the parameters of one device, per mode.
SUBENTRY_TYPE_PRESET: Final = "preset"

#: Kind of a config entry. Written explicitly from 0.1.0 on; an entry without
#: the key is read as a preset mode, which is what ``blueprints.entry_type``
#: does. A third kind is therefore an addition rather than a migration.
CONF_ENTRY_TYPE: Final = "entry_type"
#: A preset mode: a set of modes plus the presets that follow them.
ENTRY_TYPE_PRESET_MODE: Final = "preset_mode"
#: A blueprint: a config entry that holds nothing but parameter
#: definitions, followed by any number of presets.
ENTRY_TYPE_BLUEPRINT: Final = "blueprint"

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
#: Only used by the flow that moves a preset to another preset mode; a
#: preset belongs to the config entry it is a subentry of.
CONF_PRESET_MODE: Final = "preset_mode"
CONF_PARAMETERS: Final = "parameters"
#: Entry id of the blueprint a preset follows. While it is set the preset
#: has no parameters of its own: they are resolved from the blueprint on every setup,
#: and its parameter editor stays closed.
CONF_BLUEPRINT: Final = "blueprint"

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

STORAGE_KEY: Final = f"{DOMAIN}.values"
#: Bumped when the shape of the value store changes; see
#: ``PresetValueStore`` for the migration path.
STORAGE_VERSION: Final = 1
#: Bumped for changes an older version could still read.
STORAGE_MINOR_VERSION: Final = 1
#: Config entry version; bumped when the stored key names change. Every bump
#: needs a step in ``async_migrate_entry``.
ENTRY_VERSION: Final = 1
#: Bumped for additive changes to the entry data, which an older version of the
#: integration can still load.
ENTRY_MINOR_VERSION: Final = 1
SAVE_DELAY: Final = 2.0

STORE_ACTIVE_MODES: Final = "active_modes"
STORE_AUTOMATIC: Final = "automatic"
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
