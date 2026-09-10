/**
 * The value list of a preset - what is valid now, or the values of one mode.
 *
 * Without `editor.enabled` it is one row per parameter carrying the value of
 * whichever mode is active. That is the whole point of the integration, and it
 * is what a dashboard wants to see.
 *
 * With the editors on, a row of chips above the list says which mode it shows.
 * The first chip is **Active**, and it is where the card rests: the values as
 * they are, read-only, exactly as a card without editors would show them. Any
 * other chip shows that mode's values as editors. Picking a mode is therefore
 * the deliberate act that a separate "edit" switch used to be, and it is one
 * gesture instead of two.
 *
 * **Nothing is written until *Apply*.** Changes are collected in the card's
 * draft, which is keyed by entity, so one round can touch several modes: pick
 * Night, change a value, pick Away, change another, apply once. The button
 * appears exactly while something is waiting, so it cannot be missed and does
 * not sit there empty. Reading is therefore always safe - there is no gesture
 * in this list that changes the house by itself.
 */

import { html, nothing, type TemplateResult } from "lit";

import { activeModeKey, modesOf } from "../data/state";
import { orderedParameters } from "../data/subject";
import { localize } from "../localize";
import { icon } from "./icon";
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

/** Sends what the editors collected, and returns to the resolved values. */
function applyButton(context: CardContext): TemplateResult {
  return html`
    <div class="toolbar">
      <span class="toolbar-label"></span>
      <button class="apply" type="button" @click=${() => context.apply()}>
        ${localize(context.hass, "apply")}
      </button>
    </div>
  `;
}

/**
 * The chips choosing which mode the list shows.
 *
 * "Active" first, and it is not a mode: it is the resolved view, the one the
 * card shows when nobody has asked for anything else. The rest are the modes,
 * and picking one opens its values for editing.
 */
function modePicker(context: CardContext): TemplateResult | typeof nothing {
  const modes = modesOf(context.subject);
  if (!modes.length) return nothing;
  const label = localize(context.hass, "mode");
  const picked = context.editMode;

  if (context.config.editor.style === "dropdown") {
    return html`
      <div class="row">
        <div class="row-label"><span>${label}:</span></div>
        <div class="row-control">
          <select
            class="select-input"
            aria-label=${label}
            @change=${(event: Event) => {
              const value = (event.target as HTMLSelectElement).value;
              context.selectEditMode(value === "" ? null : value);
            }}
          >
            <option value="" ?selected=${picked === null}>
              ${localize(context.hass, "active")}
            </option>
            ${modes.map(
              (mode) => html`
                <option value=${mode.key} ?selected=${mode.key === picked}>
                  ${mode.name}
                </option>
              `,
            )}
          </select>
        </div>
      </div>
    `;
  }

  return html`
    <div class="row">
      <div class="row-label"><span>${label}:</span></div>
      <div class="row-control">
        <div class="chips secondary" role="group" aria-label=${label}>
          <button
            class="chip"
            type="button"
            aria-pressed=${picked === null ? "true" : "false"}
            @click=${() => context.selectEditMode(null)}
          >
            <span>${localize(context.hass, "active")}</span>
          </button>
          ${modes.map(
            (mode) => html`
              <button
                class="chip"
                type="button"
                aria-pressed=${mode.key === picked ? "true" : "false"}
                @click=${() => context.selectEditMode(mode.key)}
              >
                <span>${mode.name}</span>
              </button>
            `,
          )}
        </div>
      </div>
    </div>
  `;
}

export function renderValues(context: CardContext): TemplateResult | typeof nothing {
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
  // The button is here whenever something is waiting, whichever mode is on
  // screen - a draft left behind by switching chips must not be invisible.
  const apply = context.draft.size ? applyButton(context) : nothing;

  if (!editor.enabled) {
    return html`
      <div class="section rows">
        ${note}${list.map((row) => readOnlyRow(context, row, reserved))}
      </div>
    `;
  }

  if (editor.mode === "all") {
    const modes = modesOf(context.subject);
    return html`
      <div class="section rows">
        ${note}
        ${list.map(
          (row) => html`
            <div class="group-label">${row.label}</div>
            ${modes.map((mode) =>
              editorRow(context, row, mode.key, mode.name, reserved),
            )}
          `,
        )}
        ${apply}
      </div>
    `;
  }

  if (editor.mode === "active") {
    const modeKey = activeModeKey(context.hass, context.subject);
    return html`
      <div class="section rows">
        ${note}
        ${list.map((row) => editorRow(context, row, modeKey, row.label, reserved))}
        ${apply}
      </div>
    `;
  }

  // The picker, resting on "Active": the same rows a card without editors
  // shows, until a mode is asked for.
  const picked = context.editMode;
  return html`
    <div class="section rows">
      ${note}${modePicker(context)}
      ${picked === null
        ? list.map((row) => readOnlyRow(context, row, reserved))
        : list.map((row) => editorRow(context, row, picked, row.label, reserved))}
      ${apply}
    </div>
  `;
}
