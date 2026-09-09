/**
 * What every part of the card gets handed.
 *
 * The card is one custom element and the sections below it are functions, not
 * elements of their own. Lit re-renders the whole template on every change and
 * patches only what differs, so a dozen nested elements would buy nothing and
 * cost a dozen more upgrade paths on a frontend release.
 */

import type { ResolvedConfig } from "../types/config";
import type { HomeAssistant } from "../types/ha";
import type { Subject } from "../data/subject";

export interface CardContext {
  hass: HomeAssistant;
  config: ResolvedConfig;
  subject: Subject;
  /** The element events are fired from. */
  host: HTMLElement;
  /** Mode key whose values the editors write to. */
  editMode: string | null;
  /** Change the mode being edited. */
  selectEditMode(modeKey: string): void;
  /** Run a service call and surface a rejection on the card itself. */
  call(promise: Promise<unknown>): void;
  /** Whether the header carries a tap/hold action worth a cursor and a role. */
  tappable: boolean;
  /** Pointer plumbing of the header action; see `card.ts`. */
  onHeaderDown(): void;
  onHeaderUp(): void;
  onHeaderClick(): void;
}
