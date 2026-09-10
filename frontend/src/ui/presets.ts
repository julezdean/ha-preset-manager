/**
 * The presets that follow a preset mode.
 *
 * Off by default: a preset mode card is about the dimension, and one that
 * listed every device following it would grow with the setup rather than with
 * the user's intent. Turned on, it answers the one question the entity list
 * cannot - "what does 'Night' actually mean here" - because it can show each
 * preset with the values that are valid right now.
 *
 * With `show: editable` those rows become the editors of the mode each preset
 * is currently on, which is the answer to the question the list provokes:
 * having seen what Night means, this is where it is changed. Not a mode picker per
 * preset - the card already has one row of chips deciding the mode, and a
 * second way to choose one would be a different question wearing the same
 * clothes. Switching the mode therefore moves these editors with it.
 */

import { html, nothing, type TemplateResult } from "lit";

import { presetModeKey } from "../data/state";
import { localize, localizeCount } from "../localize";
import { isWideControl, renderControl } from "./controls";
import { formatState, hasNoValue, showMoreInfo, stateOf, UNKNOWN } from "../util/ha";
import type { CardContext } from "./context";
import type { ParameterInfo, PresetInfo } from "../types/data";

function readOnlyValue(context: CardContext, parameter: ParameterInfo): TemplateResult {
  const entity = stateOf(context.hass, parameter.entity);
  let text: string;
  let muted = true;
  if (!entity) text = localize(context.hass, "unavailable");
  else if (entity.state === UNKNOWN) text = localize(context.hass, "not_set");
  else if (hasNoValue(entity.state)) text = localize(context.hass, "unavailable");
  else {
    text = formatState(context.hass, entity);
    muted = false;
  }
  return html`<div class="row-value ${muted ? "muted" : ""}">${text}</div>`;
}

function editorValue(
  context: CardContext,
  preset: PresetInfo,
  parameter: ParameterInfo,
): TemplateResult {
  const modeKey = presetModeKey(context.hass, preset);
  const entity = stateOf(context.hass, modeKey ? parameter.editors[modeKey] : undefined);
  return html`
    <div class="row-control">
      ${renderControl(context, parameter.type, entity, parameter.name)}
    </div>
  `;
}

function valueRows(context: CardContext, preset: PresetInfo): TemplateResult[] {
  const editable = context.config.presets.show === "editable";
  return preset.parameters.map((parameter) => {
    const wide =
      editable &&
      isWideControl(
        parameter.type,
        stateOf(
          context.hass,
          parameter.editors[presetModeKey(context.hass, preset) ?? ""],
        ),
      );
    return html`
      <div class="row ${wide ? "wide" : ""}">
        <div class="row-label"><span>${parameter.name}</span></div>
        ${editable
          ? editorValue(context, preset, parameter)
          : readOnlyValue(context, parameter)}
      </div>
    `;
  });
}

export function renderPresets(context: CardContext): TemplateResult | typeof nothing {
  if (context.subject.kind !== "preset_mode") return nothing;
  const show = context.config.presets.show;
  if (show === "none") return nothing;

  const { presets } = context.subject;
  if (!presets.length) {
    return html`<div class="section note">
      ${localizeCount(context.hass, "presets_one", "presets_other", 0)}
    </div>`;
  }

  const withValues = show !== "names";
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
              <div class="row-value ${entity && !hasNoValue(entity.state) ? "" : "muted"}">
                ${entity && !hasNoValue(entity.state)
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
