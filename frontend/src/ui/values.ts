/**
 * The value list of a preset - read-only, or editable per mode.
 *
 * Read-only is the default and shows the main sensors: one row per parameter
 * carrying the value of whichever mode is active. That is the whole point of
 * the integration, and it is what a dashboard wants to see.
 *
 * With `editor.enabled` the same rows become the per-mode editors, and the
 * read-only column goes away with them: the editor of the active mode holds
 * exactly the value the sensor resolves, so showing both would be the same
 * number twice with nothing to tell the two apart.
 *
 * With `editor.confirm` on top of that, the card starts on the values and the
 * editors sit behind a switch. What is changed there is held, not written, and
 * an *Apply* button sends the lot and closes the view again. Two things follow
 * from that shape and are worth stating: the mode picker still works while the
 * editors are open, so one round of editing can touch several modes, and
 * turning the switch back off throws the draft away because none of it was
 * ever written.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeModeKey, modesOf } from "../data/state";
import { orderedParameters } from "../data/subject";
import { localize } from "../localize";
import { icon } from "./icon";
import { applyButton, editSwitch } from "./confirm";
import { isWideControl, renderControl } from "./controls";
import type { CardContext } from "./context";
import type { ParameterInfo, PresetInfo } from "../types/data";
import type { ResolvedParameterRow } from "../types/config";
import { formatState, hasNoValue, stateOf, UNKNOWN } from "../util/ha";

interface Row {
  parameter: ParameterInfo;
  label: string;
  icon: string | false | undefined;
}

function rows(context: CardContext, preset: PresetInfo): Row[] {
  const wanted = context.config.values.parameters;
  const overrides = new Map<string, ResolvedParameterRow>(
    (wanted ?? []).map((row) => [row.parameter, row]),
  );
  return orderedParameters(
    preset,
    wanted ? wanted.map((row) => row.parameter) : null,
  ).map((parameter) => {
    const override = overrides.get(parameter.key);
    return {
      parameter,
      label: override?.name ?? parameter.name,
      icon: override?.icon,
    };
  });
}

/**
 * The icon of one row, in a slot of its own.
 *
 * The slot is kept even where there is no icon: a parameter without one would
 * otherwise pull its label left by an icon's width, and a list where one row
 * out of three starts somewhere else reads as a mistake. Rows only get the
 * slot at all once something in the list has an icon to show.
 */
function rowIcon(
  context: CardContext,
  row: Row,
  reserved: boolean,
): TemplateResult | typeof nothing {
  if (!reserved) return nothing;
  const name =
    row.icon === false
      ? undefined
      : (row.icon ??
        (context.config.values.icons
          ? stateOf(context.hass, row.parameter.entity)?.attributes.icon
          : undefined));
  return html`<span class="row-icon">${icon(name)}</span>`;
}

/** Whether this list shows an icon column at all. */
function iconColumn(context: CardContext, list: Row[]): boolean {
  return (
    context.config.values.icons || list.some((row) => typeof row.icon === "string")
  );
}

/** What one value reads as: its formatted state, or why there is none. */
function valueText(context: CardContext, parameter: ParameterInfo): {
  text: string;
  muted: boolean;
} {
  const entity = stateOf(context.hass, parameter.entity);
  if (!entity) {
    return { text: localize(context.hass, "unavailable"), muted: true };
  }
  if (entity.state === UNKNOWN) {
    // `unknown` on a value sensor means one thing here: the mode has no value
    // for this parameter and the parameter has no default.
    return { text: localize(context.hass, "not_set"), muted: true };
  }
  if (hasNoValue(entity.state)) {
    return { text: localize(context.hass, "unavailable"), muted: true };
  }
  return { text: formatState(context.hass, entity), muted: false };
}

function readOnlyRow(
  context: CardContext,
  row: Row,
  reserved: boolean,
): TemplateResult {
  const { text, muted } = valueText(context, row.parameter);
  return html`
    <div class="row">
      <div class="row-label">
        ${rowIcon(context, row, reserved)}<span>${row.label}</span>
      </div>
      <div class="row-value ${muted ? "muted" : ""}">${text}</div>
    </div>
  `;
}

function editorRow(
  context: CardContext,
  row: Row,
  modeKey: string | null,
  label: string,
  reserved: boolean,
): TemplateResult {
  const entityId = modeKey ? row.parameter.editors[modeKey] : undefined;
  const entity = stateOf(context.hass, entityId);
  const wide = isWideControl(row.parameter.type, entity);
  return html`
    <div class="row ${wide ? "wide" : ""}">
      <div class="row-label">
        ${rowIcon(context, row, reserved)}<span>${label}</span>
      </div>
      <div class="row-control">
        ${renderControl(context, row.parameter.type, entity, label)}
      </div>
    </div>
  `;
}

/** The chips choosing which mode the editors write to. */
function editModePicker(context: CardContext): TemplateResult | typeof nothing {
  const modes = modesOf(context.subject);
  if (modes.length < 2) return nothing;
  const active = activeModeKey(context.hass, context.subject);
  const activeMode = modes.find((mode) => mode.key === active);

  // Under the edit switch the word "edit" has already been said, and saying it
  // twice reads like two settings for one thing. There the line only has to
  // name what it picks - which mode the editors write to.
  const label = localize(context.hass, context.config.editor.confirm ? "mode" : "editing");
  const control =
    context.config.editor.style === "dropdown"
      ? html`
          <select
            class="select-input"
            aria-label=${label}
            @change=${(event: Event) =>
              context.selectEditMode((event.target as HTMLSelectElement).value)}
          >
            ${modes.map(
              (mode) => html`
                <option value=${mode.key} ?selected=${mode.key === context.editMode}>
                  ${mode.name}
                </option>
              `,
            )}
          </select>
        `
      : html`
          <div class="chips secondary" role="group" aria-label=${label}>
            ${modes.map(
              (mode) => html`
                <button
                  class="chip"
                  type="button"
                  aria-pressed=${mode.key === context.editMode ? "true" : "false"}
                  @click=${() => context.selectEditMode(mode.key)}
                >
                  <span>${mode.name}</span>
                </button>
              `,
            )}
          </div>
        `;

  return html`
    <div class="row">
      <div class="row-label"><span>${label}:</span></div>
      <div class="row-control">${control}</div>
    </div>
    ${activeMode && activeMode.key !== context.editMode
      ? html`<div class="note">
          ${localize(context.hass, "active_is", { mode: activeMode.name })}
        </div>`
      : nothing}
  `;
}

export function renderValues(context: CardContext): TemplateResult | typeof nothing {
  if (context.subject.kind !== "preset") return nothing;
  if (!context.config.values.visible) return nothing;

  const preset = context.subject.preset;
  const list = rows(context, preset);
  if (!list.length) {
    return html`<div class="section note">
      ${localize(context.hass, "no_parameters")}
    </div>`;
  }

  // Every row of an orphaned preset reads "Not set", and each of them is
  // literally true and none of them says why. One line does.
  const note =
    context.subject.presetMode === null
      ? html`<div class="note warning">${localize(context.hass, "orphaned")}</div>`
      : nothing;

  const reserved = iconColumn(context, list);
  const { editor } = context.config;
  const values = () => html`
    <div class="section rows">
      ${note}${editor.confirm ? editSwitch(context) : nothing}
      ${list.map((row) => readOnlyRow(context, row, reserved))}
    </div>
  `;

  if (!editor.enabled) return values();
  // Confirmed editing starts closed: the card is a card until asked otherwise.
  if (editor.confirm && !context.editing) return values();

  if (editor.mode === "all") {
    const modes = modesOf(context.subject);
    return html`
      <div class="section rows">
        ${note}${editor.confirm ? editSwitch(context) : nothing}
        ${list.map(
          (row) => html`
            <div class="group-label">${row.label}</div>
            ${modes.map((mode) =>
              editorRow(context, row, mode.key, mode.name, reserved),
            )}
          `,
        )}
        ${editor.confirm ? applyButton(context) : nothing}
      </div>
    `;
  }

  const modeKey =
    editor.mode === "active" ? activeModeKey(context.hass, context.subject) : context.editMode;

  return html`
    <div class="section rows">
      ${note}${editor.confirm ? editSwitch(context) : nothing}
      ${editor.mode === "picker" ? editModePicker(context) : nothing}
      ${list.map((row) => editorRow(context, row, modeKey, row.label, reserved))}
      ${editor.confirm ? applyButton(context) : nothing}
    </div>
  `;
}
