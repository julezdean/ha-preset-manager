/**
 * Who decides the mode, and which mode it is.
 *
 * Two rows, two decisions, and both belong to the object the card is about -
 * never to another one. A preset mode card switches its own automatic between
 * the conditions and the hand; a preset card switches its own between the
 * preset mode and the hand. The chips underneath set whichever of the two the
 * switch has released. Nothing here ever reaches into the dimension from a
 * preset: a click on a card named after one preset must not change what every
 * other preset of that dimension does.
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

import {
  activeModeKey,
  automaticEntityId,
  automaticState,
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
    // Exactly while a click would do something: the automatic is off, or
    // there never was one. An external preset mode is never settable and
    // never shows.
    return modeLockReason(context.hass, context.subject) === null;
  }
  // Where the user said nothing, the row is shown: it sets the mode of the
  // object the card is about, which is what the card is for.
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

/** The switch handing the mode over to the conditions, or to the preset mode. */
function automaticRow(context: CardContext): TemplateResult | typeof nothing {
  const { hass, subject, config } = context;
  if (!config.modes.automatic) return nothing;
  const entityId = automaticEntityId(subject);
  if (!entityId) return nothing;
  const on = automaticState(hass, subject);
  const label = localize(hass, "automatic");

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

/** The mode row proper: the chips or the dropdown, or why there are neither. */
function modeControl(context: CardContext): TemplateResult {
  const modes = modesOf(context.subject);
  if (!modes.length) {
    return html`<div class="note">${localize(context.hass, "no_modes")}</div>`;
  }

  const active = activeModeKey(context.hass, context.subject);
  const locked = modeLockReason(context.hass, context.subject) !== null;

  // No line explaining why a locked row is locked. Every version of that
  // sentence said again what the switch above and the header say - who is
  // deciding, that it follows an entity, that there is no preset mode - and
  // repeated it on every card and every render. The chips being visibly
  // disabled is the part that was not already written down.
  return context.config.modes.style === "dropdown"
    ? dropdown(context, modes, active, locked)
    : chips(context, modes, active, locked);
}

export function renderModes(context: CardContext): TemplateResult | typeof nothing {
  const automatic = automaticRow(context);
  const control = modesVisible(context) ? modeControl(context) : nothing;
  if (automatic === nothing && control === nothing) return nothing;

  return html`<div class="section rows">${automatic}${control}</div>`;
}
