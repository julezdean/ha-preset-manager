/**
 * The card element.
 *
 * Two things here are worth knowing before changing anything.
 *
 * **`hass` is not a Lit property.** Home Assistant hands every card a new
 * `hass` object on every state change anywhere in the instance - hundreds a
 * minute in a normal house. A `@property` would re-render this card for each
 * of them. Instead the setter compares the states of the entities this card
 * actually draws and asks for a render only when one of them changed.
 *
 * **The structure arrives asynchronously.** Which entity belongs to which
 * preset comes from the websocket command, so the first frame has no subject
 * yet. That frame draws a skeleton rather than an error: a card that flashed
 * "not found" on every page load would be wrong more often than right.
 */

import { LitElement, html, nothing, type PropertyValues, type TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import { CARD_TYPE } from "./const";
import { resolveConfig } from "./config";
import { cachedPresetManagerConfig, loadPresetManagerConfig, subscribePresetManagerConfig } from "./data/store";
import { activeModeKey, modesOf } from "./data/state";
import { resolveSubject, watchedEntityIds, type Subject } from "./data/subject";
import { localize } from "./localize";
import { cardStyles } from "./styles";
import type { ResolvedConfig } from "./types/config";
import type { ActionConfig, HomeAssistant, LovelaceCardEditor } from "./types/ha";
import type { PresetManagerConfig } from "./types/data";
import { hasAction, isDefined, performAction } from "./util/ha";
import { renderHeader } from "./ui/header";
import { renderModes } from "./ui/modes";
import { renderValues } from "./ui/values";
import { renderPresets } from "./ui/presets";
import { renderFooter } from "./ui/footer";
import type { CardContext } from "./ui/context";

/** How long a press has to last to count as a hold. */
const HOLD_MS = 500;
/** How long a second tap may take to count as a double tap. */
const DOUBLE_TAP_MS = 250;
/** How long a failed service call stays on the card. */
const ERROR_MS = 6000;

/** Tapping the card opens the entity, the way every core card behaves. */
const DEFAULT_TAP_ACTION: ActionConfig = { action: "more-info" };

@customElement(CARD_TYPE)
export class PresetManagerCard extends LitElement {
  static override styles = cardStyles;

  @state() private _config?: ResolvedConfig;
  @state() private _structure?: PresetManagerConfig;
  @state() private _editModeOverride: string | null = null;
  @state() private _error?: string;

  private _hass?: HomeAssistant;
  private _watched: string[] = [];
  private _unsubscribe?: () => void;
  private _holdTimer?: ReturnType<typeof setTimeout>;
  private _errorTimer?: ReturnType<typeof setTimeout>;
  private _held = false;
  private _lastTap = 0;
  private _tapTimer?: ReturnType<typeof setTimeout>;

  // Configuration ----------------------------------------------------------

  public setConfig(config: unknown): void {
    // Anything thrown here is what the user sees in place of the card, so
    // `resolveConfig` speaks in sentences rather than in stack traces.
    this._config = resolveConfig(config);
    this._editModeOverride = null;
    this._watched = [];
  }

  public static getConfigElement(): LovelaceCardEditor {
    return document.createElement(`${CARD_TYPE}-editor`) as LovelaceCardEditor;
  }

  /**
   * The configuration the card picker starts a new card with.
   *
   * Asynchronous on purpose: the picker awaits it, and a card that opened on
   * an empty entity would greet the user with its own error message.
   */
  public static async getStubConfig(
    hass: HomeAssistant,
  ): Promise<Record<string, unknown>> {
    const structure =
      cachedPresetManagerConfig(hass) ?? (await loadPresetManagerConfig(hass));
    // A preset mode first: it is the object a dashboard starts from, and its
    // card needs nothing else to be useful.
    const entity =
      structure.preset_modes.find((item) => item.entities.mode)?.entities.mode ??
      structure.presets.find((item) => item.entities.active_mode)?.entities.active_mode;
    return { type: `custom:${CARD_TYPE}`, entity: entity ?? "" };
  }

  // Home Assistant ---------------------------------------------------------

  public set hass(hass: HomeAssistant) {
    const previous = this._hass;
    this._hass = hass;
    if (!previous) {
      this.requestUpdate();
      void this._load();
      return;
    }
    if (previous.language !== hass.language || previous.themes !== hass.themes) {
      this.requestUpdate();
      return;
    }
    // The identity of a state object changes when, and only when, that entity
    // changed. Comparing the handful we draw is what keeps this card off the
    // critical path of every other entity in the house.
    for (const entityId of this._watched) {
      if (previous.states[entityId] !== hass.states[entityId]) {
        this.requestUpdate();
        return;
      }
    }
  }

  public get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  public override connectedCallback(): void {
    super.connectedCallback();
    void this._load();
  }

  public override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.();
    this._unsubscribe = undefined;
    this._clearTimers();
  }

  private async _load(): Promise<void> {
    if (!this._hass || this._unsubscribe) return;
    this._unsubscribe = subscribePresetManagerConfig(this._hass, (structure) => {
      this._structure = structure;
    });
    this._structure = await loadPresetManagerConfig(this._hass);
  }

  // Sizing -----------------------------------------------------------------

  public getCardSize(): number {
    const config = this._config;
    if (!config) return 2;
    let size = config.header.visible ? 1 : 0;
    // The default depends on what the entity turned out to be, which is known
    // here only after the structure arrived. Before that it counts as shown,
    // so a card is never given less room than it needs.
    const subject = this._subject;
    const modes =
      config.modes.visible === undefined
        ? subject === null || subject.kind === "preset_mode"
        : config.modes.visible !== "never";
    if (modes) size += 1;
    if (config.values.visible) size += 2;
    if (config.presets.visible) size += 2;
    if (config.footer.visible) size += 1;
    return Math.max(1, size);
  }

  /** Sections view: full width by default, never narrower than half a row. */
  public getGridOptions(): Record<string, unknown> {
    return { columns: 12, min_columns: 6 };
  }

  // Actions ----------------------------------------------------------------

  private get _tapAction(): ActionConfig | undefined {
    return this._config?.tap_action ?? DEFAULT_TAP_ACTION;
  }

  private _clearTimers(): void {
    if (this._holdTimer) clearTimeout(this._holdTimer);
    if (this._tapTimer) clearTimeout(this._tapTimer);
    if (this._errorTimer) clearTimeout(this._errorTimer);
    this._holdTimer = this._tapTimer = this._errorTimer = undefined;
  }

  private _headerDown(subject: Subject): void {
    this._held = false;
    if (!hasAction(this._config?.hold_action)) return;
    this._holdTimer = setTimeout(() => {
      this._held = true;
      this._run(this._config?.hold_action, subject);
    }, HOLD_MS);
  }

  private _headerUp(): void {
    if (this._holdTimer) clearTimeout(this._holdTimer);
    this._holdTimer = undefined;
  }

  private _headerClick(subject: Subject): void {
    // The hold already fired; the click that ends the press is not a tap.
    if (this._held) {
      this._held = false;
      return;
    }
    const double = this._config?.double_tap_action;
    if (!hasAction(double)) {
      this._run(this._tapAction, subject);
      return;
    }
    const now = Date.now();
    if (now - this._lastTap < DOUBLE_TAP_MS) {
      if (this._tapTimer) clearTimeout(this._tapTimer);
      this._tapTimer = undefined;
      this._lastTap = 0;
      this._run(double, subject);
      return;
    }
    this._lastTap = now;
    this._tapTimer = setTimeout(() => {
      this._tapTimer = undefined;
      this._run(this._tapAction, subject);
    }, DOUBLE_TAP_MS);
  }

  private _run(action: ActionConfig | undefined, subject: Subject): void {
    if (!this._hass) return;
    const fallback =
      subject.kind === "preset_mode"
        ? subject.presetMode.entities.mode
        : subject.preset.entities.active_mode;
    this._call(performAction(this, this._hass, action, fallback ?? this._config?.entity));
  }

  /**
   * Run a call and put a failure on the card.
   *
   * Home Assistant raises a translated `ServiceValidationError` when a write
   * is refused - switching a mode while the automatic is on, a value outside
   * its range. That sentence is the useful one, and a rejected promise nobody
   * catches would only reach the browser console.
   */
  private _call(promise: Promise<unknown>): void {
    void promise.then(
      () => {
        if (this._error !== undefined) this._error = undefined;
      },
      (error: unknown) => {
        this._error = this._messageOf(error);
        if (this._errorTimer) clearTimeout(this._errorTimer);
        this._errorTimer = setTimeout(() => {
          this._errorTimer = undefined;
          this._error = undefined;
        }, ERROR_MS);
      },
    );
  }

  private _messageOf(error: unknown): string {
    if (typeof error === "string") return error;
    if (error && typeof error === "object") {
      const record = error as Record<string, unknown>;
      const body = record.body as Record<string, unknown> | undefined;
      for (const candidate of [record.message, body?.message, record.error]) {
        if (typeof candidate === "string" && candidate) return candidate;
      }
    }
    return String(error);
  }

  // Rendering ---------------------------------------------------------------

  protected override willUpdate(changed: PropertyValues): void {
    super.willUpdate(changed);
    const subject = this._subject;
    this._watched = subject ? watchedEntityIds(subject) : [];
  }

  private get _subject(): Subject | null {
    if (!this._config || !this._structure) return null;
    return resolveSubject(this._structure, this._config.entity);
  }

  /** The mode the editors write to: the user's pick, else what is active. */
  private _editMode(subject: Subject): string | null {
    if (this._editModeOverride) return this._editModeOverride;
    const configured = this._config?.editor.default_mode;
    const modes = modesOf(subject);
    if (configured && modes.some((mode) => mode.key === configured)) return configured;
    return activeModeKey(this._hass!, subject) ?? modes[0]?.key ?? null;
  }

  protected override render(): TemplateResult | typeof nothing {
    const config = this._config;
    const hass = this._hass;
    if (!config || !hass) return nothing;

    if (!this._structure) return this._shell(this._skeleton());

    const subject = this._subject;
    if (!subject) {
      const known =
        this._structure.preset_modes.length + this._structure.presets.length;
      return this._shell(
        this._alert(
          known
            ? localize(hass, "not_found", { entity: config.entity })
            : localize(hass, "not_set_up"),
        ),
      );
    }

    const context: CardContext = {
      hass,
      config,
      subject,
      host: this,
      editMode: this._editMode(subject),
      selectEditMode: (key) => {
        this._editModeOverride = key;
      },
      call: (promise) => this._call(promise),
      tappable: hasAction(this._tapAction) || hasAction(config.hold_action),
      onHeaderDown: () => this._headerDown(subject),
      onHeaderUp: () => this._headerUp(),
      onHeaderClick: () => this._headerClick(subject),
    };

    return this._shell(html`
      ${renderHeader(context)} ${renderModes(context)} ${renderValues(context)}
      ${renderPresets(context)} ${renderFooter(context)}
      ${this._error
        ? html`<div class="section inline-error" role="alert">${this._error}</div>`
        : nothing}
    `);
  }

  /**
   * The card shell.
   *
   * Nothing is styled from the configuration: `ha-card` already answers to the
   * user's theme, and a card that took a background and a radius of its own
   * would be the one card on the dashboard that stops following it.
   */
  private _shell(content: TemplateResult): TemplateResult {
    return html`<ha-card>${content}</ha-card>`;
  }

  private _skeleton(): TemplateResult {
    return html`
      <div class="section rows" aria-busy="true" aria-label=${localize(this._hass, "loading")}>
        <div class="skeleton" style="width:45%"></div>
        <div class="skeleton" style="width:70%"></div>
      </div>
    `;
  }

  private _alert(message: string): TemplateResult {
    // `ha-alert` is part of the frontend, but a card that assumed it was
    // always defined would render nothing at all on the one release where it
    // is not - which is exactly the release where this message matters.
    return isDefined("ha-alert")
      ? html`<ha-alert alert-type="warning">${message}</ha-alert>`
      : html`<div class="fallback-alert" role="alert">${message}</div>`;
  }
}
