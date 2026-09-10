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

/**
 * The switch saying whether a preset follows its preset mode.
 *
 * Only a preset has one. A preset mode gets its mode from its conditions or
 * from the entity it follows and is never operated, so a card for one shows
 * what it is doing and offers nothing to press.
 */
export function followsEntityId(subject: Subject): string | undefined {
  return subject.kind === "preset" ? subject.preset.entities.automatic : undefined;
}

/** The entity the mode of this subject is set on, if it can be set at all. */
export function modeSelectEntityId(subject: Subject): string | undefined {
  return subject.kind === "preset"
    ? subject.preset.entities.mode_selection
    : undefined;
}

/**
 * `true` while a preset takes the mode of its preset mode, `false` while it
 * has been taken out by hand, `null` where there is no such switch.
 */
export function followsPresetMode(
  hass: HomeAssistant,
  subject: Subject,
): boolean | null {
  const entity = stateOf(hass, followsEntityId(subject));
  if (!entity || hasNoValue(entity.state)) return null;
  return entity.state === "on";
}

/** Why the mode cannot be set here, or `null` when it can. */
export function modeLockReason(
  hass: HomeAssistant,
  subject: Subject,
): "computed" | "following" | "missing" | null {
  // A preset mode is not settable at all: its mode is computed, and that is
  // the whole point of it.
  if (subject.kind === "preset_mode") return "computed";
  // A preset without a preset mode has no modes to choose between.
  if (!subject.presetMode) return "missing";
  if (!modeSelectEntityId(subject)) return "missing";
  return followsPresetMode(hass, subject) ? "following" : null;
}

/** Whether an entity of the integration currently has a usable value. */
export function hasValue(
  hass: HomeAssistant,
  entityId: string | null | undefined,
): boolean {
  const entity = stateOf(hass, entityId);
  return entity !== undefined && !hasNoValue(entity.state);
}
