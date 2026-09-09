/**
 * Validation and defaults, in one place.
 *
 * `setConfig` is the only chance to reject a configuration in a way the user
 * actually sees - Home Assistant renders whatever it throws as the card. So
 * everything that can be decided without `hass` is decided here, once, and the
 * rendering code never asks "was this set?" again.
 *
 * The errors say what to write, not what went wrong internally: a card that
 * reports `Cannot read properties of undefined` for a typo is the thing this
 * file exists to prevent.
 */

import { CARD_TYPE } from "./const";
import type {
  FooterItem,
  ModeVisibility,
  ParameterRowConfig,
  PresetManagerCardConfig,
  ResolvedConfig,
  ResolvedParameterRow,
} from "./types/config";

export class CardConfigError extends Error {}

const MODE_STYLES = ["chips", "dropdown"] as const;
const MODE_VISIBILITIES: ModeVisibility[] = ["always", "never", "manual"];
const EDITOR_MODES = ["picker", "active", "all"] as const;
const FOOTER_ITEMS: FooterItem[] = [
  "preset_mode",
  "blueprint",
  "source",
  "last_changed",
];

function fail(message: string): never {
  throw new CardConfigError(message);
}

function section(value: unknown, path: string): Record<string, unknown> {
  if (value === undefined || value === null) return {};
  if (typeof value !== "object" || Array.isArray(value)) {
    fail(`"${path}" has to be a group of options, for example "${path}: {visible: false}"`);
  }
  return value as Record<string, unknown>;
}

function bool(value: unknown, path: string, fallback: boolean): boolean {
  if (value === undefined) return fallback;
  if (typeof value !== "boolean") fail(`"${path}" has to be true or false`);
  return value;
}

/** A switch the user may leave alone, so the card can decide for itself. */
function optionalBool(value: unknown, path: string): boolean | undefined {
  if (value === undefined) return undefined;
  if (typeof value !== "boolean") fail(`"${path}" has to be true or false`);
  return value;
}

/**
 * When to show the mode row, with `true`/`false` as the obvious shorthands.
 *
 * Left unset it stays undefined, because what a card shows by default depends
 * on what its entity turned out to be, and that is not known here.
 */
function modeVisibility(value: unknown, path: string): ModeVisibility | undefined {
  if (value === undefined) return undefined;
  if (value === true) return "always";
  if (value === false) return "never";
  if (typeof value !== "string" || !MODE_VISIBILITIES.includes(value as ModeVisibility)) {
    fail(`"${path}" has to be true, false, or one of ${MODE_VISIBILITIES.join(", ")}`);
  }
  return value as ModeVisibility;
}

function text(value: unknown, path: string): string | undefined {
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "string") fail(`"${path}" has to be text`);
  return value;
}

function oneOf<T extends string>(
  value: unknown,
  path: string,
  allowed: readonly T[],
  fallback: T,
): T {
  if (value === undefined) return fallback;
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    fail(`"${path}" has to be one of ${allowed.join(", ")}`);
  }
  return value as T;
}

/** `string | false`: a text overriding the default, or the removal of it. */
function textOrFalse(value: unknown, path: string): string | false | undefined {
  if (value === undefined || value === null) return undefined;
  if (value === false) return false;
  if (typeof value !== "string") fail(`"${path}" has to be text, or false to hide it`);
  return value;
}

function colors(value: unknown, path: string): Record<string, string> {
  const raw = section(value, path);
  const result: Record<string, string> = {};
  for (const [key, colour] of Object.entries(raw)) {
    if (typeof colour !== "string") fail(`"${path}.${key}" has to be a colour`);
    result[key] = colour;
  }
  return result;
}

function parameterRows(value: unknown): ResolvedParameterRow[] | null {
  if (value === undefined || value === null) return null;
  if (!Array.isArray(value)) {
    fail('"values.parameters" has to be a list of parameter keys');
  }
  return (value as ParameterRowConfig[]).map((row, index) => {
    const path = `values.parameters[${index}]`;
    if (typeof row === "string") return { parameter: row };
    if (typeof row !== "object" || row === null || !("parameter" in row)) {
      fail(`"${path}" has to be a parameter key, or a group with a "parameter" key`);
    }
    const key = text((row as Record<string, unknown>).parameter, `${path}.parameter`);
    if (!key) fail(`"${path}.parameter" is required`);
    const resolved: ResolvedParameterRow = { parameter: key };
    const name = text((row as Record<string, unknown>).name, `${path}.name`);
    if (name !== undefined) resolved.name = name;
    const icon = textOrFalse((row as Record<string, unknown>).icon, `${path}.icon`);
    if (icon !== undefined) resolved.icon = icon;
    return resolved;
  });
}

function footerContent(value: unknown): FooterItem[] {
  if (value === undefined || value === null) return [];
  if (!Array.isArray(value)) fail('"footer.content" has to be a list');
  return value.map((item, index) =>
    oneOf(item, `footer.content[${index}]`, FOOTER_ITEMS, "preset_mode"),
  );
}

/**
 * Turn user configuration into the shape the card renders from.
 *
 * Unknown keys are left alone rather than rejected: Lovelace adds its own
 * (`view_layout`, `grid_options`, `visibility`), and a card that refused them
 * would break the moment the dashboard grew a feature.
 */
export function resolveConfig(raw: unknown): ResolvedConfig {
  if (typeof raw !== "object" || raw === null) {
    fail("The card needs a configuration.");
  }
  const config = raw as PresetManagerCardConfig;

  const entity = text(config.entity, "entity");
  if (!entity) {
    fail(
      'Pick an entity of Preset Manager, for example "entity: sensor.house_mode_mode" ' +
        'or the active mode sensor of a preset.',
    );
  }
  if (!entity.includes(".")) {
    fail(`"${entity}" is not an entity id.`);
  }

  const header = section(config.header, "header");
  const modes = section(config.modes, "modes");
  const values = section(config.values, "values");
  const editor = section(config.editor, "editor");
  const presets = section(config.presets, "presets");
  const footer = section(config.footer, "footer");

  const presetsEditable = bool(presets.editable, "presets.editable", false);
  const editorConfirm = bool(editor.confirm, "editor.confirm", false);

  const resolved: ResolvedConfig = {
    type: String(config.type ?? ""),
    entity,
    header: {
      visible: bool(header.visible, "header.visible", true),
      automatic: optionalBool(header.automatic, "header.automatic"),
      title: text(header.title, "header.title"),
      subtitle: textOrFalse(header.subtitle, "header.subtitle"),
      icon: textOrFalse(header.icon, "header.icon"),
      icon_color: text(header.icon_color, "header.icon_color"),
    },
    modes: {
      visible: modeVisibility(modes.visible, "modes.visible"),
      style: oneOf(modes.style, "modes.style", MODE_STYLES, "chips"),
      icons: bool(modes.icons, "modes.icons", true),
      colors: colors(modes.colors, "modes.colors"),
    },
    values: {
      visible: bool(values.visible, "values.visible", true),
      parameters: parameterRows(values.parameters),
      icons: bool(values.icons, "values.icons", false),
    },
    editor: {
      // A card that asks for confirmed editing is a card that has editors.
      enabled: bool(editor.enabled, "editor.enabled", editorConfirm),
      confirm: editorConfirm,
      mode: oneOf(editor.mode, "editor.mode", EDITOR_MODES, "picker"),
      style: oneOf(editor.style, "editor.style", MODE_STYLES, "chips"),
      default_mode: text(editor.default_mode, "editor.default_mode"),
    },
    presets: {
      // Asking for editable presets is asking to see them; a third switch to
      // turn on before anything appears would only be a way to get it wrong.
      visible: bool(presets.visible, "presets.visible", presetsEditable),
      values: bool(presets.values, "presets.values", presetsEditable),
      editable: presetsEditable,
    },
    footer: {
      // A footer that lists something is a footer that is wanted; asking for
      // `visible: true` on top of `content:` would only be a second switch for
      // the same decision.
      visible: bool(footer.visible, "footer.visible", footer.content !== undefined),
      content: footerContent(footer.content),
    },
    tap_action: config.tap_action,
    hold_action: config.hold_action,
    double_tap_action: config.double_tap_action,
  };

  if (resolved.footer.visible && !resolved.footer.content.length) {
    resolved.footer.content = ["preset_mode"];
  }
  return resolved;
}

/**
 * Drop everything the card would have assumed anyway.
 *
 * The form always hands back a complete object; saving that would bury the
 * three lines the user actually chose under every default the card has. The
 * comparison is against a freshly resolved default configuration, so the two
 * can never disagree about what a default is.
 */
export function pruneConfig(data: Record<string, unknown>): Record<string, unknown> {
  const type = String(data.type ?? `custom:${CARD_TYPE}`);
  const entity = typeof data.entity === "string" ? data.entity : "";
  let defaults: Record<string, unknown> = {};
  try {
    defaults = resolveConfig({
      type,
      entity: entity || "sensor.placeholder",
    }) as unknown as Record<string, unknown>;
  } catch (_err) {
    defaults = {};
  }

  const result: Record<string, unknown> = { type, entity };
  for (const [key, value] of Object.entries(data)) {
    if (key === "type" || key === "entity") continue;
    const kept = pruneValue(value, defaults[key]);
    if (kept !== undefined) result[key] = kept;
  }
  return result;
}

function pruneValue(value: unknown, fallback: unknown): unknown {
  if (value === undefined || value === null || value === "") return undefined;
  if (Array.isArray(value)) return value.length ? value : undefined;
  if (typeof value === "object") {
    const source = value as Record<string, unknown>;
    const base = (fallback ?? {}) as Record<string, unknown>;
    const kept: Record<string, unknown> = {};
    for (const [key, item] of Object.entries(source)) {
      const pruned = pruneValue(item, base[key]);
      if (pruned !== undefined && JSON.stringify(pruned) !== JSON.stringify(base[key])) {
        kept[key] = pruned;
      }
    }
    return Object.keys(kept).length ? kept : undefined;
  }
  return value === fallback ? undefined : value;
}
