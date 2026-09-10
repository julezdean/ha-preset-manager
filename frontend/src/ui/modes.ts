/**
 * Which mode this preset is on, and setting it.
 *
 * The chips are live while the preset is not following its preset mode - the
 * switch for that sits in the header, beside the name it belongs to - and
 * disabled while it is. Nothing here ever reaches into the dimension: a click
 * on a card named after one preset must not change what every other preset of
 * that dimension does, and it structurally cannot, because a preset mode has
 * nothing to write to.
 *
 * Setting goes through `preset_manager.set_active_mode` with the mode *key*,
 * not through `select.select_option` with its display name - the key is what
 * survives a rename, and the service exists for exactly that reason.
 */

import { html, nothing, type TemplateResult } from "lit";

import {
  activeModeKey,
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

/** The mode row proper: the chips or the dropdown, or why there are neither. */
function modeControl(context: CardContext): TemplateResult {
  const modes = modesOf(context.subject);
  if (!modes.length) {
    return html`<div class="note">${localize(context.hass, "no_modes")}</div>`;
  }

  const active = activeModeKey(context.hass, context.subject);
  // No line explaining why a locked row is locked. Every version of that
  // sentence said again what the switch above and the header say, and repeated
  // it on every card and every render. The chips being visibly disabled is the
  // part that was not already written down.
  return chips(
    context,
    modes,
    active,
    modeLockReason(context.hass, context.subject) !== null,
  );
}

export function renderModes(context: CardContext): TemplateResult | typeof nothing {
  if (!modesVisible(context)) return nothing;
  return html`<div class="section">${modeControl(context)}</div>`;
}
