/**
 * The mode row: which mode is active, and switching to another one.
 *
 * Switching goes through `preset_manager.set_active_mode` with the mode *key*,
 * not through `select.select_option` with its display name - the key is what
 * survives a rename, and the service exists for exactly that reason.
 *
 * A mode that cannot be set is shown disabled rather than clickable with an
 * error afterwards: the integration refuses the write while the automatic is
 * on, on purpose, so that one click cannot silently switch somebody's
 * automation off. Disabled and nothing else - the reason used to be spelled
 * out underneath, and every version of that sentence repeated the header.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeModeKey, modeLockReason, modesOf } from "../data/state";
import { localize } from "../localize";
import { icon } from "./icon";
import type { CardContext } from "./context";
import type { ModeInfo, PresetModeInfo } from "../types/data";

/** The preset mode this card's mode row drives, if any. */
export function drivenPresetMode(context: CardContext): PresetModeInfo | null {
  // A preset mode drives itself; a preset drives the one it follows, which is
  // the same field on both and may be missing on a preset.
  return context.subject.presetMode;
}

export function modesVisible(context: CardContext): boolean {
  const { visible } = context.config.modes;
  if (visible === "never") return false;
  if (visible === "always") return true;
  // Automatic: a preset mode *is* its modes, so it shows them. A preset shows
  // its values, and the mode row would let a card named after one preset
  // change what every other preset of that dimension does.
  return context.subject.kind === "preset_mode";
}

function selectMode(context: CardContext, presetMode: PresetModeInfo, key: string) {
  const entityId = presetMode.entities.active_mode;
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

function chips(
  context: CardContext,
  modes: ModeInfo[],
  active: string | null,
  presetMode: PresetModeInfo | null,
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
            @click=${() => presetMode && selectMode(context, presetMode, mode.key)}
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
  presetMode: PresetModeInfo | null,
  locked: boolean,
): TemplateResult {
  return html`
    <select
      class="select-input"
      aria-label=${localize(context.hass, "preset_mode")}
      ?disabled=${locked}
      @change=${(event: Event) => {
        const value = (event.target as HTMLSelectElement).value;
        if (presetMode) selectMode(context, presetMode, value);
      }}
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

export function renderModes(context: CardContext): TemplateResult | typeof nothing {
  if (!modesVisible(context)) return nothing;

  const modes = modesOf(context.subject);
  if (!modes.length) {
    return html`<div class="section note">
      ${localize(context.hass, "no_modes")}
    </div>`;
  }

  const presetMode = drivenPresetMode(context);
  const active = activeModeKey(context.hass, context.subject);
  const locked = modeLockReason(context.hass, presetMode) !== null;

  // No line explaining why a locked row is locked. Every version of that
  // sentence said again what the header says one line above - which mode is
  // active, that it follows an entity, that there is no preset mode - and
  // repeated it on every card and every render. The chips being visibly
  // disabled is the part that was not already written down.
  return html`
    <div class="section">
      ${context.config.modes.style === "dropdown"
        ? dropdown(context, modes, active, presetMode, locked)
        : chips(context, modes, active, presetMode, locked)}
    </div>
  `;
}
