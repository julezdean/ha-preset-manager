import { describe, expect, it } from "vitest";

import { localize } from "../src/localize";

describe("localize", () => {
  it("speaks the language of the instance", () => {
    expect(localize({ language: "en" }, "no_preset_mode")).toBe("No preset mode");
    expect(localize({ language: "de" }, "no_preset_mode")).toBe("Kein Preset Mode");
  });

  it("ignores the region of a language tag", () => {
    expect(localize({ language: "de-CH" }, "manual")).toBe("Manuell");
  });

  it("falls back to English for a language it does not have", () => {
    expect(localize({ language: "fr" }, "manual")).toBe("Manual");
  });

  it("survives having no hass at all", () => {
    expect(localize(undefined, "manual")).toBe("Manual");
  });

  it("fills placeholders", () => {
    expect(localize({ language: "en" }, "not_found", { entity: "light.x" })).toBe(
      "“light.x” does not belong to Preset Manager.",
    );
  });

  it("returns the key rather than an empty card for an unknown string", () => {
    expect(localize({ language: "en" }, "nope")).toBe("nope");
  });

  it("keeps German entries in step with English ones", () => {
    // A missing German string would silently fall back and read as a seam.
    for (const key of [
      "mode_automatic",
      "no_mode",
      "not_set",
      "unavailable",
      "orphaned",
    ]) {
      expect(localize({ language: "de" }, key)).not.toBe(localize({ language: "en" }, key));
    }
  });
});
