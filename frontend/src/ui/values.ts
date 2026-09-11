/**
 * The value list of a preset - what is valid now, or the values of one mode.
 *
 * With `values.mode: active` it is one row per parameter carrying the value of
 * whichever mode is active. That is the whole point of the integration, and it
 * is what a dashboard wants to see.
 *
 * With `picker`, a strip of tabs above the list says which mode it shows. The
 * first tab is **Active**, and it is where the card rests: the values as they
 * are, read-only, exactly as a card without editors would show them. Any other
 * tab shows that mode's values as editors. Picking a mode is therefore the
 * deliberate act that a separate "edit" switch used to be, and it is one
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

/**
 * What to do with what the editors collected.
 *
 * Both or neither: a button that sends changes without one that drops them
 * makes backing out mean retyping every value from memory, while the values
 * are still there to be read off the entities - discarding costs nothing but
 * the button.
 */
function draftButtons(context: CardContext): TemplateResult {
  return html`
    <div class="toolbar">
      <span class="toolbar-label"></span>
      <button class="discard" type="button" @click=${() => context.discard()}>
        ${localize(context.hass, "discard")}
      </button>
      <button class="apply" type="button" @click=${() => context.apply()}>
        ${localize(context.hass, "apply")}
      </button>
    </div>
  `;
}

/**
 * Move the focus along the strip, and take the selection with it.
 *
 * Arrow keys are what a tab strip answers to; without them a keyboard walks
 * into the strip and out the other side. Selection follows focus because
 * picking a mode here costs nothing - it changes what this card shows and
 * touches nothing in the house, so there is no reason to ask for a second
 * press to confirm it.
 */
function onStripKey(event: KeyboardEvent): void {
  const offset = { ArrowLeft: -1, ArrowRight: 1, Home: -Infinity, End: Infinity }[
    event.key
  ];
  if (offset === undefined) return;
  const strip = event.currentTarget as HTMLElement;
  const tabs = [...strip.querySelectorAll<HTMLButtonElement>("button.tab")];
  const from = tabs.indexOf(event.target as HTMLButtonElement);
  if (from < 0) return;
  event.preventDefault();
  const to = Math.min(Math.max(from + offset, 0), tabs.length - 1);
  tabs[to].focus();
  tabs[to].click();
}

/**
 * The strip choosing which mode the list shows.
 *
 * Tabs, not chips. The row above this one switches the house; this one
 * switches nothing but the panel underneath, and a second row of pills said
 * those were the same kind of act - a pill is a state, a tab is a view. It
 * therefore carries no colour and no icons, sits flush against the list it
 * governs, and scrolls sideways rather than wrapping: a strip that breaks
 * into two lines stops reading as one.
 *
 * "Active" is first and is not a mode: it is the resolved view, where the
 * card rests when nobody has asked for anything else. The rest are the modes,
 * and picking one opens its values for editing.
 */
function modePicker(context: CardContext): TemplateResult | typeof nothing {
  const modes = modesOf(context.subject);
  if (!modes.length) return nothing;
  const picked = context.editMode;

  const tab = (key: string | null, name: string): TemplateResult => {
    const selected = key === picked;
    return html`
      <button
        class="tab"
        type="button"
        role="tab"
        aria-selected=${selected ? "true" : "false"}
        tabindex=${selected ? 0 : -1}
        @click=${() => context.selectEditMode(key)}
      >
        ${name}
      </button>
    `;
  };

  return html`
    <div class="section strip">
      <div
        class="tabs"
        role="tablist"
        aria-label=${localize(context.hass, "mode")}
        @keydown=${onStripKey}
      >
        ${tab(null, localize(context.hass, "active"))}
        ${modes.map((mode) => tab(mode.key, mode.name))}
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
  // Here whenever something is waiting, whichever mode is on screen - a draft
  // left behind by switching chips must not be invisible.
  const buttons = context.draft.size ? draftButtons(context) : nothing;
  const mode = context.config.values.mode;

  if (mode === "active") {
    return html`
      <div class="section rows">
        ${note}${list.map((row) => readOnlyRow(context, row, reserved))}
      </div>
    `;
  }

  if (mode === "all") {
    const modes = modesOf(context.subject);
    return html`
      <div class="section rows">
        ${note}
        ${list.map(
          (row) => html`
            <div class="group-label">${row.label}</div>
            ${modes.map((each) =>
              editorRow(context, row, each.key, each.name, reserved),
            )}
          `,
        )}
        ${buttons}
      </div>
    `;
  }

  if (mode === "edit") {
    const modeKey = activeModeKey(context.hass, context.subject);
    return html`
      <div class="section rows">
        ${note}
        ${list.map((row) => editorRow(context, row, modeKey, row.label, reserved))}
        ${buttons}
      </div>
    `;
  }

  // The picker, resting on "Active": the same rows a read-only card shows,
  // until a mode is asked for. The strip is a section of its own so that it
  // can reach both edges of the card - a tab strip that stops short of them
  // is a row of buttons with a line under it.
  const picked = context.editMode;
  return html`
    ${modePicker(context)}
    <div class="section rows" role="tabpanel">
      ${note}
      ${picked === null
        ? list.map((row) => readOnlyRow(context, row, reserved))
        : list.map((row) => editorRow(context, row, picked, row.label, reserved))}
      ${buttons}
    </div>
  `;
}
