/**
 * Editing as a deliberate act: the switch that opens it and the button that
 * ends it.
 *
 * Both live here rather than beside one of their users, because the two places
 * that edit values want the same pair. On a preset card it is optional, behind
 * `editor.confirm`; on the presets of a preset mode card it is the only shape
 * there is, because one row of editors there reaches into every device of the
 * dimension at once, and that is not a thing to do by dragging a slider past
 * the wrong number.
 *
 * What is changed in between is held in the card's draft and reaches Home
 * Assistant only when *Apply* is pressed. Turning the switch back off throws
 * the draft away - nothing was written, so there is nothing to undo.
 */

import { html, type TemplateResult } from "lit";

import { localize } from "../localize";
import type { CardContext } from "./context";

/** The switch that opens and closes the editors. */
export function editSwitch(context: CardContext): TemplateResult {
  const label = localize(context.hass, "editing");
  return html`
    <label class="toolbar">
      <span class="toolbar-label">${label}</span>
      <span class="switch">
        <input
          type="checkbox"
          role="switch"
          aria-label=${label}
          .checked=${context.editing}
          @change=${(event: Event) =>
            context.setEditing((event.target as HTMLInputElement).checked)}
        />
      </span>
    </label>
  `;
}

/** Sends what the editors collected, and closes them again. */
export function applyButton(context: CardContext): TemplateResult {
  return html`
    <div class="toolbar">
      <span class="toolbar-label"></span>
      <button
        class="apply"
        type="button"
        ?disabled=${context.draft.size === 0}
        @click=${() => context.apply()}
      >
        ${localize(context.hass, "apply")}
      </button>
    </div>
  `;
}
