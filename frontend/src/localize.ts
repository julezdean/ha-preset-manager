/**
 * The card's own strings, in the two languages the integration ships.
 *
 * Everything the card says about *Home Assistant* - a state, a unit, an entity
 * name - comes from Home Assistant already translated. What is left is the
 * handful of sentences the card itself writes, and a German instance that
 * translates its config flow and then says "No preset mode" on the dashboard
 * would be a seam the user has no reason to expect.
 *
 * Unknown languages fall back to English, and an unknown key to itself, so a
 * missing translation is a plain word rather than an empty card.
 */

import type { HomeAssistant } from "./types/ha";

type Strings = Record<string, string>;

const EN: Strings = {
  active: "Active",
  apply: "Apply",
  automatic: "Automatic",
  blueprint: "Blueprint",
  changed: "Changed",
  editing: "Edit",
  follows: "Follows {entity}",
  mode_automatic: "Automatic mode selection",
  loading: "Loading…",
  manual: "Manual",
  mode: "Mode",
  no_entity: "Set “entity” to any entity of a preset.",
  not_a_preset: "“{entity}” belongs to a preset mode. A card shows a preset; point it at one of its entities.",
  no_mode: "No mode active",
  no_modes: "This preset mode has no modes yet.",
  no_parameters: "This preset has no parameters yet.",
  no_preset_mode: "No preset mode",
  not_editable: "Not editable here",
  not_found: "“{entity}” does not belong to Preset Manager.",
  not_set: "Not set",
  not_set_up: "Preset Manager is not set up.",
  orphaned: "Waiting for a preset mode; values do not resolve.",
  preset_mode: "Preset mode",
  source: "Source",
  unavailable: "Unavailable",
};

const DE: Strings = {
  active: "Aktiv",
  apply: "Übernehmen",
  automatic: "Automatik",
  blueprint: "Blueprint",
  changed: "Geändert",
  editing: "Bearbeiten",
  follows: "Folgt {entity}",
  mode_automatic: "Mode-Automatik",
  loading: "Wird geladen…",
  manual: "Manuell",
  mode: "Mode",
  no_entity: "„entity“ auf eine beliebige Entität eines Presets setzen.",
  not_a_preset: "„{entity}“ gehört zu einem Preset Mode. Eine Card zeigt ein Preset; zeig auf eine seiner Entitäten.",
  no_mode: "Kein Mode aktiv",
  no_modes: "Dieser Preset Mode hat noch keine Modes.",
  no_parameters: "Dieses Preset hat noch keine Parameter.",
  no_preset_mode: "Kein Preset Mode",
  not_editable: "Hier nicht editierbar",
  not_found: "„{entity}“ gehört nicht zu Preset Manager.",
  not_set: "Nicht gesetzt",
  not_set_up: "Preset Manager ist nicht eingerichtet.",
  orphaned: "Wartet auf einen Preset Mode; die Werte lösen nicht auf.",
  preset_mode: "Preset Mode",
  source: "Quelle",
  unavailable: "Nicht verfügbar",
};

const LANGUAGES: Record<string, Strings> = { en: EN, de: DE };

export function localize(
  hass: Pick<HomeAssistant, "language"> | undefined,
  key: string,
  placeholders: Record<string, string | number> = {},
): string {
  const language = (hass?.language ?? "en").toLowerCase().split("-")[0];
  const strings = LANGUAGES[language] ?? EN;
  let text = strings[key] ?? EN[key] ?? key;
  for (const [name, value] of Object.entries(placeholders)) {
    text = text.replace(`{${name}}`, String(value));
  }
  return text;
}
