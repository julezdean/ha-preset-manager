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
import type { StagedWrite } from "./controls";

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
  /**
   * Confirmed editing, when `editor.confirm` is on: whether the editors are
   * open, what has been changed but not written, and the three things the user
   * can do about it.
   */
  editing: boolean;
  draft: ReadonlyMap<string, StagedWrite>;
  setEditing(open: boolean): void;
  /**
   * Present only where something applies the draft afterwards.
   *
   * A control stages instead of writing as soon as it is handed this, so
   * handing it over unconditionally made every edit outside confirmed editing
   * vanish into a draft nobody flushed - the plain editors wrote nothing at
   * all, silently, from the first release of the card.
   */
  stage?(entityId: string, write: StagedWrite): void;
  apply(): void;
  /** Whether the header carries a tap/hold action worth a cursor and a role. */
  tappable: boolean;
  /** Pointer plumbing of the header action; see `card.ts`. */
  onHeaderDown(): void;
  onHeaderUp(): void;
  onHeaderClick(): void;
}
