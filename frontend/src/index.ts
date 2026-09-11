/**
 * Entry point: define the elements and offer the card in the picker.
 *
 * Loaded by the integration itself through `add_extra_js_url`, so a user never
 * adds a Lovelace resource and never has a card of a different version than
 * the integration behind it.
 */

import { CARD_TYPE, CARD_VERSION } from "./const";

import "./card";
import "./editor";

interface CustomCardEntry {
  type: string;
  name: string;
  description: string;
  preview: boolean;
  documentationURL: string;
}

declare global {
  interface Window {
    customCards?: CustomCardEntry[];
  }
}

window.customCards = window.customCards ?? [];
if (!window.customCards.some((card) => card.type === CARD_TYPE)) {
  window.customCards.push({
    type: CARD_TYPE,
    name: "Preset Manager",
    description: "The values of a preset, with the mode it is on right now.",
    // No preview: the card has nothing to draw without an entity, and a
    // picker tile that says "not found" sells it badly.
    preview: false,
    documentationURL: "https://github.com/julezdean/ha-preset-manager",
  });
}

// eslint-disable-next-line no-console
console.info(
  `%c PRESET-MANAGER-CARD %c ${CARD_VERSION} `,
  "color: white; background: #03a9f4; font-weight: 700;",
  "color: #03a9f4; background: white; font-weight: 700;",
);
