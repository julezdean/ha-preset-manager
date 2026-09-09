/**
 * The footer: the facts that explain the card without competing with it.
 *
 * Off unless asked for, and even then one small line. Where a value comes
 * from - which preset mode decided it, which blueprint defines the parameters,
 * which entity the whole dimension was handed to - matters exactly when
 * something looks wrong, which is not often enough to spend the top of the
 * card on.
 */

import { html, nothing, type TemplateResult } from "lit";

import { localize, localizeCount } from "../localize";
import { modeSourceEntityId } from "../data/state";
import { stateOf } from "../util/ha";
import type { CardContext } from "./context";
import type { FooterItem } from "../types/config";

/** "5 minutes ago", in the language of the instance. */
function relativeTime(hass: CardContext["hass"], iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((then - Date.now()) / 1000);
  const units: Array<[Intl.RelativeTimeFormatUnit, number]> = [
    ["year", 31536000],
    ["month", 2592000],
    ["day", 86400],
    ["hour", 3600],
    ["minute", 60],
  ];
  const formatter = new Intl.RelativeTimeFormat(hass.language || "en", {
    numeric: "auto",
  });
  for (const [unit, size] of units) {
    if (Math.abs(seconds) >= size) {
      return formatter.format(Math.round(seconds / size), unit);
    }
  }
  return formatter.format(Math.round(seconds), "second");
}

function item(context: CardContext, kind: FooterItem): string | null {
  const { hass, subject } = context;

  switch (kind) {
    case "preset_mode":
      if (subject.kind === "preset") {
        return subject.presetMode
          ? `${localize(hass, "preset_mode")}: ${subject.presetMode.name}`
          : localize(hass, "orphaned");
      }
      return localizeCount(
        hass,
        "presets_one",
        "presets_other",
        subject.presets.length,
      );

    case "blueprint":
      if (subject.kind !== "preset" || !subject.blueprint) return null;
      return `${localize(hass, "blueprint")}: ${subject.blueprint.name}`;

    case "source": {
      const entityId =
        subject.kind === "preset_mode" ? subject.presetMode.source_entity : null;
      if (!entityId) return null;
      const entity = hass.states[entityId];
      return `${localize(hass, "source")}: ${
        entity?.attributes.friendly_name ?? entityId
      }`;
    }

    case "last_changed": {
      const entity = stateOf(hass, modeSourceEntityId(subject));
      if (!entity) return null;
      return `${localize(hass, "changed")}: ${relativeTime(hass, entity.last_changed)}`;
    }

    default:
      return null;
  }
}

export function renderFooter(context: CardContext): TemplateResult | typeof nothing {
  if (!context.config.footer.visible) return nothing;
  const parts = context.config.footer.content
    .map((kind) => item(context, kind))
    .filter((text): text is string => text !== null);
  if (!parts.length) return nothing;

  return html`
    <div class="section footer">
      ${parts.map((text) => html`<span>${text}</span>`)}
    </div>
  `;
}
