/**
 * The visual editor.
 *
 * Built on `ha-form`, which is the frontend's own form renderer: every
 * selector it draws - the entity picker, the icon picker, the action editor -
 * is the one the core cards use, so the editor looks and behaves like the rest
 * of the dashboard editor without this card drawing a single field itself.
 *
 * Two rules shape it.
 *
 * **Only the entity is on the surface.** Everything else sits in a collapsed
 * group, so a new card asks for one thing. The groups the current subject
 * cannot use - the preset list of a preset mode, the editors of a preset - are
 * not shown at all rather than shown and ignored.
 *
 * **What is left at its default is not written.** The form has to show a
 * checkbox in its real position, so it is fed the resolved configuration; what
 * comes back is compared against the defaults again and only the differences
 * are saved. Without that, opening the editor once would turn three lines of
 * YAML into forty.
 */

import { LitElement, html, nothing, type TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

import { CARD_TYPE } from "./const";
import { pruneConfig, resolveConfig } from "./config";
import { cachedPresetManagerConfig, loadPresetManagerConfig, subscribePresetManagerConfig } from "./data/store";
import { resolveSubject, type Subject } from "./data/subject";
import { localize } from "./localize";
import type { HomeAssistant } from "./types/ha";
import type { PresetManagerConfig } from "./types/data";
import { fireEvent } from "./util/ha";

type Schema = Record<string, unknown>;

const LABELS: Record<string, string> = {
  entity: "Entity",
  header: "Header",
  modes: "Modes",
  values: "Values",
  editor: "Editing",
  presets: "Presets",
  footer: "Footer",
  actions: "Actions",
  visible: "Show",
  automatic: "Automatic switch",
  title: "Title",
  subtitle: "Subtitle",
  icon: "Icon",
  icon_color: "Icon colour",
  style: "Style",
  icons: "Show icons",
  parameters: "Parameters",
  parameters_note: "Parameters",
  enabled: "Editable",
  confirm: "Confirm with a button",
  editable: "Editable",
  mode: "Which mode",
  default_mode: "Start on",
  content: "Content",
  tap_action: "Tap",
  hold_action: "Hold",
  double_tap_action: "Double tap",
};

/** Shown in place of the parameter picker when YAML says more than it can. */
const YAML_ONLY = "Renamed parameters are edited in YAML.";

/** Actions that mean something for this card; `assist` deliberately not. */
const ACTIONS = ["more-info", "navigate", "url", "perform-action", "none"];

function options(values: Array<[string, string]>): Schema {
  return {
    selector: {
      select: {
        mode: "dropdown",
        options: values.map(([value, label]) => ({ value, label })),
      },
    },
  };
}

@customElement(`${CARD_TYPE}-editor`)
export class PresetManagerCardEditor extends LitElement {
  @state() private _config: Record<string, unknown> = {};
  @state() private _structure?: PresetManagerConfig;

  private _hass?: HomeAssistant;
  private _unsubscribe?: () => void;

  public set hass(hass: HomeAssistant) {
    this._hass = hass;
    this._structure ??= cachedPresetManagerConfig(hass);
    void this._load();
    this.requestUpdate();
  }

  public get hass(): HomeAssistant | undefined {
    return this._hass;
  }

  public setConfig(config: Record<string, unknown>): void {
    this._config = config;
  }

  public override disconnectedCallback(): void {
    super.disconnectedCallback();
    this._unsubscribe?.();
    this._unsubscribe = undefined;
  }

  private async _load(): Promise<void> {
    if (!this._hass || this._unsubscribe) return;
    this._unsubscribe = subscribePresetManagerConfig(this._hass, (structure) => {
      this._structure = structure;
    });
    this._structure = await loadPresetManagerConfig(this._hass);
  }

  /**
   * The entities the picker offers: one per preset and per preset mode.
   *
   * Everything of this integration would be the whole setup - a preset with
   * five parameters over four modes brings 26 entities, and 25 of them are
   * ways of saying the same card. The canonical one is the sensor carrying
   * the active mode, so the list is exactly the objects the user thinks in.
   *
   * The *card* still accepts any of them: pointing at a value sensor or at one
   * per-mode editor resolves to the same subject, and a dashboard written by
   * hand should not have to know which entity is the canonical one. Only the
   * picker is narrowed. Before the structure has arrived there is nothing to
   * narrow it with, so it falls back to the whole integration.
   */
  private _entityPicker(): Record<string, unknown> {
    const canonical = [
      ...(this._structure?.preset_modes ?? []).map((item) => item.entities.mode),
      ...(this._structure?.presets ?? []).map((item) => item.entities.active_mode),
    ].filter((entityId): entityId is string => Boolean(entityId));
    return canonical.length
      ? { include_entities: canonical }
      : { integration: "preset_manager" };
  }

  /** Whether `values.parameters` carries more than a list of keys. */
  private _hasParameterOverrides(): boolean {
    const values = this._config.values as Record<string, unknown> | undefined;
    const rows = values?.parameters;
    return Array.isArray(rows) && rows.some((row) => typeof row !== "string");
  }

  private get _subject(): Subject | null {
    const entity = this._config.entity;
    if (!this._structure || typeof entity !== "string" || !entity) return null;
    return resolveSubject(this._structure, entity);
  }

  private _schema(subject: Subject | null): Schema[] {
    const isPreset = subject?.kind === "preset";
    const isPresetMode = subject?.kind === "preset_mode";
    const modes = subject
      ? (subject.kind === "preset_mode" ? subject.presetMode.modes : subject.preset.modes)
      : [];

    const schema: Schema[] = [
      {
        name: "entity",
        required: true,
        selector: { entity: this._entityPicker() },
      },
      {
        type: "expandable",
        name: "header",
        title: LABELS.header,
        schema: [
          { name: "visible", selector: { boolean: {} } },
          { name: "title", selector: { text: {} } },
          { name: "subtitle", selector: { text: {} } },
          { name: "icon", selector: { icon: {} } },
          { name: "icon_color", selector: { ui_color: {} } },
        ],
      },
      {
        type: "expandable",
        name: "modes",
        title: LABELS.modes,
        schema: [
          { name: "automatic", selector: { boolean: {} } },
          {
            name: "visible",
            ...options([
              ["always", "Always"],
              ["never", "Never"],
              ["manual", "While the mode can be set by hand"],
            ]),
          },
          {
            name: "style",
            ...options([
              ["chips", "Chips"],
              ["dropdown", "Dropdown"],
            ]),
          },
          // Only where there is an icon to show. Mode icons are set per mode
          // in the config flow, and most setups have none - a switch that
          // visibly does nothing is worse than no switch, because the user
          // spends the time finding out.
          ...(modes.some((mode) => mode.icon)
            ? [{ name: "icons", selector: { boolean: {} } }]
            : []),
        ],
      },
    ];

    if (isPreset) {
      const parameters = subject.preset.parameters.map((parameter) => ({
        value: parameter.key,
        label: parameter.name,
      }));
      schema.push(
        {
          type: "expandable",
          name: "values",
          title: LABELS.values,
          schema: [
            { name: "visible", selector: { boolean: {} } },
            // A list of plain keys round-trips through a multi select; rows
            // that also rename a parameter or give it an icon do not, and a
            // select fed those would show nothing selected and then throw the
            // overrides away on the first click. So it steps aside instead.
            this._hasParameterOverrides()
              ? { name: "parameters_note", type: "constant", value: YAML_ONLY }
              : {
                  name: "parameters",
                  selector: {
                    select: { multiple: true, mode: "list", options: parameters },
                  },
                },
            { name: "icons", selector: { boolean: {} } },
          ],
        },
        {
          type: "expandable",
          name: "editor",
          title: LABELS.editor,
          schema: [
            { name: "enabled", selector: { boolean: {} } },
            { name: "confirm", selector: { boolean: {} } },
            {
              name: "mode",
              ...options([
                ["picker", "Pick a mode in the card"],
                ["active", "The active mode"],
                ["all", "Every mode"],
              ]),
            },
            {
              name: "style",
              ...options([
                ["chips", "Chips"],
                ["dropdown", "Dropdown"],
              ]),
            },
            {
              name: "default_mode",
              ...options(modes.map((mode) => [mode.key, mode.name] as [string, string])),
            },
          ],
        },
      );
    }

    if (isPresetMode) {
      schema.push({
        type: "expandable",
        name: "presets",
        title: LABELS.presets,
        schema: [
          { name: "visible", selector: { boolean: {} } },
          { name: "values", selector: { boolean: {} } },
          { name: "editable", selector: { boolean: {} } },
        ],
      });
    }

    schema.push(
      {
        type: "expandable",
        name: "footer",
        title: LABELS.footer,
        schema: [
          { name: "visible", selector: { boolean: {} } },
          {
            name: "content",
            selector: {
              select: {
                multiple: true,
                mode: "list",
                options: [
                  { value: "preset_mode", label: "Preset mode" },
                  { value: "blueprint", label: "Blueprint" },
                  { value: "source", label: "Source entity" },
                  { value: "last_changed", label: "Last change" },
                ],
              },
            },
          },
        ],
      },
      {
        // No `name`: the action keys stay at the top level of the
        // configuration, where every other Home Assistant card has them.
        type: "expandable",
        title: LABELS.actions,
        schema: [
          { name: "tap_action", selector: { ui_action: { actions: ACTIONS } } },
          { name: "hold_action", selector: { ui_action: { actions: ACTIONS } } },
          { name: "double_tap_action", selector: { ui_action: { actions: ACTIONS } } },
        ],
      },
    );
    return schema;
  }

  /**
   * The configuration with every default filled in.
   *
   * A checkbox has no third position, so a form fed the raw configuration
   * would show every unset option as off - and the user would fix a checkbox
   * that was never wrong.
   */
  private _formData(): Record<string, unknown> {
    try {
      const resolved = resolveConfig({
        type: `custom:${CARD_TYPE}`,
        ...this._config,
        entity: this._config.entity ?? "sensor.placeholder",
      }) as unknown as Record<string, unknown>;
      return {
        ...resolved,
        entity: this._config.entity ?? "",
        values: {
          ...(resolved.values as Record<string, unknown>),
          // The form picks parameters, the configuration also allows renaming
          // them; only the plain list round-trips through a multi select.
          parameters: (this._config.values as Record<string, unknown> | undefined)
            ?.parameters,
        },
      };
    } catch (_err) {
      // An incomplete configuration - no entity yet - is the normal state of a
      // card that was just added.
      return { ...this._config };
    }
  }

  private _valueChanged(event: CustomEvent): void {
    event.stopPropagation();
    const data = { ...(event.detail.value as Record<string, unknown>) };
    fireEvent(this, "config-changed", { config: pruneConfig(data) });
  }

  private _label = (schema: { name?: string; title?: string }): string =>
    (schema.name && LABELS[schema.name]) || schema.title || schema.name || "";

  protected override render(): TemplateResult | typeof nothing {
    if (!this._hass) return nothing;
    const subject = this._subject;
    return html`
      <ha-form
        .hass=${this._hass}
        .data=${this._formData()}
        .schema=${this._schema(subject)}
        .computeLabel=${this._label}
        @value-changed=${this._valueChanged}
      ></ha-form>
      ${this._config.entity && !subject && this._structure
        ? html`<p style="color: var(--error-color)">
            ${localize(this._hass, "not_found", {
              entity: String(this._config.entity),
            })}
          </p>`
        : nothing}
    `;
  }
}
