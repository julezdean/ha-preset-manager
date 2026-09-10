import { describe, expect, it } from "vitest";

import { activeMode, activeModeKey, automaticState, modeLockReason } from "../src/data/state";
import { resolveSubject } from "../src/data/subject";
import { entity, hass, structure } from "./fixtures";

const CONFIG = structure();
const presetMode = resolveSubject(CONFIG, "sensor.house_mode_mode")!;
const preset = resolveSubject(CONFIG, "sensor.motion_sensor_living_room_active_mode")!;

describe("activeModeKey", () => {
  it("reads the stable key, not the display name", () => {
    // The state is the name and is renameable and translated; `mode_key` is
    // the thing every other part of the integration keys off.
    const states = {
      "sensor.house_mode_mode": entity("sensor.house_mode_mode", "Night", {
        mode_key: "night",
      }),
    };
    expect(activeModeKey(hass(states), presetMode)).toBe("night");
    expect(activeMode(hass(states), presetMode)?.name).toBe("Night");
  });

  it("reads a preset from its own active mode sensor", () => {
    const states = {
      "sensor.motion_sensor_living_room_active_mode": entity(
        "sensor.motion_sensor_living_room_active_mode",
        "Home",
        { mode_key: "home" },
      ),
    };
    expect(activeModeKey(hass(states), preset)).toBe("home");
  });

  it("is nothing while no mode is active", () => {
    // No condition matched, or the source entity names no mode.
    const states = {
      "sensor.house_mode_mode": entity("sensor.house_mode_mode", "unknown", {}),
    };
    expect(activeModeKey(hass(states), presetMode)).toBeNull();
    expect(activeMode(hass(states), presetMode)).toBeNull();
  });

  it("is nothing while the entity does not exist at all", () => {
    expect(activeModeKey(hass({}), presetMode)).toBeNull();
  });

  it("does not invent a mode for a key that was deleted", () => {
    const states = {
      "sensor.house_mode_mode": entity("sensor.house_mode_mode", "Party", {
        mode_key: "party",
      }),
    };
    expect(activeMode(hass(states), presetMode)).toBeNull();
  });
});

describe("automaticState", () => {
  it.each([
    ["on", true],
    ["off", false],
  ])("reports the switch as %s", (state, expected) => {
    const states = {
      "switch.house_mode_automatic": entity("switch.house_mode_automatic", state),
    };
    expect(automaticState(hass(states), presetMode)).toBe(expected);
  });

  it("reads a preset from its own switch, not from the dimension's", () => {
    const states = {
      "switch.house_mode_automatic": entity("switch.house_mode_automatic", "on"),
      "switch.motion_sensor_living_room_follows_preset_mode": entity(
        "switch.motion_sensor_living_room_follows_preset_mode",
        "off",
      ),
    };
    expect(automaticState(hass(states), preset)).toBe(false);
  });

  it("reports nothing when there is no automatic", () => {
    expect(automaticState(hass({}), presetMode)).toBeNull();
  });
});

describe("modeLockReason", () => {
  it("lets the mode be set while the automatic is off", () => {
    const states = {
      "switch.house_mode_automatic": entity("switch.house_mode_automatic", "off"),
    };
    expect(modeLockReason(hass(states), presetMode)).toBeNull();
  });

  it("refuses while the automatic is on, the way the service does", () => {
    const states = {
      "switch.house_mode_automatic": entity("switch.house_mode_automatic", "on"),
    };
    expect(modeLockReason(hass(states), presetMode)).toBe("automatic");
  });

  it("refuses when the preset mode belongs to another entity", () => {
    const external = structure({
      preset_modes: [
        { ...CONFIG.preset_modes[0], source_entity: "input_select.house_mode" },
      ],
    });
    const subject = resolveSubject(external, "sensor.house_mode_mode")!;
    expect(modeLockReason(hass({}), subject)).toBe("external");
  });

  it("refuses when the selector is missing from the registry", () => {
    const withoutSelector = structure({
      preset_modes: [
        { ...CONFIG.preset_modes[0], entities: { mode: "sensor.house_mode_mode" } },
      ],
    });
    const subject = resolveSubject(withoutSelector, "sensor.house_mode_mode")!;
    expect(modeLockReason(hass({}), subject)).toBe("missing");
  });

  it("lets a preset be set while its own automatic is off", () => {
    // Even though its preset mode is running on its conditions: that is the
    // whole point of the preset having a switch of its own.
    const states = {
      "switch.house_mode_automatic": entity("switch.house_mode_automatic", "on"),
      "switch.motion_sensor_living_room_follows_preset_mode": entity(
        "switch.motion_sensor_living_room_follows_preset_mode",
        "off",
      ),
    };
    expect(modeLockReason(hass(states), preset)).toBeNull();
  });

  it("refuses a preset that follows no preset mode", () => {
    const orphan = resolveSubject(CONFIG, "sensor.shutter_living_room_active_mode")!;
    const states = {
      "switch.shutter_living_room_follows_preset_mode": entity(
        "switch.shutter_living_room_follows_preset_mode",
        "off",
      ),
    };
    expect(modeLockReason(hass(states), orphan)).toBe("missing");
  });
});
