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

/**
 * When the mode row is shown.
 *
 * `manual` means "while the mode can actually be set from here" - the automatic
 * is off, or there is none to be on. A row of chips nobody may click is a row
 * that only takes space, and this is the option that says so. `true` and
 * `false` are accepted for `always` and `never`.
 */
export type ModeVisibility = "always" | "never" | "manual";

export interface ModesConfig {
  /** Defaults to on. */
  visible?: boolean | ModeVisibility;
  /**
   * The automatic switch, on its own row above the modes. Two decisions, two
   * rows: one picks the mode, the other decides who picks it. It is always
   * the switch of the object the card is about - the conditions of a preset
   * mode, or whether a preset takes the mode of its preset mode. Defaults to
   * on wherever there is one.
   */
  automatic?: boolean;
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
  /** How `picker` is drawn. */
  style?: "chips" | "dropdown";
  /** Mode key the picker starts on; defaults to the active mode. */
  default_mode?: string;
  /**
   * Make editing a deliberate act: the card shows the values, offers a switch
   * to edit them, holds what is changed and writes it only when applied - then
   * goes back to the values. Implies `enabled`, because there is nothing to
   * switch into otherwise.
   */
  confirm?: boolean;
}

export interface PresetsConfig {
  /** On a preset mode card: list the presets that follow it. */
  visible?: boolean;
  /** Also show each preset's resolved values. */
  values?: boolean;
  /**
   * Turn those values into editors for the mode each preset is on. Implies
   * the two above - there is nothing to edit in a list of names.
   */
  editable?: boolean;
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
  modes: Required<Omit<ModesConfig, "colors" | "visible">> & {
    visible: ModeVisibility;
    colors: Record<string, string>;
  };
  values: { visible: boolean; parameters: ResolvedParameterRow[] | null; icons: boolean };
  editor: Required<Pick<EditorConfig, "enabled" | "mode" | "style" | "confirm">> &
    EditorConfig;
  presets: Required<PresetsConfig>;
  footer: { visible: boolean; content: FooterItem[] };
  tap_action?: ActionConfig;
  hold_action?: ActionConfig;
  double_tap_action?: ActionConfig;
}
