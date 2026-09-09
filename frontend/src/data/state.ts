/**
 * Reading the live state of what the structure describes.
 *
 * The active mode is taken from the `mode_key` attribute rather than from the
 * state text: the state is the *display name* of the mode and is translated
 * and renameable, while the key is the thing that stays. Everything else in
 * this integration keys off it, and so does the card.
 */

import type { ModeInfo, PresetModeInfo } from "../types/data";
import type { HassEntity, HomeAssistant } from "../types/ha";
import type { Subject } from "./subject";
import { isUnavailable, stateOf } from "../util/ha";

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
 * `true` while a preset mode follows its conditions, `false` while it has been
 * taken over by hand, `null` when there is no automatic at all.
 */
export function automaticState(
  hass: HomeAssistant,
  presetMode: PresetModeInfo | null,
): boolean | null {
  const entity = stateOf(hass, presetMode?.entities.automatic);
  if (!entity || isUnavailable(entity.state)) return null;
  return entity.state === "on";
}

/** Why the mode cannot be set here, or `null` when it can. */
export function modeLockReason(
  hass: HomeAssistant,
  presetMode: PresetModeInfo | null,
): "external" | "automatic" | "missing" | null {
  if (!presetMode) return "missing";
  // The integration refuses the write in both cases and says why. The card
  // shows the same reason before the click instead of after it.
  if (presetMode.source_entity) return "external";
  if (!presetMode.entities.active_mode) return "missing";
  return automaticState(hass, presetMode) ? "automatic" : null;
}

/** Whether an entity of the integration currently has a usable value. */
export function hasValue(
  hass: HomeAssistant,
  entityId: string | null | undefined,
): boolean {
  const entity = stateOf(hass, entityId);
  return entity !== undefined && !isUnavailable(entity.state);
}
