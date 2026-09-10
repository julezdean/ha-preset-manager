/**
 * What the card is about, resolved from the one entity the user named.
 *
 * A card is about a **preset**, and it takes any entity of one: its active
 * mode sensor, one of its values, one of its editors, its selector, its
 * switch. That is what keeps the simple case to one line, and it is only
 * possible because the structure says which entity belongs to what. Nothing
 * here parses a name.
 *
 * A preset mode has no card of its own. It is a definition plus the logic that
 * picks a mode, it is not operated, and what it computes is one sensor that
 * every core card can already draw. `presetModeOf` still finds it, because a
 * preset resolves against its modes and redraws when it switches.
 */

import type {
  BlueprintInfo,
  ParameterInfo,
  PresetInfo,
  PresetManagerConfig,
  PresetModeInfo,
} from "../types/data";

export interface PresetSubject {
  preset: PresetInfo;
  /** The preset mode it follows, `null` while it follows none. */
  presetMode: PresetModeInfo | null;
  blueprint: BlueprintInfo | null;
}

export type Subject = PresetSubject;

function presetSubject(
  config: PresetManagerConfig,
  preset: PresetInfo,
): PresetSubject {
  return {
    preset,
    presetMode:
      config.preset_modes.find((item) => item.id === preset.preset_mode) ?? null,
    blueprint:
      config.blueprints.find((item) => item.id === preset.blueprint) ?? null,
  };
}

/** Every entity id of a preset, whatever it is for. */
export function presetEntityIds(preset: PresetInfo): string[] {
  const ids: string[] = Object.values(preset.entities);
  for (const parameter of preset.parameters) {
    if (parameter.entity) ids.push(parameter.entity);
    ids.push(...Object.values(parameter.editors));
  }
  return ids;
}

/** Every entity id of a preset mode. */
export function presetModeEntityIds(presetMode: PresetModeInfo): string[] {
  const ids = Object.values(presetMode.entities);
  // The entity a preset mode follows is not ours, but the card shows what it
  // says, so it has to be watched like one of ours.
  if (presetMode.source_entity) ids.push(presetMode.source_entity);
  return ids;
}

/** Resolve the entity the user named to the preset it belongs to. */
export function resolveSubject(
  config: PresetManagerConfig,
  entityId: string,
): Subject | null {
  for (const preset of config.presets) {
    if (presetEntityIds(preset).includes(entityId)) {
      return presetSubject(config, preset);
    }
  }
  return null;
}

/**
 * Whether the entity belongs to a preset mode.
 *
 * Only to tell the user why there is no card for it. A wrong entity and an
 * entity of the wrong kind are different mistakes and deserve different
 * sentences.
 */
export function belongsToPresetMode(
  config: PresetManagerConfig,
  entityId: string,
): boolean {
  return config.preset_modes.some((item) =>
    presetModeEntityIds(item).includes(entityId),
  );
}

/**
 * The entities whose state changes have to redraw this card.
 *
 * `hass` is replaced on every state change in the whole instance, so a card
 * that redrew on each of them would redraw hundreds of times a minute for
 * nothing. This list is what turns that into "only when something we show
 * actually changed".
 */
export function watchedEntityIds(subject: Subject): string[] {
  const ids = presetEntityIds(subject.preset);
  // The mode of the preset mode decides what this preset resolves to, so a
  // switch over there has to redraw the card over here.
  if (subject.presetMode) ids.push(...presetModeEntityIds(subject.presetMode));
  return ids;
}

/** The parameters a card shows, in the order it shows them. */
export function orderedParameters(
  preset: PresetInfo,
  wanted: readonly string[] | null,
): ParameterInfo[] {
  if (!wanted) return preset.parameters;
  const byKey = new Map(preset.parameters.map((item) => [item.key, item]));
  return wanted
    .map((key) => byKey.get(key))
    .filter((item): item is ParameterInfo => item !== undefined);
}
