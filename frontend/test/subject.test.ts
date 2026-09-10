import { describe, expect, it } from "vitest";

import {
  belongsToPresetMode,
  orderedParameters,
  presetEntityIds,
  resolveSubject,
  watchedEntityIds,
} from "../src/data/subject";
import { structure } from "./fixtures";

const CONFIG = structure();

describe("resolveSubject", () => {
  it("finds nothing behind a preset mode, which has no card", () => {
    // It is a definition plus the logic that picks a mode, and what it
    // computes is one sensor that every core card already draws.
    expect(resolveSubject(CONFIG, "sensor.house_mode_mode")).toBeNull();
    expect(belongsToPresetMode(CONFIG, "sensor.house_mode_mode")).toBe(true);
  });

  it("tells an entity of ours from one that is not", () => {
    // Two different mistakes, and the card says two different sentences.
    expect(belongsToPresetMode(CONFIG, "light.living_room")).toBe(false);
  });

  it("finds the preset behind its active mode sensor", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode");
    expect(subject?.preset.name).toBe(
      "Motion Sensor Living Room",
    );
  });

  it("finds the preset behind one of its values", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_brightness");
    expect(subject?.preset.id).toBe("p1");
  });

  it("finds the preset behind one of its per-mode editors", () => {
    // The editors are the entity a user is most likely to have to hand: they
    // are what a dashboard already shows to change a value.
    const subject = resolveSubject(
      CONFIG,
      "number.motion_sensor_living_room_night_brightness",
    );
    expect(subject?.preset.id).toBe("p1");
  });

  it("resolves what a preset follows", () => {
    const subject = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode");
    expect(subject?.presetMode?.name).toBe(
      "House Mode",
    );
  });

  it("keeps a preset whose preset mode was deleted", () => {
    const subject = resolveSubject(CONFIG, "sensor.shutter_living_room_active_mode");
    expect(subject?.presetMode).toBeNull();
    // Its blueprint is untouched by the loss of the dimension.
    expect(subject?.blueprint?.name).toBe("Shutters");
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
    // Its own switch decides whether the chips are usable, and the mode of
    // its preset mode decides what it resolves to - both redraw the card.
    expect(watched).toContain("switch.motion_sensor_living_room_follows_preset_mode");
    expect(watched).toContain("sensor.house_mode_mode");
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
    // Not this card's entity, but what its preset mode follows decides the
    // mode this preset resolves against.
    const subject = resolveSubject(
      external,
      "sensor.motion_sensor_living_room_active_mode",
    )!;
    expect(watchedEntityIds(subject)).toContain("input_select.house_mode");
  });

  it("stays small - a card must not redraw for the whole house", () => {
    const subject = resolveSubject(
      CONFIG,
      "sensor.motion_sensor_living_room_active_mode",
    )!;
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
