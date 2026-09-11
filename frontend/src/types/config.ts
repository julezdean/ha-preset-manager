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
  /**
   * The automatic switch, beside the name it belongs to. Only a preset has
   * one - a preset mode is not operated. Defaults to on.
   */
  automatic?: boolean;
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
 * `manual` means "while the mode can actually be set from here" - so on a
 * preset that is not following its preset mode, and never on a preset mode,
 * which is not operated at all. A row of chips nobody may click is a row that
 * only takes space, and this is the option that says so. `true` and `false`
 * are accepted for `always` and `never`.
 */
export type ModeVisibility = "always" | "never" | "manual";

export interface ModesConfig {
  /** Defaults to on. */
  visible?: boolean | ModeVisibility;
  icons?: boolean;
  /** Mode key -> colour, for the chip of that mode while it is active. */
  colors?: Record<string, string>;
}

/** One row of the value list: a parameter key, or that key with overrides. */
export type ParameterRowConfig =
  | string
  | { parameter: string; name?: string; icon?: string | false };

/**
 * What the value list shows, and whether it can be changed.
 *
 * One ladder, not a switch plus a choice: `active` is a card to read, the
 * other three are the ways of editing. Folding "can this card edit" into
 * "which mode" leaves no combination that contradicts itself.
 */
export type ValuesMode = "active" | "picker" | "edit" | "all";

export interface ValuesConfig {
  visible?: boolean;
  /**
   * `active` shows the values that are valid right now, read-only - which is
   * what a dashboard is for, and the default. `picker` puts a row of chips
   * above the list: *Active* first, and every other chip opens that mode's
   * values as editors. `edit` skips the picker and edits the active mode,
   * `all` shows every mode of every parameter at once.
   */
  mode?: ValuesMode;
  /** Which parameters to show, in which order. Omit for all of them. */
  parameters?: ParameterRowConfig[];
  icons?: boolean;
}

export interface PresetManagerCardConfig {
  type: string;
  /** Any entity of the integration; the card resolves what it belongs to. */
  entity?: string;
  header?: HeaderConfig;
  modes?: ModesConfig;
  values?: ValuesConfig;
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
  header: Required<Pick<HeaderConfig, "visible" | "automatic">> & HeaderConfig;
  modes: Required<Omit<ModesConfig, "colors" | "visible">> & {
    visible: ModeVisibility;
    colors: Record<string, string>;
  };
  values: {
    visible: boolean;
    mode: ValuesMode;
    parameters: ResolvedParameterRow[] | null;
    icons: boolean;
  };
  tap_action?: ActionConfig;
  hold_action?: ActionConfig;
  double_tap_action?: ActionConfig;
}
