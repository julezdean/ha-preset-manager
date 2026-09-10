import { describe, expect, it } from "vitest";

import { CardConfigError, pruneConfig, resolveConfig } from "../src/config";

const MINIMAL = { type: "custom:preset-manager-card", entity: "sensor.house_mode_mode" };

describe("resolveConfig", () => {
  it("needs nothing but an entity", () => {
    const config = resolveConfig(MINIMAL);
    expect(config.entity).toBe("sensor.house_mode_mode");
    expect(config.header.visible).toBe(true);
    expect(config.values.visible).toBe(true);
    expect(config.modes.visible).toBe("always");
  });

  it("keeps the editors closed unless asked", () => {
    // They are configuration entities: setting a preset up, not running it.
    expect(resolveConfig(MINIMAL).editor.enabled).toBe(false);
  });

  it("says what to write when the entity is missing", () => {
    expect(() => resolveConfig({ type: "x" })).toThrow(CardConfigError);
    expect(() => resolveConfig({ type: "x" })).toThrow(/entity of Preset Manager/);
  });

  it("rejects something that is not an entity id", () => {
    expect(() => resolveConfig({ ...MINIMAL, entity: "house_mode" })).toThrow(
      /is not an entity id/,
    );
  });

  it("names the option when a group is written as a scalar", () => {
    expect(() => resolveConfig({ ...MINIMAL, header: true })).toThrow(/"header"/);
  });

  it("names the option when a value is out of range", () => {
    expect(() => resolveConfig({ ...MINIMAL, editor: { mode: "sometimes" } })).toThrow(
      /picker, active, all/,
    );
  });

  it("shows the mode row and the automatic unless told otherwise", () => {
    const config = resolveConfig(MINIMAL);
    expect(config.modes.visible).toBe("always");
    expect(config.header.automatic).toBe(true);
  });

  it("takes them as plain switches once they are set", () => {
    const config = resolveConfig({
      ...MINIMAL,
      header: { automatic: false },
      modes: { visible: false },
    });
    expect(config.modes.visible).toBe("never");
    expect(config.header.automatic).toBe(false);
  });

  it.each([
    [true, "always"],
    [false, "never"],
    ["always", "always"],
    ["never", "never"],
    ["manual", "manual"],
  ])("takes %s as %s for the mode row", (written, expected) => {
    expect(resolveConfig({ ...MINIMAL, modes: { visible: written } }).modes.visible).toBe(
      expected,
    );
  });

  it("names what it accepts for the mode row", () => {
    expect(() => resolveConfig({ ...MINIMAL, modes: { visible: "sometimes" } })).toThrow(
      /always, never, manual/,
    );
  });

  it("accepts a parameter list of keys and of groups", () => {
    const config = resolveConfig({
      ...MINIMAL,
      values: {
        parameters: ["brightness", { parameter: "off_delay", name: "Run-on", icon: false }],
      },
    });
    expect(config.values.parameters).toEqual([
      { parameter: "brightness" },
      { parameter: "off_delay", name: "Run-on", icon: false },
    ]);
  });

  it("shows a footer that was given content, without a second switch", () => {
    const config = resolveConfig({ ...MINIMAL, footer: { content: ["blueprint"] } });
    expect(config.footer.visible).toBe(true);
    expect(config.footer.content).toEqual(["blueprint"]);
  });

  it("gives an asked-for footer something to say", () => {
    const config = resolveConfig({ ...MINIMAL, footer: { visible: true } });
    expect(config.footer.content).toEqual(["preset_mode"]);
  });

  it("leaves keys Lovelace adds alone", () => {
    expect(() =>
      resolveConfig({ ...MINIMAL, grid_options: { columns: 6 }, visibility: [] }),
    ).not.toThrow();
  });

  it("takes false as “remove this line”", () => {
    const config = resolveConfig({ ...MINIMAL, header: { subtitle: false, icon: false } });
    expect(config.header.subtitle).toBe(false);
    expect(config.header.icon).toBe(false);
  });
});

describe("pruneConfig", () => {
  it("writes nothing that the card would have assumed", () => {
    const resolved = resolveConfig(MINIMAL) as unknown as Record<string, unknown>;
    expect(pruneConfig({ ...resolved, entity: MINIMAL.entity, type: MINIMAL.type })).toEqual(
      MINIMAL,
    );
  });

  it("keeps what differs from the default", () => {
    const resolved = resolveConfig(MINIMAL) as unknown as Record<string, unknown>;
    const pruned = pruneConfig({
      ...resolved,
      type: MINIMAL.type,
      entity: MINIMAL.entity,
      editor: { enabled: true, mode: "picker", style: "chips" },
      modes: { visible: true },
    });
    // `mode: picker` and `style: chips` are the defaults and go; the other two
    // stay.
    expect(pruned).toEqual({
      ...MINIMAL,
      editor: { enabled: true },
      modes: { visible: true },
    });
  });

  it("survives a round trip through the card", () => {
    const written = pruneConfig({
      type: MINIMAL.type,
      entity: MINIMAL.entity,
      modes: { visible: true },
    });
    expect(resolveConfig(written).modes.visible).toBe("always");
  });
});

describe("the presets of a preset mode", () => {
  const MODE_CARD = { ...MINIMAL, entity: "sensor.house_mode_mode" };

  it("shows nothing until asked", () => {
    expect(resolveConfig(MODE_CARD).presets.show).toBe("none");
  });

  it.each(["names", "values", "editable"])("takes %s", (show) => {
    expect(resolveConfig({ ...MODE_CARD, presets: { show } }).presets.show).toBe(show);
  });

  it("names the four rungs when handed something else", () => {
    expect(() =>
      resolveConfig({ ...MODE_CARD, presets: { show: "everything" } }),
    ).toThrow(/none, names, values, editable/);
  });

  it.each([
    [{ editable: true }, "editable"],
    [{ values: true }, "values"],
    [{ visible: true }, "names"],
    [{ visible: false }, "none"],
  ])("refuses the old spelling %j and says what to write", (presets, expected) => {
    // Three switches for four exclusive states let half their combinations
    // contradict themselves - "editable but no values" rendered a read-only
    // list under a switch that read "editable". Refused rather than guessed.
    expect(() => resolveConfig({ ...MODE_CARD, presets })).toThrow(
      new RegExp(`presets: \\{show: ${expected}\\}`),
    );
  });
});
