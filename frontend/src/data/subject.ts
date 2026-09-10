/**
 * What the card is about, resolved from the one entity the user named.
 *
 * A card takes a single `entity:` and works out the rest: point it at the mode
 * sensor of a preset mode and it becomes a preset mode card, point it at any
 * entity of a preset - its active mode sensor, one of its values, one of its
 * editors - and it becomes a card for that preset. That is what keeps the
 * simple case to one line, and it is only possible because the structure says
 * which entity belongs to what. Nothing here parses a name.
 */

import type {
  BlueprintInfo,
  ParameterInfo,
  PresetInfo,
  PresetManagerConfig,
  PresetModeInfo,
} from "../types/data";

export interface PresetSubject {
  kind: "preset";
  preset: PresetInfo;
  /** The preset mode it follows, `null` while it follows none. */
  presetMode: PresetModeInfo | null;
  blueprint: BlueprintInfo | null;
}

export interface PresetModeSubject {
  kind: "preset_mode";
  presetMode: PresetModeInfo;
  /** The presets following it, in configuration order. */
  presets: PresetInfo[];
}

export type Subject = PresetSubject | PresetModeSubject;

function presetSubject(
  config: PresetManagerConfig,
  preset: PresetInfo,
): PresetSubject {
  return {
    kind: "preset",
    preset,
    presetMode:
      config.preset_modes.find((item) => item.id === preset.preset_mode) ?? null,
    blueprint:
      config.blueprints.find((item) => item.id === preset.blueprint) ?? null,
  };
}

function presetModeSubject(
  config: PresetManagerConfig,
  presetMode: PresetModeInfo,
): PresetModeSubject {
  return {
    kind: "preset_mode",
    presetMode,
    presets: config.presets.filter((item) => item.preset_mode === presetMode.id),
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

/** Resolve the entity the user named to the object it belongs to. */
export function resolveSubject(
  config: PresetManagerConfig,
  entityId: string,
): Subject | null {
  for (const presetMode of config.preset_modes) {
    if (presetModeEntityIds(presetMode).includes(entityId)) {
      return presetModeSubject(config, presetMode);
    }
  }
  for (const preset of config.presets) {
    if (presetEntityIds(preset).includes(entityId)) {
      return presetSubject(config, preset);
    }
  }
  return null;
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
  if (subject.kind === "preset_mode") {
    const ids = presetModeEntityIds(subject.presetMode);
    for (const preset of subject.presets) ids.push(...presetEntityIds(preset));
    return ids;
  }
  const ids = presetEntityIds(subject.preset);
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
