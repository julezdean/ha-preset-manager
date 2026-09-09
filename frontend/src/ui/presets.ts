/**
 * The presets that follow a preset mode.
 *
 * Off by default: a preset mode card is about the dimension, and one that
 * listed every device following it would grow with the setup rather than with
 * the user's intent. Turned on, it answers the one question the entity list
 * cannot - "what does 'Night' actually mean here" - because it can show each
 * preset with the values that are valid right now.
 */

import { html, nothing, type TemplateResult } from "lit";

import { localize, localizeCount } from "../localize";
import { formatState, isUnavailable, showMoreInfo, stateOf, UNKNOWN } from "../util/ha";
import type { CardContext } from "./context";
import type { PresetInfo } from "../types/data";

function valueRows(context: CardContext, preset: PresetInfo): TemplateResult[] {
  return preset.parameters.map((parameter) => {
    const entity = stateOf(context.hass, parameter.entity);
    let text: string;
    let muted = true;
    if (!entity) text = localize(context.hass, "unavailable");
    else if (entity.state === UNKNOWN) text = localize(context.hass, "not_set");
    else if (isUnavailable(entity.state)) text = localize(context.hass, "unavailable");
    else {
      text = formatState(context.hass, entity);
      muted = false;
    }
    return html`
      <div class="row">
        <div class="row-label"><span>${parameter.name}</span></div>
        <div class="row-value ${muted ? "muted" : ""}">${text}</div>
      </div>
    `;
  });
}

export function renderPresets(context: CardContext): TemplateResult | typeof nothing {
  if (context.subject.kind !== "preset_mode") return nothing;
  if (!context.config.presets.visible) return nothing;

  const { presets } = context.subject;
  if (!presets.length) {
    return html`<div class="section note">
      ${localizeCount(context.hass, "presets_one", "presets_other", 0)}
    </div>`;
  }

  const withValues = context.config.presets.values;
  return html`
    <div class="section rows">
      ${presets.map((preset) => {
        const target = preset.entities.active_mode;
        const name = html`
          <button
            class="row-label link-row"
            type="button"
            ?disabled=${!target}
            @click=${() => target && showMoreInfo(context.host, target)}
          >
            <span>${preset.name}</span>
          </button>
        `;
        if (!withValues) {
          const entity = stateOf(context.hass, target);
          return html`
            <div class="row">
              ${name}
              <div class="row-value ${entity && !isUnavailable(entity.state) ? "" : "muted"}">
                ${entity && !isUnavailable(entity.state)
                  ? entity.state
                  : localize(context.hass, "no_mode")}
              </div>
            </div>
          `;
        }
        return html`
          <div class="group-label">${preset.name}</div>
          ${valueRows(context, preset)}
        `;
      })}
    </div>
  `;
}
