# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
versioning [Semantic Versioning](https://semver.org/).

## [0.2.0b2] - 2026-09-07

Beta. The layout of the config entries changes. Entries written by 0.1.0 are
**not** migrated: that release was withdrawn without anybody running it, so
such an entry is refused and has to be deleted and set up again. A backup
beforehand is what a beta is for all the same.

### Changed

- Preset modes, presets and preset blueprints now each live in a hub of their
  own and are subentries of it. With that, every object says what kind it is, a
  blueprint is no longer offered where a preset is expected, and the model says
  what it means: a blueprint belongs to no preset mode.
- A preset survives the deletion of its preset mode. It keeps its parameters,
  its values and the modes it had, and a repair issue asks for a new preset
  mode; until it gets one it has no active mode and its values do not resolve.
- Assigning another preset mode is a field on the preset rather than a move
  between config entries — its entities are not rebuilt at all.
- A rename, a changed condition and another source entity no longer cost a
  reload of everything the hub holds.

### Added

- Duplicating, in the menu of every object: a preset with its stored values, a
  preset mode with its modes and conditions, a blueprint with its parameters.
- A preset can be created without a preset mode and be assigned one later.

### Removed

- The config entry schema of 0.1.0. There is no path from it - a migration
  nobody needs is a path nobody tests - so an entry at schema 1.1 is refused
  with an error on the entry instead of being read half way.

## [0.1.0] - 2026-09-07

First release. Preset Manager creates the helpers for mode-dependent values
and keeps the mode logic out of your automations.

Entity ids, unique ids, service names and their fields, state attributes and
the two storage formats are public surface from this release on: they end up in
setups this project can neither see nor update, so changing any of them needs a
migration step or a deprecation period. Display names, the translations and the
internal module layout are deliberately not part of that.

### Added

- Preset modes as config entries: a set of modes that belong together, with the
  conditions deciding which of them is active, added through **Settings →
  Devices & services → Add integration**
- Presets as subentries of the preset mode they follow, each one a device with
  its parameters and its values per mode
- One main sensor per parameter carrying the value of whichever mode is active,
  so an automation needs no mode logic of its own
- Editable helpers per mode and parameter — `number`, `switch`, `select`,
  `text`, `datetime`, `date` and `time` in the category *Configuration*
- Parameter types mirroring the Home Assistant input helpers, with range, step,
  unit, device class, options, pattern, display mode, default value and icon
- Conditions per mode in one sortable list, the first match wins; a mode
  without conditions always matches and is therefore the fallback
- An automatic switch per preset mode, to take over by hand without changing
  the configuration
- Handing a preset mode to an entity whose state names the active mode, which
  leaves the integration carrying the values and nothing else
- Preset blueprints: a parameter list of its own, added through **Settings →
  Devices & services → Add integration → Preset blueprint**, followed by any
  number of presets and usable across preset modes. A blueprint holds nothing
  but parameter definitions — no device, no entities
- A preset can follow a blueprint instead of defining parameters itself, chosen
  when it is created or later under **Preset → Edit → Preset blueprint**. It
  then takes over the parameters of the blueprint and every later change of
  them, while its values per mode stay its own. Its parameter editor is closed
  for as long as it follows one, so the two cannot drift apart
- Leaving a blueprint keeps its parameters as the preset's own, values
  included, and opens the editor again. Deleting a blueprint does the same to
  every preset following it, so a deleted blueprint costs its presets their
  lock and nothing else
- Presets movable to another preset mode, keeping their entity ids, their
  history and every value of a mode that exists in both
- Services `set_active_mode`, `set_value` and `get_values`, each taking a
  standard target: the mode selector for `set_active_mode`, the device or any
  entity of a preset for the other two, so areas, floors and labels work too
- Stable keys behind every mode and parameter, so renaming loses nothing, and
  English entity ids on a translated instance
- Icons for every entity and every service, the automatic switch showing at a
  glance whether it is following its conditions
- Downloadable diagnostics per config entry, covering the modes, the resolved
  state and every stored value; also available for an entry that failed to set
  up, which is when they are needed most
- English and German translations
- CI runs hassfest, the HACS validation, ruff, black, mypy and the test suite
  on every push
