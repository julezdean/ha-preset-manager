/**
 * The mode row: which mode is active, and switching to another one.
 *
 * Switching goes through `preset_manager.set_active_mode` with the mode *key*,
 * not through `select.select_option` with its display name - the key is what
 * survives a rename, and the service exists for exactly that reason.
 *
 * A mode that cannot be set is shown disabled with the reason underneath,
 * rather than clickable with an error afterwards: the integration refuses the
 * write while the automatic is on, on purpose, so that one click cannot
 * silently switch somebody's automation off.
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

function lockNote(context: CardContext, presetMode: PresetModeInfo | null): string | null {
  const reason = modeLockReason(context.hass, presetMode);
  if (reason === "automatic") return localize(context.hass, "automatic_hint");
  if (reason === "external" && presetMode?.source_entity) {
    const followed = context.hass.states[presetMode.source_entity];
    return localize(context.hass, "external_hint", {
      entity: followed?.attributes.friendly_name ?? presetMode.source_entity,
    });
  }
  // Disabled chips with nothing said about them are the worst of both: a
  // preset that lost its preset mode has no mode to be set to.
  if (reason === "missing" && context.subject.kind === "preset") {
    return localize(context.hass, "orphaned");
  }
  return null;
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
  const note = lockNote(context, presetMode);

  return html`
    <div class="section">
      ${context.config.modes.style === "dropdown"
        ? dropdown(context, modes, active, presetMode, locked)
        : chips(context, modes, active, presetMode, locked)}
      ${note ? html`<div class="note" style="margin-top:8px">${note}</div>` : nothing}
    </div>
  `;
}
