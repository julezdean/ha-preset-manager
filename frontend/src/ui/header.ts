/**
 * The header: what this card is about, and what it is doing right now.
 *
 * The icon is the active mode's icon wherever there is one. Mode icons are
 * configured in the flow and were until now stored and unused; here they are
 * the one place the card carries a colour, which is why the design gets away
 * with a single accent everywhere else.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeMode, automaticState } from "../data/state";
import { localize } from "../localize";
import { DEFAULT_PRESET_ICON, DEFAULT_PRESET_MODE_ICON, icon } from "./icon";
import { modesVisible } from "./modes";
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

  if (!subject.presetMode) {
    return `${modeName} · ${localize(hass, "no_preset_mode")}`;
  }
  return `${modeName} · ${subject.presetMode.name}`;
}

function automaticToggle(context: CardContext): TemplateResult | typeof nothing {
  const { hass, subject } = context;
  // Both kinds of subject carry one, which is why this needs no branch: a
  // preset names the preset mode it follows, a preset mode is its own.
  const presetMode = subject.presetMode;
  if (!presetMode?.entities.automatic) return nothing;
  const entityId = presetMode.entities.automatic;
  const on = automaticState(hass, presetMode);
  const label = localize(hass, "automatic");

  // Stops here, or the tap action of the header would fire on top of the
  // toggle - and "open more info" is not what a click on a switch means.
  const swallow = (event: Event) => event.stopPropagation();

  return html`
    <label
      class="switch"
      title=${label}
      @click=${swallow}
      @pointerdown=${swallow}
      @pointerup=${swallow}
      @keydown=${swallow}
    >
      <input
        type="checkbox"
        role="switch"
        aria-label=${label}
        .checked=${on === true}
        .disabled=${on === null}
        @change=${(event: Event) => {
          const checked = (event.target as HTMLInputElement).checked;
          context.call(
            hass.callService(
              "switch",
              checked ? "turn_on" : "turn_off",
              {},
              { entity_id: entityId },
            ),
          );
        }}
      />
    </label>
  `;
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

  // The automatic belongs to a preset mode, and switching it changes what
  // every preset of that dimension does. So a preset card only offers it when
  // it offers the modes as well: a card that can switch the mode has to be
  // able to reach the switch that gates it, and a card that only reads values
  // has no business owning that decision.
  const controls =
    context.subject.kind === "preset_mode" || modesVisible(context)
      ? automaticToggle(context)
      : nothing;

  // A row that contains a switch must not also be a button: nesting one
  // control inside another is neither valid nor announceable. The tap action
  // still works with the mouse; the keyboard reaches the switch instead, which
  // is the control that actually changes something.
  const asButton = tappable && controls === nothing;

  return html`
    <div
      class="header section ${tappable ? "tappable" : ""}"
      style=${colour ? `--pm-icon-color: ${colour}` : ""}
      role=${asButton ? "button" : nothing}
      tabindex=${asButton ? "0" : nothing}
      @pointerdown=${() => context.onHeaderDown()}
      @pointerup=${() => context.onHeaderUp()}
      @pointercancel=${() => context.onHeaderUp()}
      @click=${() => context.onHeaderClick()}
      @keydown=${(event: KeyboardEvent) => {
        if (!asButton || (event.key !== "Enter" && event.key !== " ")) return;
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
      ${controls === nothing ? nothing : html`<div class="header-end">${controls}</div>`}
    </div>
  `;
}
