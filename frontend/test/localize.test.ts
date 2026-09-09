import { describe, expect, it } from "vitest";

import { localize, localizeCount } from "../src/localize";

describe("localize", () => {
  it("speaks the language of the instance", () => {
    expect(localize({ language: "en" }, "no_preset_mode")).toBe("No preset mode");
    expect(localize({ language: "de" }, "no_preset_mode")).toBe("Kein Preset Mode");
  });

  it("ignores the region of a language tag", () => {
    expect(localize({ language: "de-CH" }, "automatic")).toBe("Automatik");
  });

  it("falls back to English for a language it does not have", () => {
    expect(localize({ language: "fr" }, "automatic")).toBe("Automatic");
  });

  it("survives having no hass at all", () => {
    expect(localize(undefined, "automatic")).toBe("Automatic");
  });

  it("fills placeholders", () => {
    expect(localize({ language: "en" }, "follows", { entity: "input_select.x" })).toBe(
      "Follows input_select.x",
    );
  });

  it("returns the key rather than an empty card for an unknown string", () => {
    expect(localize({ language: "en" }, "nope")).toBe("nope");
  });

  it("keeps German entries in step with English ones", () => {
    // A missing German string would silently fall back and read as a seam.
    for (const key of ["automatic", "no_mode", "not_set", "unavailable", "orphaned"]) {
      expect(localize({ language: "de" }, key)).not.toBe(localize({ language: "en" }, key));
    }
  });
});

describe("localizeCount", () => {
  it.each([
    [0, "0 presets"],
    [1, "1 preset"],
    [3, "3 presets"],
  ])("counts %i as %s", (count, expected) => {
    expect(localizeCount({ language: "en" }, "presets_one", "presets_other", count)).toBe(
      expected,
    );
  });
});
