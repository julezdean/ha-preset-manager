import { describe, expect, it } from "vitest";

import { hasNoValue, isMissing } from "../src/util/ha";

/**
 * The distinction the editor stands or falls on.
 *
 * An editor entity reports `unknown` while its mode has no value for its
 * parameter - the state of every parameter of every mode of a preset nobody
 * has filled in yet. Treating that as "unavailable" disabled every control on
 * a fresh preset, which is precisely when the editor is wanted.
 */
describe("hasNoValue", () => {
  it.each([
    ["unavailable", true],
    ["unknown", true],
    [undefined, true],
    ["on", false],
    ["15", false],
    ["", false],
  ])("says %s has no value: %s", (state, expected) => {
    expect(hasNoValue(state)).toBe(expected);
  });
});

describe("isMissing", () => {
  it("is true only when the entity itself is gone", () => {
    expect(isMissing("unavailable")).toBe(true);
    expect(isMissing(undefined)).toBe(true);
  });

  it("is false for a value that was never set", () => {
    // The whole point: such a control stays usable.
    expect(isMissing("unknown")).toBe(false);
  });

  it("is false for a real value", () => {
    expect(isMissing("15")).toBe(false);
    expect(isMissing("")).toBe(false);
  });
});
