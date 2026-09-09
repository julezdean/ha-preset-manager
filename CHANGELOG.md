# Changelog

All notable changes to this project are documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the
versioning [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **A dashboard card**, shipped with the integration and served by it — no
  resource to add, and no way for card and backend to end up at different
  versions. `type: custom:preset-manager-card` with an `entity:` is the whole
  configuration: point it at any entity of a preset or a preset mode — a value
  sensor, a per-mode editor, the mode selector, the automatic switch — and it
  draws the object that entity belongs to. Values and the active mode on a
  preset, the modes as chips and the automatic on a preset mode, the per-mode
  editors on request, and the presets of a preset mode with their values.
  Grouped options for the header, the modes, the values, the editors and the
  footer, plus Home Assistant's three action keys, and a visual editor built on
  `ha-form`. Nothing about the background, the radius, the shadow or the
  spacing: those come from the theme, and a card that carried its own would be
  the one that stops following it.
- The websocket command `preset_manager/config`, which the card asks for the
  *structure*: the modes with their keys and icons, the parameters, and which
  entity edits which mode of which parameter. None of that is derivable from
  the states, and a card that reconstructed it from display names would break
  on the first rename — which is the one thing this integration promises not to
  do. It carries no values.

  It is deliberately **not** part of the public surface frozen in 0.1.0: the
  card and the integration ship in one version and a user cannot separate them,
  so it may change with any release.
- Mode icons are drawn for the first time. They were configurable, stored and
  until now unused.
- An editor whose mode has no value yet is empty and usable, rather than
  disabled. A value entity reports `unknown` for two different reasons - the
  entity is gone, or nobody has set the value - and the card told them apart
  everywhere except in the controls, where it mattered most: on a preset nobody
  has filled in, which is every new preset, every control was dead. A toggle
  without a value now shows that it has none instead of resting on off, the way
  the integration keeps the two apart itself.
- `modes.visible` takes `true`, `false` or `automatic`, and the new
  `header.automatic` is a switch of its own: which mode is one decision, who
  gets to decide it is another, and they are now decided separately. `manual`
  shows the mode row only while a click would do something: the automatic is
  off, or the preset mode never had one. A row of chips nobody may press is a
  row that only takes space. Left
  alone, a preset mode card offers both and a preset card neither; it does not
  own the dimension. The old `auto`, which meant "guess from the entity", is
  gone: that is what the default does, and it needed no name.
- The mode picker of the editors is an *Edit:* line rather than a heading, and
  can be a dropdown instead of chips (`editor.style`).
- `editor.confirm`: the card shows its values and puts the editors behind an
  **Edit** switch. What is changed there is held rather than written, the
  *Edit:* picker still changes which mode is being edited so one round can
  touch several modes, and an **Apply** button sends the lot and returns to the
  values. Turning the switch off discards the draft — nothing had been written,
  so there is nothing to undo.
- The second line of a preset's header names the active mode and stops there.
  Which preset mode it follows was on every card and every render; the footer
  carries it where it is wanted.
- Arrow keys step a number that is shown as an input field, and write the value
  straight away. The step and the range are the entity's own.
- The row that picks which mode is edited no longer looks like the row that
  sets the active mode. It is smaller, carries no icons and takes its colour
  from the text rather than the accent — one changes the house, the other
  changes what the card shows.
- No more sentence under a locked mode row explaining why it is locked. Every
  version of it repeated what the header says one line above, on every card and
  every render; the chips being visibly disabled was the only part that was not
  already written down.
- The visual editor offers "show icons" for the modes only where a mode
  actually has one. Mode icons are set per mode in the config flow and most
  setups have none, so the switch usually did nothing visible.
- `presets.editable` on a preset mode card: the presets it lists get editors
  for the values of the mode each of them is on, rather than only showing them.
  It implies `visible` and `values`, because asking for editable presets is
  asking to see them. No mode picker per preset — the chips at the top of the
  card already decide the mode, and the editors move with it.
- The entity picker of the visual editor offers one entity per preset and per
  preset mode instead of every entity the integration owns — a preset with five
  parameters over four modes brings 26 of them, and 25 are ways of writing the
  same card. The card itself still accepts any of them, so a dashboard written
  by hand need not know which one is the canonical one.
- A value list with icons keeps the column even for the rows that have none, so
  the labels line up instead of one of them starting an icon's width further
  left.
- The card registers itself as a **Lovelace resource**, the way a card
  installed through HACS arrives, and removes that entry again with the last
  hub. `add_extra_js_url` is gone: it puts a `<script>` into the Home Assistant
  page, which the service worker caches per client, so a browser or a phone
  holding a copy from before the card existed kept serving it — across restarts
  and past a hard reload, looking exactly like a card that does not work. Two
  ways in were also two ways to fail, and a release that changed the version in
  the URL could have the same bundle arrive twice under two URLs, which is one
  module instance too many for an element that may only be defined once.
  Where a dashboard declares its resources in YAML and cannot be written to,
  the log now names the URL to add by hand instead of falling silent.
- The log says what became of the card on every start — the URL it was
  registered at, or which of the two reasons stopped it. Its failure mode from
  the browser is Home Assistant's “custom element not found”, which cannot tell
  a card that was never offered from one that failed to load, and neither can
  the person reading it. The README says what to do about the common cause,
  which is a page held by the service worker rather than anything in the card.
- `frontend/preview.html`, which renders every variant of the card against a
  fake Home Assistant — including the states that are awkward to produce on
  purpose, and a column too narrow for the card. It found three bugs that
  neither the type checker nor the tests can see.

### Changed

- `frontend` is an *after* dependency and `websocket_api` a real one. An
  instance without a frontend sets the integration up exactly as before and
  only skips the card.

## [0.2.0] - 2026-09-08

0.1.0 was withdrawn; this is the release that supersedes it. Entries written
by it are **not** migrated - it had no users, and a migration nobody needs is a
path nobody tests - so an entry at schema 1.1 is refused and has to be deleted
and set up again.

Published as 0.2.0b1 to 0.2.0b3 first.

Entity ids, unique ids, service names and their fields, state attributes and
the two storage formats are the public surface again from here on: they end up
in setups this project can neither see nor update, so changing any of them
needs a migration step or a deprecation period.

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
- Renaming is its own entry in the menu of every object, in the same place, and
  the menus read the same everywhere: what the object is, its name, the rest,
  and duplicating last. The parameter editor of a blueprint opens directly
  instead of behind a name form.
- Menu entries say what they do to what: "Assign preset blueprint" rather than
  "Preset blueprint", "Assign external entity" for the entity a preset mode
  follows.

### Added

- **Duplicating**, in the menu of every object: a preset with its stored
  values, a preset mode with its modes and conditions, a blueprint with its
  parameters.
- **Assign presets**, in the menu of a preset mode and of a blueprint: which
  presets follow it, editable from there as well as from each preset. It is the
  same key either way - the reference lives on the preset - and it is the only
  place that answers "what follows this?" without opening every preset in turn.
- A preset can be created without a preset mode and be assigned one later.

### Removed

- The config entry schema of 0.1.0, see above.

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
