/**
 * The configuration a user writes, and the shape the card works with.
 *
 * Two types, on purpose. {@link PresetManagerCardConfig} is what YAML looks
 * like: every section optional, every field optional, nothing to fill in for
 * the common case. {@link ResolvedConfig} is what the rendering code sees:
 * every field present, every default applied, once, in `setConfig`. Nothing
 * below the normalisation ever writes `?? true` again.
 */

import type { ActionConfig } from "./ha";

/** How much of the card is visible when the card decides for itself. */
export type Visibility = "auto" | "always" | "never";

export interface HeaderConfig {
  visible?: boolean;
  /** Overrides the name of the preset or preset mode. */
  title?: string;
  /** Overrides the second line; `false` removes it. */
  subtitle?: string | false;
  /** Overrides the icon; `false` removes it. */
  icon?: string | false;
  icon_color?: string;
}

export interface ModesConfig {
  /** `auto`: shown on a preset mode, hidden on a preset. */
  visible?: Visibility;
  style?: "chips" | "dropdown";
  icons?: boolean;
  /** Mode key -> colour, for the chip of that mode while it is active. */
  colors?: Record<string, string>;
}

/** One row of the value list: a parameter key, or that key with overrides. */
export type ParameterRowConfig =
  | string
  | { parameter: string; name?: string; icon?: string | false };

export interface ValuesConfig {
  visible?: boolean;
  /** Which parameters to show, in which order. Omit for all of them. */
  parameters?: ParameterRowConfig[];
  icons?: boolean;
}

export interface EditorConfig {
  /**
   * Off by default. The editors are `EntityCategory.CONFIG` entities - they
   * are how a preset is set up, not how it is operated.
   */
  enabled?: boolean;
  /**
   * `picker` lets the card choose which mode is edited, `active` edits the
   * mode that is active right now, `all` shows every mode of every parameter.
   */
  mode?: "picker" | "active" | "all";
  /** Mode key the picker starts on; defaults to the active mode. */
  default_mode?: string;
}

export interface PresetsConfig {
  /** On a preset mode card: list the presets that follow it. */
  visible?: boolean;
  /** Also show each preset's resolved values. */
  values?: boolean;
}

export type FooterItem =
  | "preset_mode"
  | "blueprint"
  | "source"
  | "last_changed";

export interface FooterConfig {
  visible?: boolean;
  content?: FooterItem[];
}

export interface PresetManagerCardConfig {
  type: string;
  /** Any entity of the integration; the card resolves what it belongs to. */
  entity?: string;
  header?: HeaderConfig;
  modes?: ModesConfig;
  values?: ValuesConfig;
  editor?: EditorConfig;
  presets?: PresetsConfig;
  footer?: FooterConfig;
  /** Home Assistant's own action keys, at the top level as everywhere else. */
  tap_action?: ActionConfig;
  hold_action?: ActionConfig;
  double_tap_action?: ActionConfig;
}

export interface ResolvedParameterRow {
  parameter: string;
  name?: string;
  icon?: string | false;
}

export interface ResolvedConfig {
  type: string;
  entity: string;
  header: Required<Pick<HeaderConfig, "visible">> & HeaderConfig;
  modes: Required<Omit<ModesConfig, "colors">> & { colors: Record<string, string> };
  values: { visible: boolean; parameters: ResolvedParameterRow[] | null; icons: boolean };
  editor: Required<Pick<EditorConfig, "enabled" | "mode">> & EditorConfig;
  presets: Required<PresetsConfig>;
  footer: { visible: boolean; content: FooterItem[] };
  tap_action?: ActionConfig;
  hold_action?: ActionConfig;
  double_tap_action?: ActionConfig;
}
