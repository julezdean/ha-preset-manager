/**
 * Reading the live state of what the structure describes.
 *
 * The active mode is taken from the `mode_key` attribute rather than from the
 * state text: the state is the *display name* of the mode and is translated
 * and renameable, while the key is the thing that stays. Everything else in
 * this integration keys off it, and so does the card.
 */

import type { ModeInfo, PresetInfo } from "../types/data";
import type { HassEntity, HomeAssistant } from "../types/ha";
import type { Subject } from "./subject";
import { hasNoValue, stateOf } from "../util/ha";

/** Attribute carrying the stable key of the active mode. Frozen surface. */
const ATTR_MODE_KEY = "mode_key";

function modeKeyOf(entity: HassEntity | undefined): string | null {
  const key = entity?.attributes[ATTR_MODE_KEY];
  return typeof key === "string" && key ? key : null;
}

/** The entity whose `mode_key` says what is active for this subject. */
export function modeSourceEntityId(subject: Subject): string | undefined {
  return subject.kind === "preset_mode"
    ? subject.presetMode.entities.mode
    : subject.preset.entities.active_mode;
}

export function activeModeKey(
  hass: HomeAssistant,
  subject: Subject,
): string | null {
  return modeKeyOf(stateOf(hass, modeSourceEntityId(subject)));
}

/**
 * The mode one preset resolves right now, read from its own sensor.
 *
 * For a preset that a card lists rather than is about - the same key, taken
 * without building a subject for it.
 */
export function presetModeKey(
  hass: HomeAssistant,
  preset: PresetInfo,
): string | null {
  return modeKeyOf(stateOf(hass, preset.entities.active_mode));
}

export function modesOf(subject: Subject): ModeInfo[] {
  return subject.kind === "preset_mode"
    ? subject.presetMode.modes
    : subject.preset.modes;
}

export function activeMode(
  hass: HomeAssistant,
  subject: Subject,
): ModeInfo | null {
  const key = activeModeKey(hass, subject);
  if (!key) return null;
  return modesOf(subject).find((mode) => mode.key === key) ?? null;
}

/** The switch deciding who sets the mode of this subject, if there is one. */
export function automaticEntityId(subject: Subject): string | undefined {
  // Both kinds have one, and each has its own: a preset mode switches between
  // its conditions and the hand, a preset between its preset mode and the
  // hand. A card therefore never reaches past the object it is about.
  return subject.kind === "preset_mode"
    ? subject.presetMode.entities.automatic
    : subject.preset.entities.automatic;
}

/** The entity the mode of this subject is set on, if it can be set at all. */
export function modeSelectEntityId(subject: Subject): string | undefined {
  return subject.kind === "preset_mode"
    ? subject.presetMode.entities.active_mode
    : subject.preset.entities.mode_selection;
}

/**
 * `true` while the mode is decided elsewhere, `false` while it has been taken
 * over by hand, `null` when there is no automatic at all.
 */
export function automaticState(
  hass: HomeAssistant,
  subject: Subject,
): boolean | null {
  const entity = stateOf(hass, automaticEntityId(subject));
  if (!entity || hasNoValue(entity.state)) return null;
  return entity.state === "on";
}

/** Why the mode cannot be set here, or `null` when it can. */
export function modeLockReason(
  hass: HomeAssistant,
  subject: Subject,
): "external" | "automatic" | "missing" | null {
  // The integration refuses the write and says why. The card shows the same
  // reason before the click instead of after it.
  if (subject.kind === "preset_mode" && subject.presetMode.source_entity) {
    return "external";
  }
  // A preset without a preset mode has no mode to set - and an external
  // preset mode does not lock its presets: standing alone is exactly how one
  // of them gets out from under an entity it cannot argue with.
  if (subject.kind === "preset" && !subject.presetMode) return "missing";
  if (!modeSelectEntityId(subject)) return "missing";
  return automaticState(hass, subject) ? "automatic" : null;
}

/** Whether an entity of the integration currently has a usable value. */
export function hasValue(
  hass: HomeAssistant,
  entityId: string | null | undefined,
): boolean {
  const entity = stateOf(hass, entityId);
  return entity !== undefined && !hasNoValue(entity.state);
}
