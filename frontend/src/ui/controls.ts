/**
 * The editing controls, one per parameter type.
 *
 * They are built from plain form elements rather than from Home Assistant's
 * own components. Two reasons: the frontend's inputs are internal elements
 * whose names have changed more than once, and a real `<input>` brings the
 * keyboard behaviour, the focus ring and the screen reader announcement that
 * a div with a click handler has to reimplement and usually does not.
 *
 * Everything a control needs - range, step, options, pattern, password mode -
 * is read from the *state* of the editor entity, which is where Home Assistant
 * publishes it. The websocket command therefore does not repeat any of it, and
 * a parameter whose range changed is right on the next state without the card
 * asking anybody.
 *
 * Writes go out on `change`, not on `input`: a slider dragged across its range
 * would otherwise be one service call and one store write per pixel.
 *
 * **`unknown` is not `unavailable`.** An editor entity reports `unknown` while
 * the mode has no value for its parameter - which is the state of every
 * parameter of every mode of a preset nobody has filled in yet. Those controls
 * are empty and fully usable; only an entity that is really not there (gone,
 * or disabled in the registry) is disabled here.
 */

import { html, nothing, type TemplateResult } from "lit";

import { localize } from "../localize";
import type { HassEntity, HomeAssistant } from "../types/ha";
import type { ParameterType } from "../types/data";
import { hasNoValue, isMissing } from "../util/ha";

export interface ControlContext {
  hass: HomeAssistant;
  call(promise: Promise<unknown>): void;
}

function set(
  context: ControlContext,
  entity: HassEntity,
  service: string,
  data: Record<string, unknown>,
): void {
  const domain = entity.entity_id.split(".", 1)[0];
  context.call(
    context.hass.callService(domain, service, data, { entity_id: entity.entity_id }),
  );
}

/** Shown where a control cannot be empty but has no value either. */
const UNSET = "—";

interface ControlState {
  /** The entity is not there; nothing can be written to it. */
  disabled: boolean;
  /** There is no value yet, so the control starts empty. */
  empty: boolean;
}

function controlState(entity: HassEntity): ControlState {
  return { disabled: isMissing(entity.state), empty: hasNoValue(entity.state) };
}

function attr<T>(entity: HassEntity, name: string, fallback: T): T {
  const value = entity.attributes[name];
  return value === undefined || value === null ? fallback : (value as T);
}

function numberControl(
  context: ControlContext,
  entity: HassEntity,
  label: string,
): TemplateResult {
  const { disabled, empty } = controlState(entity);
  const min = attr<number>(entity, "min", 0);
  const max = attr<number>(entity, "max", 100);
  const step = attr<number>(entity, "step", 1);
  const unit = entity.attributes.unit_of_measurement ?? "";
  const value = empty ? "" : entity.state;
  // `valueAsNumber`, not `value`: a number input renders and accepts the
  // decimal separator of the browser's locale, so a German user typing "19,5"
  // leaves `value` empty while this reads 19.5. It is also the only reading
  // that says "not a number" rather than quietly producing NaN.
  const commit = (event: Event) => {
    const number = (event.target as HTMLInputElement).valueAsNumber;
    if (Number.isNaN(number)) return;
    set(context, entity, "set_value", { value: number });
  };

  if (attr<string>(entity, "mode", "box") === "slider") {
    return html`
      <input
        class="slider"
        type="range"
        aria-label=${label}
        min=${min}
        max=${max}
        step=${step}
        .value=${empty ? String(min) : value}
        ?disabled=${disabled}
        @change=${commit}
      />
      <span class="slider-value">
        ${empty ? UNSET : `${entity.state}${unit ? ` ${unit}` : ""}`}
      </span>
    `;
  }

  // Up and down step the value and write it straight away. A number input
  // does the stepping itself, but whether that also counts as a change - and
  // therefore reaches the store - is up to the browser. Doing it here makes
  // the arrow keys the quickest way to set a value on every one of them, and
  // keeps the step and the range the entity's own.
  const arrows = (event: KeyboardEvent) => {
    const direction = event.key === "ArrowUp" ? 1 : event.key === "ArrowDown" ? -1 : 0;
    if (!direction || disabled) return;
    event.preventDefault();
    const input = event.target as HTMLInputElement;
    const current = Number.isNaN(input.valueAsNumber) ? min : input.valueAsNumber;
    const next = Math.min(max, Math.max(min, current + direction * step));
    if (next === current) return;
    // Rounded to the step, or 0.1 + 0.2 arrives in the store as it famously is.
    const decimals = (String(step).split(".")[1] ?? "").length;
    input.value = next.toFixed(decimals);
    set(context, entity, "set_value", { value: Number(input.value) });
  };

  return html`
    <input
      class="number-input"
      type="number"
      inputmode="decimal"
      aria-label=${label}
      min=${min}
      max=${max}
      step=${step}
      .value=${value}
      ?disabled=${disabled}
      @change=${commit}
      @keydown=${arrows}
    />
    ${unit ? html`<span class="row-value">${unit}</span>` : nothing}
  `;
}

function booleanControl(
  context: ControlContext,
  entity: HassEntity,
  label: string,
): TemplateResult {
  const { disabled, empty } = controlState(entity);
  return html`
    <label class="switch">
      <input
        type="checkbox"
        role="switch"
        aria-label=${label}
        .checked=${entity.state === "on"}
        .indeterminate=${empty}
        ?disabled=${disabled}
        @change=${(event: Event) =>
          set(
            context,
            entity,
            (event.target as HTMLInputElement).checked ? "turn_on" : "turn_off",
            {},
          )}
      />
    </label>
  `;
}

function selectControl(
  context: ControlContext,
  entity: HassEntity,
  label: string,
): TemplateResult {
  const { disabled, empty } = controlState(entity);
  const options = attr<string[]>(entity, "options", []);
  return html`
    <select
      class="select-input"
      aria-label=${label}
      ?disabled=${disabled}
      @change=${(event: Event) =>
        set(context, entity, "select_option", {
          option: (event.target as HTMLSelectElement).value,
        })}
    >
      ${empty
        ? html`<option value="" selected disabled>${UNSET}</option>`
        : nothing}
      ${options.map(
        (option) => html`
          <option value=${option} ?selected=${option === entity.state}>
            ${option}
          </option>
        `,
      )}
    </select>
  `;
}

function textControl(
  context: ControlContext,
  entity: HassEntity,
  label: string,
): TemplateResult {
  const { disabled, empty } = controlState(entity);
  const pattern = entity.attributes.pattern as string | undefined;
  return html`
    <input
      class="text-input"
      type=${attr<string>(entity, "mode", "text") === "password" ? "password" : "text"}
      aria-label=${label}
      minlength=${attr<number>(entity, "min", 0)}
      maxlength=${attr<number>(entity, "max", 255)}
      pattern=${pattern ?? nothing}
      .value=${empty ? "" : entity.state}
      ?disabled=${disabled}
      @change=${(event: Event) =>
        set(context, entity, "set_value", {
          value: (event.target as HTMLInputElement).value,
        })}
    />
  `;
}

/** `2026-09-09T21:30:00+02:00` -> `2026-09-09T21:30`, in the browser's zone. */
function localDateTimeValue(state: string): string {
  const parsed = new Date(state);
  if (Number.isNaN(parsed.getTime())) return "";
  const pad = (value: number) => String(value).padStart(2, "0");
  return (
    `${parsed.getFullYear()}-${pad(parsed.getMonth() + 1)}-${pad(parsed.getDate())}` +
    `T${pad(parsed.getHours())}:${pad(parsed.getMinutes())}`
  );
}

function temporalControl(
  context: ControlContext,
  entity: HassEntity,
  label: string,
  type: "date" | "time" | "datetime",
): TemplateResult {
  const { disabled, empty } = controlState(entity);
  let value = empty ? "" : entity.state;
  if (type === "datetime") value = empty ? "" : localDateTimeValue(entity.state);
  // A time entity reports seconds; the input wants minutes unless it is told
  // otherwise, and a preset's time is a wall clock time, not a stopwatch.
  if (type === "time") value = value.slice(0, 5);

  return html`
    <input
      class="date-input"
      type=${type === "datetime" ? "datetime-local" : type}
      aria-label=${label}
      .value=${value}
      ?disabled=${disabled}
      @change=${(event: Event) => {
        const raw = (event.target as HTMLInputElement).value;
        if (!raw) return;
        if (type === "date") set(context, entity, "set_value", { date: raw });
        else if (type === "time") {
          set(context, entity, "set_value", { time: `${raw}:00` });
        } else {
          // `datetime-local` has no zone; the entity takes it as local time,
          // which is the zone the user just typed in.
          set(context, entity, "set_value", {
            datetime: raw.replace("T", " ") + ":00",
          });
        }
      }}
    />
  `;
}

/** The control editing one parameter, or a note saying why there is none. */
export function renderControl(
  context: ControlContext,
  type: ParameterType,
  entity: HassEntity | undefined,
  label: string,
): TemplateResult {
  if (!entity) {
    return html`<span class="row-value muted">
      ${localize(context.hass, "unavailable")}
    </span>`;
  }
  switch (type) {
    case "number":
      return numberControl(context, entity, label);
    case "boolean":
      return booleanControl(context, entity, label);
    case "select":
      return selectControl(context, entity, label);
    case "text":
      return textControl(context, entity, label);
    case "date":
      return temporalControl(context, entity, label, "date");
    case "time":
      return temporalControl(context, entity, label, "time");
    case "datetime":
      return temporalControl(context, entity, label, "datetime");
    default:
      return html`<span class="row-value muted">
        ${localize(context.hass, "not_editable")}
      </span>`;
  }
}

/** Whether a type's control wants a whole row to itself on a narrow card. */
export function isWideControl(type: ParameterType, entity: HassEntity | undefined): boolean {
  return (
    type === "number" &&
    entity !== undefined &&
    attr<string>(entity, "mode", "box") === "slider"
  );
}
