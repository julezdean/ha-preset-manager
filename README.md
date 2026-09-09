# Preset Manager for Home Assistant

[![HACS: custom repository](https://img.shields.io/badge/HACS-custom%20repository-41BDF5.svg)](https://github.com/hacs/integration)
[![Release](https://img.shields.io/github/v/release/julezdean/ha-preset-manager?include_prereleases&sort=semver)](https://github.com/julezdean/ha-preset-manager/releases)
[![Tests](https://github.com/julezdean/ha-preset-manager/actions/workflows/test.yml/badge.svg)](https://github.com/julezdean/ha-preset-manager/actions/workflows/test.yml)
[![Validate](https://github.com/julezdean/ha-preset-manager/actions/workflows/validate.yml/badge.svg)](https://github.com/julezdean/ha-preset-manager/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Creates the helpers for mode-dependent values in one go — and keeps the
mode logic out of your automations.

You define a **preset mode** with a set of modes (for example Home /
Away / Night / Window open) and one **preset** per device with its
**parameters**. The integration creates every helper you would otherwise build
by hand — one editable value per mode and parameter — plus **one main sensor
per parameter**, which always carries the value of whichever mode is active
right now.

```
Preset mode "House Mode"                          active: Night
   Home · Away · Night · Window open

Preset "Motion Sensor Living Room"
   number.…_home_brightness            80 %
   number.…_away_brightness             0 %
   number.…_night_brightness           15 %   <- active mode
   number.…_window_open_brightness      5 %
                     |
   sensor.…_brightness                 15 %   <- the main sensor
```

**Adding a mode is all it takes** — every helper that belongs to it appears
automatically, in every preset. Delete the mode and they disappear again.

**The main sensor is the actual point.** An automation reads it and nothing
else: no `if night then 15 else 80`, no template picking one helper out of
four, no branch per mode.

```yaml
brightness_pct: "{{ states('sensor.motion_sensor_living_room_brightness') | int }}"
```

Change a value from the dashboard, switch the mode, add a fifth mode —
that automation never changes. A large part of what would otherwise sit in your
automations lives in the integration instead.

You can create **as many preset modes as you like** and attach each preset to
one of them — a shutter can follow a "Window State" preset mode while the
heating follows "House Mode". A preset mode runs automatically as soon as one
of its modes has conditions, can be taken over by hand at any time, or can be
handed to an entity you already have.

> **On the word "helper":** these behave like the helpers you would otherwise
> create by hand, but they are not `input_number` entities. They live on the
> preset's device page under *Configuration*, not under
> Settings → Devices & Services → Helpers.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=julezdean&repository=ha-preset-manager&category=integration)

The button opens your own HACS and offers to add this repository as a custom
one; confirm, then download it from the page that opens and restart Home
Assistant. By hand instead:

1. HACS → Integrations → ⋮ → *Custom repositories*.
2. Add the repository URL, category *Integration*.
3. Install "Preset Manager" and restart Home Assistant.

Without HACS: copy the `custom_components/preset_manager` folder into
`<config>/custom_components/` and restart Home Assistant.

Then **Settings → Devices & Services → Add Integration → Preset Manager**, and
carry on at [Setup step by step](#setup-step-by-step).

Requires Home Assistant 2025.12 or newer (config subentries). The bundled brand
images in `custom_components/preset_manager/brand/` are picked up from Home
Assistant 2026.3 onwards.

## Features

* **One main sensor per parameter** carrying the currently valid value, so an
  automation needs no mode logic of its own.
* **Helpers created for you** — add a mode and every helper that belongs to
  it appears in every preset; delete it and they are gone.
* **Any number of preset modes**, each with its own modes and its own
  rule for picking the active one.
* **Conditions per mode**, in one sortable list — the first match wins.
* **Or hand a preset mode to an entity you already have**, whose state then
  names the active mode.
* **An automatic switch** per preset mode: temporarily take over by hand without
  changing the configuration.
* **Modes with stable keys** — renaming never loses values.
* **Any number of presets** (devices/scenarios), each following one preset
  mode and reassignable to another one without losing values. A preset also
  survives the deletion of its preset mode and waits for a new one.
* **Duplicate anything** — a preset with its values, a preset mode with its
  modes, a blueprint with its parameters.
* **Freely configurable parameters** with type, range, step, unit, options and a
  default value.
* **Blueprints**: define a parameter list once - "Heating" with a target
  temperature and a boost duration - and let any number of presets follow it.
  They pick up every change of the blueprint automatically, and their own
  parameter editor stays closed so the two can never drift apart. The values
  per mode stay individual.
* **Helpers editable straight from the dashboard** — `number`/`switch`/`select`/
  `text` entities in the category *Configuration*.
* **A dashboard card of its own**, shipped with the integration and served by
  it: point it at any entity of a preset or a preset mode and it draws that
  object — values, modes, and the per-mode editors when you want them. Nothing
  to install, nothing to add as a resource.
* **Instant updates** on a mode switch, without a restart and without polling.
* Fully configurable through the UI, no YAML configuration.

## Vocabulary

| Term | What it is | Example |
| --- | --- | --- |
| **Preset mode** | An ordered set of modes; the first whose conditions match is active | House Mode, Window State |
| **Mode** | One option inside a preset mode, optionally with conditions | Home · Away · Night |
| **Automatic** | Runtime switch: follow the conditions, or set the mode by hand | `switch.house_mode_automatic` |
| **Preset** | One device or scenario with its parameters, attached to a preset mode | Motion Sensor Living Room |
| **Parameter** | One configurable value inside a preset | Brightness, Off delay |
| **Blueprint** | A parameter list of its own that any number of presets can follow | Heating, Shutters |

The integration owns three entries, one per kind of object, and every object is
a subentry of the hub that collects its kind:

```
Settings → Devices & Services → Preset Manager

  Preset Modes
  ├── House Mode                    Home · Away · Night · Window open
  └── Window State                  Closed · Open

  Presets
  ├── Motion Sensor Living Room     follows House Mode
  ├── Heating Living Room           follows House Mode · Heating
  └── Shutter Living Room           follows Window State

  Preset Blueprints
  └── Heating                       target temperature, boost duration
```

Nothing is contained in anything else. A preset **names** the preset mode it
follows and the blueprint it follows, both of which it can be given, changed
and taken away — a blueprint is shared across preset modes and belongs to none
of them, and a preset is worth keeping when its dimension goes. Every preset
mode and every preset gets a device of its own.

## Setup step by step

### 1. Add a preset mode

**Settings → Devices & Services → Add Integration → Preset Manager**

The first step asks what you are adding — a *preset mode*, a *preset* or a
[*preset blueprint*](#blueprints). Pick the preset mode:

```
Name of the preset mode:  House Mode
Modes:                    [Home] [Away] [Night] [Window open]
```

Type a name and press enter to add your own. That is it — the preset mode is
manual for now. Conditions are added afterwards in the mode list, see
[Managing modes](#managing-modes).

You never create a hub yourself: the *Preset Modes* hub appears with the first
preset mode, and the other two with the first preset and the first blueprint.

### 2. Add more preset modes

Either from the integration page — **"Add preset mode"** on the *Preset Modes*
hub — or by adding the integration again. Both put the new preset mode in the
same hub, for example a "Window State" one with *Closed* and *Open*.

### 3. Create a preset

Choose **"Add preset"** on the *Presets* hub:

```
Name:         Motion Sensor Living Room
Preset mode:  House Mode
Blueprint:    -
```

The preset mode decides which of the preset's values are valid right now, and
the preset always covers **every** mode of it; modes added later show up
automatically. It can be left on "-" and assigned later — the preset exists,
keeps its parameters and its values, and only has no active mode until it
follows one.

Leave the blueprint on "-" to define the parameters yourself in the next step;
a blueprint fills them in instead and is described under
[Blueprints](#blueprints). The field only appears once at least one blueprint
exists.

### 4. Define parameters

The dialog then asks for parameters — two steps per parameter:

```
Name:  Brightness        Name:  Color temperature   Name:  Off delay
Type:  Number            Type:  Number              Type:  Number

Minimum:      0          Minimum:      2000         Minimum:      0
Maximum:      100        Maximum:      6500         Maximum:      3600
Step size:    1          Step size:    50           Step size:    1
Unit:         %          Unit:         K            Unit:         s
Device class: –          Device class: –            Device class: Duration
Display:      Input      Display:      Input        Display:      Input
Default:      –          Default:      –            Default:      –
```

After each parameter a menu appears: *Add another parameter* or *Create preset*.

The types are the Home Assistant input helpers, with the same raw settings:

| Type | Helper | Settings |
| --- | --- | --- |
| Number | `input_number` | minimum, maximum, step size, unit, device class, input field or slider |
| Toggle | `input_boolean` | – |
| Text | `input_text` | minimum and maximum length, pattern, text or password |
| Dropdown | `input_select` | options |
| Date and time / Date / Time | `input_datetime` | – |

Every type also takes a default value and an icon.

**Device class** is optional and tells Home Assistant what a number means. With
`Temperature` the value is converted to the unit in the user's Home Assistant
profile and gets proper long-term statistics; without it the number stays a
plain number with a unit. Only units the device class accepts are allowed.

### 5. Enter values

Values are entered through the helpers of the preset — on its device page
under *Configuration*, or from any dashboard:

```
number.motion_sensor_living_room_home_brightness           80
number.motion_sensor_living_room_night_brightness          15
number.motion_sensor_living_room_night_color_temperature 2200
number.motion_sensor_living_room_night_off_delay           30
```

The service `preset_manager.set_value` writes the same values from an
automation.

Date, time and date-and-time parameters publish their value as a **timestamp**
sensor, so they can be used as a trigger directly:

```yaml
automation:
  - alias: "Wake up"
    triggers:
      - trigger: time
        at: sensor.alarm_clock_wake_up
```

A time of day resolves to that time *today* and moves on at midnight.

### 6. Use it in automations

```yaml
automation:
  - alias: "Motion living room"
    triggers:
      - trigger: state
        entity_id: binary_sensor.motion_living_room
        to: "on"
    actions:
      - action: light.turn_on
        target:
          entity_id: light.living_room
        data:
          brightness_pct: "{{ states('sensor.motion_sensor_living_room_brightness') | int }}"
          kelvin: "{{ states('sensor.motion_sensor_living_room_color_temperature') | int }}"
      - delay:
          seconds: "{{ states('sensor.motion_sensor_living_room_off_delay') | int }}"
      - action: light.turn_off
        target:
          entity_id: light.living_room
```

Condition on the effective mode of a preset:

```yaml
conditions:
  - condition: state
    entity_id: sensor.motion_sensor_living_room_active_mode
    state: "Night"
```

## Managing modes

Everything about the modes of a preset mode happens in **one sortable list**,
under *Preset mode → Configure → Manage modes*:

```
Preset mode "House Mode"

⠿  Window open    Wenn binary_sensor.window an        ✎  🗑
⠿  Vacation       Wenn input_boolean.vacation an      ✎  🗑
⠿  Night          Wenn Zeit nach 22:00                ✎  🗑
⠿  Away           —                                   ✎  🗑
⠿  Home           —                                   ✎  🗑
                                        [ Add ]
```

* **Drag** a row by its handle to change the priority.
* **Pencil** opens the row: name, icon and Home Assistant's condition editor.
* **Bin** deletes the mode — with its stored values in every preset.
* **Add** creates a new mode.

The list is worked through from top to bottom and the **first mode whose
conditions match** becomes active. A mode **without conditions always
matches**, so it catches everything below it — that is how a preset mode gets a
fallback mode, and you decide where it sits. A row without conditions at the
*top* of the list therefore makes every row below it unreachable.

If nothing matches at all, **no mode is active**: the preset mode reports
`unknown` and so does every preset that follows it.

The same order is also the order of the options of the select entity, so there is
only one order to think about.

### Following an entity or a template

A mode can follow another entity as a condition — see
[Handing the preset mode to an entity](#handing-the-preset-mode-to-an-entity)
for the other way, where the whole preset mode does. Templates work the same
way.

```yaml
# Mode "Night" follows an input_select
condition: state
entity_id: input_select.house_mode
state: "Night"

# Mode "Night" from a template
condition: template
value_template: "{{ now().hour >= 22 }}"
```

Note that a state condition compares the **state text**. If you rename a mode,
update the condition that matches its name.

### How it re-evaluates

The preset mode re-evaluates whenever an entity referenced by any condition
changes. Template conditions are tracked as well. Time and sun conditions cannot
announce themselves that way, so it additionally re-evaluates once a minute when
such a condition is used.

## Automatic and manual

A preset mode where at least one mode has conditions gets a switch:

```
switch.house_mode_automatic      on
select.house_mode_active_mode    Night
sensor.house_mode_mode           Night
```

* **On** — the mode follows the conditions.
* **Off** — the mode stays where it is and you set it in the select entity.

Switching it back on evaluates the conditions right away, so the preset mode
catches up without waiting for the next event. The switch position survives restarts.

While the automatic is on, writing to the select entity — or calling
`preset_manager.set_active_mode` — is **refused** with a clear message. That
is deliberate: a single click should not silently disable your automation. Turn
the switch off first, then pick the mode.

A preset mode whose modes have no conditions has no switch, because there is
nothing to switch between.

## Handing the preset mode to an entity

Under *Configure → Preset mode settings* you can name an entity the preset mode
should **follow**. Its state names the active mode — compared against the
mode names, keys and slugs, upper/lower case irrelevant:

```
input_select.house_mode          Night
        |
        v
sensor.house_mode_mode              Night
sensor.motion_sensor_..._active_mode  Night
```

The preset mode sensor carries the entity it follows as the `source_entity`
attribute, in place of the `automatic` attribute it otherwise has.

That hands the preset mode over completely:

* the **conditions are ignored** — they stay stored, so clearing the entity
  brings them back untouched
* there is **no automatic switch**, because there is nothing to switch between
* there is **no select entity**, and `preset_manager.set_active_mode` refuses
  the preset mode — the mode belongs to the entity
* a state that names **no** mode, and an `unavailable`/`unknown` entity, leave
  the preset mode without an active mode

The picker offers `sensor`, `select`, `input_select`, `input_text` and `text`
entities. Use this when the mode already exists somewhere in your setup and
this integration should only carry the values.

## Naming

**Entity ids are always English**, regardless of the language of your Home
Assistant instance — `sensor.<preset_mode>_mode`, `sensor.<preset>_active_mode`,
`select.<preset_mode>_active_mode` and `switch.<preset_mode>_automatic` (the
last two only where they exist). The **display names** follow the system
language ("Aktiver Mode" / "Automatik" on a German instance).

Names you choose yourself (preset mode, preset, parameter and mode names) go
into the entity id unchanged: the parameter "Brightness" of the preset "Motion
Sensor Living Room" becomes `sensor.motion_sensor_living_room_brightness`.

Entity ids never change when values change, nor when you rename a mode or a
parameter — internally everything hangs off a stable key.

## Created entities

Per preset mode, and per preset with P parameters and N modes:

| Entity | Count | Category | Meaning |
| --- | --- | --- | --- |
| `sensor.<preset_mode>_mode` | 1 per preset mode | – | Active mode of the preset mode |
| `select.<preset_mode>_active_mode` | 1 per preset mode | – | Set the active mode (while automatic is off) |
| `switch.<preset_mode>_automatic` | 1 per preset mode with conditions | – | Follow the conditions, or set by hand |
| `sensor.<preset>_active_mode` | 1 per preset | – | Effective mode + attributes |
| `sensor.<preset>_<parameter>` | P | – | Currently valid value |
| `number`/`switch`/`select`/`text`/`datetime`/`date`/`time` `.<preset>_<mode>_<parameter>` | P × N | Configuration | Mode value for editing |

Toggle parameters produce a `binary_sensor` instead of a `sensor`; date and time
parameters produce a `sensor` with device class `timestamp`.

Attributes of `sensor.<preset>_active_mode`:

```yaml
mode_key: night
mode_source: House Mode
modes: [Home, Away, Night, Window open]
values:
  brightness: 15
  color_temperature: 2200
  off_delay: 30
blueprint: Heating       # only while the preset follows a blueprint
```

## Dashboard card

The integration ships its own Lovelace card. There is nothing to install and no
resource to add by hand — it registers itself as one, is served by the
integration, and can therefore never be a version out of step with it. The
entry disappears again with the last of its hubs.

```yaml
type: custom:preset-manager-card
entity: sensor.motion_sensor_living_room_active_mode
```

That is the whole configuration. The card works out what the entity belongs to
and draws the preset behind it — its name, the mode that is effective right
now, and one row per parameter with the value that is valid:

```
  Motion Sensor Living Room
  Night · House Mode

  Brightness                             15 %
  Color temperature                   2 200 K
  Off delay                              30 s
```

Point it at an entity of a **preset mode** instead and it draws that: the modes
as a row of chips, the active one marked, and the automatic switch beside the
name.

```yaml
type: custom:preset-manager-card
entity: sensor.house_mode_mode
```

```
  House Mode                          [Auto ●]
  Night

  [ Home ] [ Away ] [ Night ] [ Window open ]
```

**Any entity of the object does.** The active mode sensor of a preset, one of
its value sensors, one of its per-mode editors, the mode sensor of a preset
mode, its selector, its automatic switch — all of them name the same object and
give the same card. Nothing is matched by name, so renaming a preset, a mode or
a parameter leaves every card that shows it working.

### Configuration

Every option is optional and lives in the group it belongs to. What is not
written is not configured — the card decides, and it decides the same way every
time.

| Option | Default | Meaning |
| --- | --- | --- |
| `entity` | – | Any entity of Preset Manager. The only required option. |
| `header.visible` | `true` | The name, the state line and the automatic. |
| `header.title` | the object's name | Overrides the first line. |
| `header.subtitle` | the mode and where it comes from | Overrides the second line; `false` removes it. |
| `header.icon` | the icon of the active mode | Overrides the icon; `false` removes it. |
| `header.icon_color` | the mode's colour | Overrides the icon colour. |
| `modes.visible` | `auto` | `auto` shows the chips on a preset mode and hides them on a preset. `always`/`never` decide it. |
| `modes.style` | `chips` | `chips` or `dropdown`. |
| `modes.icons` | `true` | Show the icon of each mode — only does something for modes that were given one. |
| `modes.colors` | – | Colour per mode key, used for the active chip and the header icon. |
| `values.visible` | `true` | The parameter rows of a preset. |
| `values.parameters` | all of them | Which parameters to show, in which order. |
| `values.icons` | `false` | Show each parameter's icon. |
| `editor.enabled` | `false` | Turn the rows into the per-mode editors. |
| `editor.mode` | `picker` | `picker`, `active` or `all`; see below. |
| `editor.default_mode` | the active mode | Mode key the picker starts on. |
| `presets.visible` | `false` | On a preset mode: list the presets following it. |
| `presets.values` | `false` | And their values. |
| `presets.editable` | `false` | And make those values editable. Implies the two above. |
| `footer.visible` | `false` | The footer line. |
| `footer.content` | `[preset_mode]` | Any of `preset_mode`, `blueprint`, `source`, `last_changed`. |
| `tap_action` | `more-info` | Home Assistant's action config, on the header. |
| `hold_action` | – | Same. |
| `double_tap_action` | – | Same. |

The three action keys sit at the top level rather than in a group of their own,
because that is where every other Home Assistant card has them and a dashboard
is copied between cards more often than it is read.

There is no option for the background, the corner radius, the shadow or the
spacing. The card is a `ha-card` and takes all four from the theme, so it looks
like the cards around it and follows the next theme the user installs; a card
carrying its own would be the one that stops.

Everything else is grouped, so a long configuration stays readable:

```yaml
values:
  parameters: [brightness, off_delay]

editor:
  enabled: true
  mode: picker
```

instead of `show_values`, `value_parameters`, `show_editor`, `editor_mode`.

### Picking parameters

`values.parameters` selects and orders in one list. A row is a parameter key,
or a group that renames it or gives it an icon:

```yaml
values:
  parameters:
    - brightness
    - parameter: off_delay
      name: Run-on
      icon: mdi:timer-outline
```

A key that no longer exists is skipped rather than drawn as an error, so
deleting a parameter does not break every dashboard that named it.

### Editing values

The editors are `Configuration` entities: they are how a preset is **set up**,
not how it is used. So `editor.enabled` is off by default and a card shows the
resolved values — which is what a dashboard is for. Turn it on and the same
rows become the per-mode helpers:

* `mode: picker` — a row of chips picks which mode is edited, and a line below
  names the active mode whenever the two differ. Those chips are deliberately
  quieter than the mode row above: smaller, without icons, and coloured from
  the text rather than the accent. One row changes the house, the other changes
  what this card shows, and they should not look like the same act.
* `mode: active` — always edits the mode that is active.
* `mode: all` — every mode of every parameter, one row each. The full picture,
  and the widest.

The read-only column goes away when the editors appear. The editor of the
active mode holds exactly the value the sensor resolves, so showing both would
be the same number twice with nothing to tell them apart.

On a **preset mode** card the same applies to the presets it lists:
`presets.editable` turns their values into editors for the mode each preset is
on. There is no mode picker per preset there — the card already has one row of
chips deciding the mode, and a second way to choose one would be a different
question wearing the same clothes. Switching the mode moves these editors with
it, which is the point: having seen what Night means for every device in the
room, this is where it is changed.

### Switching the mode

Clicking a chip calls `preset_manager.set_active_mode` with the mode's **key**,
so it keeps working after a rename. The chips are disabled when the integration
would refuse the write anyway:

* while the **automatic** is on — turn the switch in the header off first,
* when the preset mode **follows another entity**, which owns the mode.

The header says which of the two it is, so the row itself carries no
explanation: the second line names the mode and, where there is one, the entity
the preset mode was handed to, and the automatic sits beside it as a switch.

On a preset card the chips are hidden by default (`modes.visible: auto`).
Showing them there is deliberate: a preset does not own its dimension, so
switching the mode from one preset's card changes what every preset of that
preset mode does.

### Examples

**Minimal** — the values of one preset.

```yaml
type: custom:preset-manager-card
entity: sensor.motion_sensor_living_room_active_mode
```

**One value** — a single row in a grid of many.

```yaml
type: custom:preset-manager-card
entity: sensor.motion_sensor_living_room_active_mode
header:
  subtitle: false
values:
  parameters: [brightness]
```

**The dimension** — the modes of a preset mode with its automatic.

```yaml
type: custom:preset-manager-card
entity: sensor.house_mode_mode
modes:
  colors:
    night: "#5c6bc0"
    window_open: "#ef6c00"
```

**The room** — one preset mode with everything that follows it, and the values
of the mode it is on, editable.

```yaml
type: custom:preset-manager-card
entity: sensor.house_mode_mode
presets:
  editable: true
footer:
  content: [last_changed]
```

**Setting up a preset** — the per-mode helpers, without leaving the dashboard.

```yaml
type: custom:preset-manager-card
entity: sensor.heating_bath_active_mode
editor:
  enabled: true
  mode: picker
footer:
  content: [preset_mode, blueprint]
```

**Everything at once** — every group, for reading rather than for using.

```yaml
type: custom:preset-manager-card
entity: sensor.motion_sensor_living_room_active_mode

header:
  visible: true
  title: Living room light
  subtitle: false
  icon: mdi:lightbulb-outline
  icon_color: "#f9a825"

modes:
  visible: always
  style: chips
  icons: true
  colors:
    night: "#5c6bc0"

values:
  visible: true
  icons: true
  parameters:
    - brightness
    - parameter: color_temperature
      name: Warmth
    - parameter: off_delay
      name: Run-on
      icon: mdi:timer-outline

editor:
  enabled: true
  mode: picker
  default_mode: night

footer:
  content: [preset_mode, blueprint, last_changed]

tap_action:
  action: more-info
hold_action:
  action: navigate
  navigation_path: /config/devices/dashboard
```

### If something is wrong

| What the card says | What it means |
| --- | --- |
| “… does not belong to Preset Manager” | The entity is not one of this integration's. Any entity of the preset or preset mode does. |
| “Preset Manager is not set up” | No preset mode and no preset exists yet, or the integration failed to load. |
| “No mode active” | No condition matched, the source entity names no mode, or the preset has no preset mode. Same causes as an `unknown` sensor. |
| “Not set” on a row | That mode has no value for the parameter and the parameter has no default. |
| “Unavailable” on a row | The entity behind the row is disabled or gone. |
| “Waiting for a preset mode” | The preset outlived its preset mode; assign it a new one. |
| “Custom element not found: preset-manager-card” | The browser is holding an old copy of the page. See below — this is the one failure that looks like a broken card and is not. |

### “Custom element not found”

The integration adds the card to your **Lovelace resources**, the way a card
installed through HACS arrives. You do not add it by hand, and it is taken back
out when the last of the integration's hubs is removed. It shows up under
Settings → Dashboards → ⋮ → Resources, and the version in its URL changes with
every release.

It used to also put a `<script>` into the Home Assistant page, which needed
nothing from your configuration. That is gone. The page is cached by the
service worker, per browser and per phone, so a client holding a copy from
before the card existed kept serving it — across restarts, past a hard reload,
and looking exactly like a card that is broken. Two ways in turned out to be
two ways to fail.

So if the card is missing, look in the log for `preset_manager`. Every outcome
says so:

* `Dashboard card registered as a Lovelace resource: …` — it is registered.
  Check that the URL in the message opens in your browser and returns
  JavaScript.
* `… cannot be written to, so the dashboard card is not registered. Add it by
  hand as a JavaScript module: …` — your dashboard declares its resources in
  YAML and owns that list. Add the URL from the message to it.
* `The dashboard card is not built …` — the install did not bring the bundle.
* `The frontend integration is not set up …` — a headless instance, where the
  card has nothing to appear on.

If it is registered, the URL serves and the card is still missing, the client
is holding a stale page. That is cleared **once per client**: in a browser,
clear the site data for your Home Assistant address (a private window is the
quick way to confirm it first); in the companion app, Settings → Companion App
→ Debugging, reset the frontend cache and restart the app.

The card asks the integration for its structure once per browser connection and
follows the entity and device registries for changes, so a new mode, a renamed
parameter or a moved preset arrives without a reload of the page.

> **For the record:** that request is the websocket command
> `preset_manager/config`. It returns the structure — modes with their keys and
> icons, the parameters, and which entity is which — and no values. It is
> **not** part of the public surface listed under [Upgrading](#upgrading): the
> card and the integration ship in one version and a user cannot separate them,
> so it may change with any release.

## Managing a preset mode

Preset mode → **Edit**:

* **Manage modes** — the sortable list: add, rename, reorder and delete
  modes, and set their conditions
* **Rename**
* **Assign presets** — which presets follow this preset mode, editable from
  here as well as from each preset. Taking one off leaves it with everything
  but its active mode; adding one that follows another preset mode moves it,
  and the picker says in brackets where it comes from
* **Assign external entity** — the entity whose state names the active mode
* **Duplicate** — a second preset mode with the same modes and conditions.
  Not with the same source entity: two preset modes reading the same entity
  would always hold the same mode.

**Deleting a preset mode does not delete its presets.** They keep their
parameters, their values and the modes they had, and a repair issue asks for a
new preset mode; until it gets one, a preset has no active mode and its values
do not resolve.

## Managing a preset

Preset → **Edit**:

* **Manage parameters** — the sortable list: add, rename, retype, reorder and
  delete parameters; the field below the list opens the type specific details
  (range, unit, options, default value) of one of them
* **Rename**
* **Assign preset mode** — let it follow another one, or none
* **Assign preset blueprint** — attach the preset to a blueprint, move it to
  another one, or let it go again
* **Duplicate** — a second preset with the same parameters *and the same
  values*, following the same preset mode and the same blueprint

A preset that follows a blueprint has **no** "Manage parameters" entry: its
parameters live in the blueprint. See [Blueprints](#blueprints).

A new parameter goes into its detail form automatically. Changing the type of an
existing one does the same — and drops its stored values, because the old ones
no longer fit the new type.

Changing the *preset mode* changes what the preset follows; nothing about the
preset itself moves. It keeps its entity ids, its history and every value of a
mode that exists in both preset modes; values of modes the new one does not
have are dropped.

## Blueprints

Ten radiators want the same parameters: a target temperature, a boost duration,
a window-open drop. A **blueprint** defines that list once, and every preset
attached to it takes the list over — including every later change.

```
Blueprint "Heating"
   Target temperature   5 – 30 °C
   Boost duration       0 – 120 min

Preset "Heating Bath"        ─┐        Preset "Heating Bedroom"
   blueprint: Heating         │           blueprint: Heating
   number.…_home_target_…  23 │           number.…_home_target_…  18
   number.…_night_target_… 19 │           number.…_night_target_… 17
                              │
   the same parameters ───────┘        their own values
```

The blueprint defines the **parameters**; the **values** stay with each preset,
per mode. That is the whole point: one definition, many devices, each with its
own numbers.

### Creating one

**Add Integration → Preset Manager → Preset blueprint**, or "Add preset
blueprint" on the *Preset Blueprints* hub. It asks for a name and then for the
parameters, in exactly the same list a preset uses. A blueprint creates no
device and no entities — it is configuration and nothing else.

**Blueprint → Edit → Assign presets** lists the presets that follow it and is
the only place that answers "what follows this blueprint?" without opening
every preset. Adding one there does what attaching does, for several at once —
including the loss of their own parameter lists, so the step says so.

Editing it later: **Blueprint → Edit → Manage parameters**. The menu is the same
everywhere — what the object *is* first, **Rename** second, then the rest, and
**Duplicate** last. Duplicating is the quickest way to a variant: the copy gets
the parameters, and the presets of the original keep following the original.

### Using one

Pick it in the *Blueprint* field when creating a preset, or later under
*Preset → Edit → Blueprint*.

A preset following a blueprint:

* takes over its parameters, and **every change to the blueprint arrives on its
  own** — a parameter added there appears in every preset that follows it, a
  deleted one disappears, a renamed one is renamed;
* has **no parameter editor of its own**. The entry is gone from its menu, so
  the two cannot drift apart — a manual change would only be silently taken back
  by the next update of the blueprint anyway;
* keeps its **own values** per mode, and its own name, preset mode, entities and
  history.

Presets of the same blueprint may sit in different preset modes: a blueprint
knows nothing about modes, which is exactly why it fits everywhere.

### Leaving one

Set the blueprint back to "-" under *Preset → Edit → Blueprint*. The preset
keeps the parameters it has at that moment **as its own**, values included, and
can edit them again. That is also how you use a blueprint as a one-off starting
point: attach, detach, edit.

**Deleting a blueprint** does the same to every preset that follows it — they
keep its parameters and are editable again. Deleting a blueprint never deletes a
preset; nothing in this integration deletes anything but itself.

Switching a preset to *another* blueprint replaces its parameters with those of
the new one. Values survive wherever a parameter of the same key exists in both;
the rest are dropped, the same way a deleted parameter's values are.

## Error behaviour

| Situation | Result |
| --- | --- |
| Mode without a value for a parameter | The parameter's default value, otherwise `unknown` |
| Mode deleted | Its helpers and stored values disappear |
| Preset mode without modes | Its presets report `unknown` |
| Preset mode deleted | Its presets keep everything but the active mode, and a repair issue asks for a new one |
| Restart with no stored active mode | The first mode, or `unknown` once conditions are in play |
| No mode's conditions match | No mode is active; the preset mode and its presets report `unknown` |
| A condition fails | Warning in the log, that mode is skipped |
| Source entity names no mode, or is unavailable | Warning in the log, no mode is active |
| Blueprint deleted | Its presets keep its parameters as their own, values included, and are editable again |

## Services

Every service takes a normal target. A preset mode is addressed by its mode
selector, a preset by its device or any of its entities - so an area, a floor
or a label works as well, and nothing depends on a name you are free to
change.

```yaml
# Set the active mode by its stable key (only while the automatic is off)
action: preset_manager.set_active_mode
target:
  entity_id: select.house_mode_active_mode
data:
  mode: night

# Set a single mode value
action: preset_manager.set_value
target:
  device_id: <device of the preset>
data:
  mode: night
  parameter: brightness
  value: 15

# Read all values of a preset (response service)
action: preset_manager.get_values
target:
  entity_id: sensor.motion_sensor_living_room_active_mode
data:
  mode: night        # optional, defaults to the currently effective mode
response_variable: values
```

## Reporting a problem

The integration ships **diagnostics**: on the entry under *Settings → Devices
& services → Preset Manager*, the three dot menu has **Download diagnostics**.
The file holds the modes with their conditions, the active mode and where it
came from, the parameters of every preset and every stored value — which is
everything needed to tell the causes of an `unknown` apart. Attach it to an
issue.

It contains no credentials; the integration has none. Values of a text
parameter in *password* mode are redacted.

## Upgrading

**0.1.x → 0.2.0** rearranges the config entries: every preset mode and every
blueprint used to be a config entry of its own, with the presets as subentries
of their preset mode. From 0.2.0 on there are three hubs and every object is a
subentry of the one that collects its kind.

There is **no migration** from 0.1.0. That release was withdrawn without
anybody running it, and a migration nobody needs is a path nobody tests. An
entry at schema 1.1 is refused with an error on the entry; delete it and add
the integration again. From 0.2.0 on — config entries at schema 2.1, the value
store at 1 — every change of either shape comes with a migration and is listed
in the [changelog](CHANGELOG.md).

A migration is only ever needed in one direction: an entry written by a *newer*
version than the one reading it is refused outright rather than guessed at.

## Development

```bash
uv venv --python 3.13 .venv
VIRTUAL_ENV=.venv uv pip install -r requirements_test.txt
.venv/bin/python -m pytest tests/ -q
.venv/bin/python -m ruff check custom_components tests
.venv/bin/python -m black --check custom_components tests
.venv/bin/python -m mypy custom_components
```

All four run in CI on every push and pull request, and all four have to be
clean. `mypy` covers `custom_components` only — the tests lean on fixtures
whose types are looser than anything the integration itself does.

The dashboard card lives in `frontend/` and is committed as a built bundle in
`custom_components/preset_manager/www/`, because Home Assistant serves it
straight from the integration:

```bash
cd frontend
npm ci
npm run typecheck
npm test
npm run build          # writes custom_components/preset_manager/www/
```

CI runs the same four and then checks that the committed bundle matches the
source, so a change to `frontend/` without a rebuild does not get through.
`frontend/` is not part of what HACS downloads — users get the bundle only.

To look at the card without Home Assistant:

```bash
npm run preview        # serves the repository; open the URL it prints
```

[frontend/preview.html](frontend/preview.html) puts every variant on one page —
both kinds of subject, every parameter type, an unset value, a preset that lost
its preset mode, the error state, and the same set again in a column too narrow
for it — against a fake `hass` that answers service calls, so switching a mode
or moving a slider really does redraw every card. Three Home Assistant elements
(`ha-card`, `ha-icon`, `ha-alert`) are stood in for; the card itself is the
built bundle, unmodified.

The brand images in `custom_components/preset_manager/brand/` are rendered from
[assets/preset_manager_icon.svg](assets/preset_manager_icon.svg) with
`rsvg-convert` (`brew install librsvg`):

```bash
rsvg-convert -w 256 -h 256 assets/preset_manager_icon.svg \
  -o custom_components/preset_manager/brand/icon.png
rsvg-convert -w 512 -h 512 assets/preset_manager_icon.svg \
  -o custom_components/preset_manager/brand/icon@2x.png
```

One icon serves both themes on purpose, so there are no `dark_*` variants, and
there is no separate logo either: Home Assistant falls back to the icon
wherever a logo would go.

Adding a new parameter type: register a `ParameterType` in `parameter_types.py` —
the config flow, the entities and the validation pick it up automatically.

The logic that picks the active mode lives in `sources.py`. Why each module is
built the way it is — and which alternatives were tried and rejected — lives in
its module docstring.

## Contributing

Issues and pull requests are welcome. For a bug, the
[diagnostics download](#reporting-a-problem) answers most of what I would ask
anyway. For a change, the tests, `ruff`, `black` and `mypy` have to be clean —
they run in CI on every pull request.

## License

[MIT](LICENSE) © Julien Streck
