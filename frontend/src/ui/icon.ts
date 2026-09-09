/**
 * Icons, with a way out when the frontend has not defined `ha-icon`.
 *
 * Every icon on this card is decorative - the text beside it always says the
 * same thing - so the fallback is to draw nothing rather than a broken box,
 * and every icon is hidden from screen readers.
 */

import { html, nothing, type TemplateResult } from "lit";

import { isDefined } from "../util/ha";

export function icon(name: string | null | undefined): TemplateResult | typeof nothing {
  if (!name || !isDefined("ha-icon")) return nothing;
  return html`<ha-icon .icon=${name} aria-hidden="true"></ha-icon>`;
}

/** A default icon per kind of object, used when nothing else says otherwise. */
export const DEFAULT_PRESET_MODE_ICON = "mdi:state-machine";
export const DEFAULT_PRESET_ICON = "mdi:tune-variant";
