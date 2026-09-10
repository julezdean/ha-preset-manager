/**
 * Which mode is active, and - on a preset - who decides that.
 *
 * The two kinds of card differ here, because the two objects do. **A preset
 * mode is not operated**: its mode comes from its conditions or from the
 * entity it follows, so its modes are drawn as a list that says which of them
 * is on, and nothing on it can be pressed. **A preset is**: one switch says
 * whether it takes the mode of its preset mode, and with that off the chips
 * below set its own.
 *
 * Nothing here ever reaches into the dimension from a preset. A click on a
 * card named after one preset must not change what every other preset of that
 * dimension does, and now it structurally cannot - there is nothing to write
 * to on the other side.
 *
 * Setting goes through `preset_manager.set_active_mode` with the mode *key*,
 * not through `select.select_option` with its display name - the key is what
 * survives a rename, and the service exists for exactly that reason.
 */

import { html, nothing, type TemplateResult } from "lit";

import {
  activeModeKey,
  followsEntityId,
  followsPresetMode,
  modeLockReason,
  modeSelectEntityId,
  modesOf,
} from "../data/state";
import { localize } from "../localize";
import { icon } from "./icon";
import type { CardContext } from "./context";
import type { ModeInfo } from "../types/data";

export function modesVisible(context: CardContext): boolean {
  const setting = context.config.modes.visible;
  if (setting === "manual") {
    // Exactly while a click would do something - so on a preset that is not
    // following its preset mode, and never on a preset mode.
    return modeLockReason(context.hass, context.subject) === null;
  }
  return setting !== "never";
}

function selectMode(context: CardContext, key: string) {
  const entityId = modeSelectEntityId(context.subject);
  if (!entityId) return;
  context.call(
    context.hass.callService(
      "preset_manager",
      "set_active_mode",
      { mode: key },
      { entity_id: entityId },
    ),
  );
}

/** The switch handing this preset back to its preset mode, or taking it out. */
function followsRow(context: CardContext): TemplateResult | typeof nothing {
  const { hass, subject, config } = context;
  if (!config.modes.automatic) return nothing;
  const entityId = followsEntityId(subject);
  if (!entityId) return nothing;
  const on = followsPresetMode(hass, subject);
  const label = localize(hass, "follows_preset_mode");

  return html`
    <label class="toolbar">
      <span class="toolbar-label">${label}</span>
      <span class="switch">
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
      </span>
    </label>
  `;
}

function chips(
  context: CardContext,
  modes: ModeInfo[],
  active: string | null,
  locked: boolean,
): TemplateResult {
  const { config } = context;
  return html`
    <div class="chips" role="group">
      ${modes.map((mode) => {
        const isActive = mode.key === active;
        const colour = config.modes.colors[mode.key];
        return html`
          <button
            class="chip"
            type="button"
            aria-pressed=${isActive ? "true" : "false"}
            ?disabled=${locked}
            style=${colour ? `--pm-chip-color: ${colour}` : ""}
            @click=${() => selectMode(context, mode.key)}
          >
            ${config.modes.icons ? icon(mode.icon) : nothing}
            <span>${mode.name}</span>
          </button>
        `;
      })}
    </div>
  `;
}

function dropdown(
  context: CardContext,
  modes: ModeInfo[],
  active: string | null,
  locked: boolean,
): TemplateResult {
  return html`
    <select
      class="select-input"
      aria-label=${localize(context.hass, "mode")}
      ?disabled=${locked}
      @change=${(event: Event) =>
        selectMode(context, (event.target as HTMLSelectElement).value)}
    >
      ${active === null
        ? html`<option value="" selected>${localize(context.hass, "no_mode")}</option>`
        : nothing}
      ${modes.map(
        (mode) => html`
          <option value=${mode.key} ?selected=${mode.key === active}>
            ${mode.name}
          </option>
        `,
      )}
    </select>
  `;
}

/**
 * The modes of a preset mode, as a list rather than as controls.
 *
 * They are not buttons and not disabled buttons: a disabled control says
 * "later, or elsewhere", and there is no later here. What the list is good for
 * is the thing the mode name alone does not say - which modes exist at all.
 */
function modeList(
  context: CardContext,
  modes: ModeInfo[],
  active: string | null,
): TemplateResult {
  const { config } = context;
  return html`
    <div class="chips" role="list">
      ${modes.map((mode) => {
        const colour = config.modes.colors[mode.key];
        return html`
          <span
            class="chip"
            role="listitem"
            aria-current=${mode.key === active ? "true" : nothing}
            aria-pressed=${mode.key === active ? "true" : "false"}
            style=${colour ? `--pm-chip-color: ${colour}` : ""}
          >
            ${config.modes.icons ? icon(mode.icon) : nothing}
            <span>${mode.name}</span>
          </span>
        `;
      })}
    </div>
  `;
}

/** The mode row proper: the chips or the dropdown, or why there are neither. */
function modeControl(context: CardContext): TemplateResult {
  const modes = modesOf(context.subject);
  if (!modes.length) {
    return html`<div class="note">${localize(context.hass, "no_modes")}</div>`;
  }

  const active = activeModeKey(context.hass, context.subject);
  if (context.subject.kind === "preset_mode") {
    return modeList(context, modes, active);
  }

  const locked = modeLockReason(context.hass, context.subject) !== null;
  // No line explaining why a locked row is locked. Every version of that
  // sentence said again what the switch above and the header say, and repeated
  // it on every card and every render. The chips being visibly disabled is the
  // part that was not already written down.
  return context.config.modes.style === "dropdown"
    ? dropdown(context, modes, active, locked)
    : chips(context, modes, active, locked);
}

export function renderModes(context: CardContext): TemplateResult | typeof nothing {
  const follows = followsRow(context);
  const control = modesVisible(context) ? modeControl(context) : nothing;
  if (follows === nothing && control === nothing) return nothing;

  return html`<div class="section rows">${follows}${control}</div>`;
}
