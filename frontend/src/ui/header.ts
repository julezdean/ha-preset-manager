/**
 * The header: what this card is about, and what it is doing right now.
 *
 * The icon is the active mode's icon wherever there is one. Mode icons are
 * configured in the flow and were until now stored and unused; here they are
 * the one place the card carries a colour, which is why the design gets away
 * with a single accent everywhere else.
 *
 * The automatic switch sits here because it belongs to *this* object. It used
 * to sit here belonging to another one - a preset card carrying the switch of
 * its preset mode - and that, not the position, was what made it wrong.
 *
 * **The row is not the button; the name is.** A row containing a switch must
 * not also be a button: nesting one control inside another is neither valid
 * nor announceable, and the card paid for that with its keyboard - `tap_action`
 * was reachable with the mouse and with nothing else. Icon and titles are the
 * button now, the switch is its sibling, and both answer to the keyboard. A
 * real `<button>` also fires `click` on Enter and Space by itself, so there is
 * no key handling left here at all.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeMode, followsEntityId, followsPresetMode } from "../data/state";
import { localize } from "../localize";
import { DEFAULT_PRESET_ICON, icon } from "./icon";
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
  return mode?.icon ?? DEFAULT_PRESET_ICON;
}

function defaultTitle(context: CardContext): string {
  return context.subject.preset.name;
}

/**
 * The second line, which answers "what is going on" in one glance: which mode
 * is effective, and where it comes from.
 */
function defaultSubtitle(context: CardContext): string {
  const { hass, subject } = context;
  const mode = activeMode(hass, subject);
  const modeName = mode?.name ?? localize(hass, "no_mode");

  // The preset mode a preset follows is not news on every render - the footer
  // carries it where it is wanted. Where the mode *comes from* is, on every
  // render: both states are named, not only the deviating one, because there
  // is a third - a switch that is missing or unavailable - and leaving the
  // normal case blank would hide it behind the same blank.
  if (!subject.presetMode) {
    return `${modeName} · ${localize(hass, "no_preset_mode")}`;
  }
  const follows = followsPresetMode(hass, subject);
  if (follows === null) return modeName;
  return `${modeName} · ${localize(hass, follows ? "automatic" : "manual")}`;
}

/**
 * The automatic of this object, as a bare toggle.
 *
 * No visible label: it can only ever belong to the object named beside it, so
 * the row already says what it switches - which is exactly what it could not
 * say while it belonged to something else. Screen readers get the word through
 * `aria-label`, and pointers get it as a tooltip; neither costs any width.
 */
function automaticToggle(context: CardContext): TemplateResult | typeof nothing {
  const { hass, subject, config } = context;
  if (!config.header.automatic) return nothing;
  const entityId = followsEntityId(subject);
  if (!entityId) return nothing;
  const on = followsPresetMode(hass, subject);
  const label = localize(hass, "mode_automatic");

  return html`
    <label class="switch-field">
      <span class="switch">
        <input
          type="checkbox"
          role="switch"
          aria-label=${label}
          title=${label}
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
      </span>
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
  const toggle = automaticToggle(context);

  const inside = html`
    ${name ? html`<div class="icon">${icon(name)}</div>` : nothing}
    <div class="titles">
      <div class="title">${config.header.title ?? defaultTitle(context)}</div>
      ${subtitle ? html`<div class="subtitle">${subtitle}</div>` : nothing}
    </div>
  `;

  return html`
    <div class="header section" style=${colour ? `--pm-icon-color: ${colour}` : ""}>
      ${tappable
        ? html`
            <button
              class="header-main tappable"
              type="button"
              @pointerdown=${() => context.onHeaderDown()}
              @pointerup=${() => context.onHeaderUp()}
              @pointercancel=${() => context.onHeaderUp()}
              @click=${() => context.onHeaderClick()}
            >
              ${inside}
            </button>
          `
        : html`<div class="header-main">${inside}</div>`}
      ${toggle === nothing ? nothing : html`<div class="header-end">${toggle}</div>`}
    </div>
  `;
}
