import { describe, expect, it } from "vitest";

import {
  orderedParameters,
  presetEntityIds,
  resolveSubject,
  watchedEntityIds,
} from "../src/data/subject";
import { structure } from "./fixtures";

const CONFIG = structure();

describe("resolveSubject", () => {
  it("finds the preset mode behind its mode sensor", () => {
    const subject = resolveSubject(CONFIG, "sensor.house_mode_mode");
    expect(subject?.kind).toBe("preset_mode");
    expect(subject && subject.kind === "preset_mode" && subject.presetMode.name).toBe(
      "House Mode",
    );
  });

  it.each([
    ["select.house_mode_active_mode"],
    ["switch.house_mode_automatic"],
  ])("finds it behind %s as well", (entityId) => {
    expect(resolveSubject(CONFIG, entityId)?.kind).toBe("preset_mode");
  });

  it("finds the preset behind its active mode sensor", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode");
    expect(subject?.kind).toBe("preset");
    expect(subject && subject.kind === "preset" && subject.preset.name).toBe(
      "Motion Sensor Living Room",
    );
  });

  it("finds the preset behind one of its values", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_brightness");
    expect(subject && subject.kind === "preset" && subject.preset.id).toBe("p1");
  });

  it("finds the preset behind one of its per-mode editors", () => {
    // The editors are the entity a user is most likely to have to hand: they
    // are what a dashboard already shows to change a value.
    const subject = resolveSubject(
      CONFIG,
      "number.motion_sensor_living_room_night_brightness",
    );
    expect(subject && subject.kind === "preset" && subject.preset.id).toBe("p1");
  });

  it("resolves what a preset follows", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode");
    expect(subject && subject.kind === "preset" && subject.presetMode?.name).toBe(
      "House Mode",
    );
  });

  it("keeps a preset whose preset mode was deleted", () => {
    const subject = resolveSubject(CONFIG, "sensor.shutter_living_room_active_mode");
    expect(subject?.kind).toBe("preset");
    expect(subject && subject.kind === "preset" && subject.presetMode).toBeNull();
    // Its blueprint is untouched by the loss of the dimension.
    expect(subject && subject.kind === "preset" && subject.blueprint?.name).toBe("Shutters");
  });

  it("lists the presets of a preset mode, and only those", () => {
    const subject = resolveSubject(CONFIG, "sensor.house_mode_mode");
    expect(subject && subject.kind === "preset_mode" && subject.presets.map((p) => p.id))
      .toEqual(["p1"]);
  });

  it("returns nothing for an entity of another integration", () => {
    expect(resolveSubject(CONFIG, "light.living_room")).toBeNull();
  });
});

describe("watchedEntityIds", () => {
  it("covers every entity a preset card draws, plus its preset mode", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode")!;
    const watched = watchedEntityIds(subject);
    expect(watched).toContain("sensor.motion_sensor_living_room_brightness");
    expect(watched).toContain("number.motion_sensor_living_room_night_brightness");
    // The automatic decides whether the mode chips are usable, so a change of
    // it has to redraw a preset card too.
    expect(watched).toContain("switch.house_mode_automatic");
  });

  it("covers the followed entity of an external preset mode", () => {
    const external = structure({
      preset_modes: [
        {
          ...CONFIG.preset_modes[0],
          source_entity: "input_select.house_mode",
          entities: { mode: "sensor.house_mode_mode" },
        },
      ],
    });
    const subject = resolveSubject(external, "sensor.house_mode_mode")!;
    expect(watchedEntityIds(subject)).toContain("input_select.house_mode");
  });

  it("stays small - a card must not redraw for the whole house", () => {
    const subject = resolveSubject(CONFIG, "sensor.house_mode_mode")!;
    expect(new Set(watchedEntityIds(subject)).size).toBeLessThan(20);
  });
});

describe("orderedParameters", () => {
  const preset = CONFIG.presets[0];

  it("keeps the configured order when nothing is asked for", () => {
    expect(orderedParameters(preset, null).map((item) => item.key)).toEqual([
      "brightness",
      "off_delay",
    ]);
  });

  it("selects and reorders", () => {
    expect(orderedParameters(preset, ["off_delay", "brightness"]).map((i) => i.key)).toEqual(
      ["off_delay", "brightness"],
    );
  });

  it("drops a parameter that no longer exists instead of breaking", () => {
    // A parameter deleted in the config flow while a dashboard still names it.
    expect(orderedParameters(preset, ["brightness", "gone"]).map((i) => i.key)).toEqual([
      "brightness",
    ]);
  });
});

describe("presetEntityIds", () => {
  it("skips a value entity the registry has no id for", () => {
    const preset = {
      ...CONFIG.presets[0],
      parameters: [{ ...CONFIG.presets[0].parameters[0], entity: null }],
    };
    expect(presetEntityIds(preset)).not.toContain(null);
  });
});
