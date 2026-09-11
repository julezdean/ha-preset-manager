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
  /**
   * Which mode the value list shows: a mode key, or `null` for "active".
   *
   * `null` is the resting state - the resolved values, read-only. A key means
   * that mode's values, as editors.
   */
  editMode: string | null;
  /** Show another mode, or `null` for the resolved values. */
  selectEditMode(modeKey: string | null): void;
  /** Run a service call and surface a rejection on the card itself. */
  call(promise: Promise<unknown>): void;
  /** What has been changed but not written yet. */
  draft: ReadonlyMap<string, StagedWrite>;
  /**
   * Present only where something applies the draft afterwards.
   *
   * Every editor stages; nothing on this card writes on its own. What made
   * that worth stating is the version where the card handed this over even
   * where no *Apply* existed - those edits vanished into a draft nobody
   * flushed, silently.
   */
  stage(entityId: string, write: StagedWrite): void;
  apply(): void;
  /** Drop the draft; the editors go back to what the entities say. */
  discard(): void;
  /** Whether the header carries a tap/hold action worth a cursor and a role. */
  tappable: boolean;
  /** Pointer plumbing of the header action; see `card.ts`. */
  onHeaderDown(): void;
  onHeaderUp(): void;
  onHeaderClick(): void;
}
