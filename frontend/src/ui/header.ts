/**
 * The header: what this card is about, and what it is doing right now.
 *
 * The icon is the active mode's icon wherever there is one. Mode icons are
 * configured in the flow and were until now stored and unused; here they are
 * the one place the card carries a colour, which is why the design gets away
 * with a single accent everywhere else.
 *
 * Nothing here is a control. The automatic switch used to sit in the corner of
 * this row, which cost the header its keyboard: a row containing a switch must
 * not also be a button, so `tap_action` was reachable with the mouse and with
 * nothing else. It has a row of its own above the modes now, where it belongs
 * anyway - it decides who picks the mode.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeMode, followsPresetMode } from "../data/state";
import { localize } from "../localize";
import { DEFAULT_PRESET_ICON, DEFAULT_PRESET_MODE_ICON, icon } from "./icon";
import type { CardContext } from "./context";

/** The colour the active mode paints the icon and its chip with. */
export function modeColor(context: CardContext): string | undefined {
  const mode = activeMode(context.hass, context.subject);
  return mode ? context.config.modes.colors[mode.key] : undefined;
}

function headerIcon(context: CardContext): string | null {
  const configured = context.config.header.icon;
  if (configured === false) return null;
  if (configured) return configured;
  const mode = activeMode(context.hass, context.subject);
  if (mode?.icon) return mode.icon;
  return context.subject.kind === "preset_mode"
    ? DEFAULT_PRESET_MODE_ICON
    : DEFAULT_PRESET_ICON;
}

function defaultTitle(context: CardContext): string {
  return context.subject.kind === "preset_mode"
    ? context.subject.presetMode.name
    : context.subject.preset.name;
}

/**
 * The second line, which answers "what is going on" in one glance.
 *
 * A preset says which mode is effective and which preset mode decided it; a
 * preset mode says its own mode, or the entity it handed itself to.
 */
function defaultSubtitle(context: CardContext): string {
  const { hass, subject } = context;
  const mode = activeMode(hass, subject);
  const modeName = mode?.name ?? localize(hass, "no_mode");

  if (subject.kind === "preset_mode") {
    const { presetMode } = subject;
    if (presetMode.source_entity) {
      const followed = hass.states[presetMode.source_entity];
      const name = followed?.attributes.friendly_name ?? presetMode.source_entity;
      return `${modeName} · ${localize(hass, "follows", { entity: name })}`;
    }
    return modeName;
  }

  // The preset mode a preset follows is not news on every render - the footer
  // carries it where it is wanted. What is news is that there is none, and
  // that this preset has stopped taking the mode from it: a preset showing
  // something other than its dimension is the one state worth a word here,
  // and the row that caused it can be switched off in the configuration.
  if (!subject.presetMode) {
    return `${modeName} · ${localize(hass, "no_preset_mode")}`;
  }
  return followsPresetMode(hass, subject) === false
    ? `${modeName} · ${localize(hass, "manual")}`
    : modeName;
}

export function renderHeader(context: CardContext): TemplateResult | typeof nothing {
  const { config } = context;
  if (!config.header.visible) return nothing;

  const name = headerIcon(context);
  const subtitle =
    config.header.subtitle === false
      ? null
      : (config.header.subtitle ?? defaultSubtitle(context));
  const colour = config.header.icon_color ?? modeColor(context);
  const { tappable } = context;

  return html`
    <div
      class="header section ${tappable ? "tappable" : ""}"
      style=${colour ? `--pm-icon-color: ${colour}` : ""}
      role=${tappable ? "button" : nothing}
      tabindex=${tappable ? "0" : nothing}
      @pointerdown=${() => context.onHeaderDown()}
      @pointerup=${() => context.onHeaderUp()}
      @pointercancel=${() => context.onHeaderUp()}
      @click=${() => context.onHeaderClick()}
      @keydown=${(event: KeyboardEvent) => {
        if (!tappable || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        context.onHeaderClick();
      }}
    >
      ${name
        ? html`<div class="icon">${icon(name)}</div>`
        : nothing}
      <div class="titles">
        <div class="title">${config.header.title ?? defaultTitle(context)}</div>
        ${subtitle ? html`<div class="subtitle">${subtitle}</div>` : nothing}
      </div>
    </div>
  `;
}
