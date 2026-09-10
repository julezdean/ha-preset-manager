/**
 * The payload of the `preset_manager/config` websocket command.
 *
 * It carries the *structure* and nothing else: which modes exist, which
 * parameters a preset has, and which entity is which. Values are read from
 * the states, so a moved slider, a switched mode and a rename arrive without
 * asking again.
 *
 * Mirrors `custom_components/preset_manager/websocket_api.py`. The two ship in
 * one version and are not separable by a user, which is why this is allowed to
 * change with a release.
 */

/** One mode of a preset mode, without the conditions that select it. */
export interface ModeInfo {
  key: string;
  name: string;
  icon: string | null;
}

export interface PresetModeInfo {
  id: string;
  name: string;
  device_id: string | null;
  modes: ModeInfo[];
  /** Set while the whole preset mode follows another entity. */
  source_entity: string | null;
  has_conditions: boolean;
  /**
   * One entity, and only one: a preset mode reports which mode is active and
   * is never operated. Everything a hand reaches sits on the presets.
   */
  entities: { mode?: string };
}

export type ParameterType =
  | "number"
  | "boolean"
  | "text"
  | "select"
  | "datetime"
  | "date"
  | "time";

export interface ParameterInfo {
  key: string;
  name: string;
  type: ParameterType;
  /** The sensor carrying the value of whichever mode is active. */
  entity: string | null;
  /** Mode key -> the entity editing this parameter in that mode. */
  editors: Record<string, string>;
}

export interface PresetInfo {
  id: string;
  name: string;
  device_id: string | null;
  /** Subentry id of the preset mode it follows, `null` while it follows none. */
  preset_mode: string | null;
  blueprint: string | null;
  modes: ModeInfo[];
  parameters: ParameterInfo[];
  entities: {
    /** The sensor naming the mode this preset resolves right now. */
    active_mode?: string;
    /** Its own mode selector, writable while its automatic is off. */
    mode_selection?: string;
    /** Its own automatic: whether it takes the mode of its preset mode. */
    automatic?: string;
  };
}

export interface BlueprintInfo {
  id: string;
  name: string;
}

export interface PresetManagerConfig {
  preset_modes: PresetModeInfo[];
  presets: PresetInfo[];
  blueprints: BlueprintInfo[];
}
