import { describe, expect, it } from "vitest";

import {
  activeMode,
  activeModeKey,
  followsPresetMode,
  modeLockReason,
} from "../src/data/state";
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

describe("followsPresetMode", () => {
  it.each([
    ["on", true],
    ["off", false],
  ])("reports the switch of a preset as %s", (state, expected) => {
    const states = {
      "switch.motion_sensor_living_room_follows_preset_mode": entity(
        "switch.motion_sensor_living_room_follows_preset_mode",
        state,
      ),
    };
    expect(followsPresetMode(hass(states), preset)).toBe(expected);
  });

  it("reports nothing for a preset mode, which has no such switch", () => {
    expect(followsPresetMode(hass({}), presetMode)).toBeNull();
  });

  it("reports nothing while the entity does not exist", () => {
    expect(followsPresetMode(hass({}), preset)).toBeNull();
  });
});

describe("modeLockReason", () => {
  it("never lets a preset mode be set", () => {
    // Its mode is computed; that is the whole point of it.
    expect(modeLockReason(hass({}), presetMode)).toBe("computed");
  });

  it("lets a preset be set while it is not following", () => {
    const states = {
      "switch.motion_sensor_living_room_follows_preset_mode": entity(
        "switch.motion_sensor_living_room_follows_preset_mode",
        "off",
      ),
    };
    expect(modeLockReason(hass(states), preset)).toBeNull();
  });

  it("refuses a preset that is following, the way the service does", () => {
    const states = {
      "switch.motion_sensor_living_room_follows_preset_mode": entity(
        "switch.motion_sensor_living_room_follows_preset_mode",
        "on",
      ),
    };
    expect(modeLockReason(hass(states), preset)).toBe("following");
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

  it("refuses a preset whose selector is missing from the registry", () => {
    const withoutSelector = structure({
      presets: [
        {
          ...CONFIG.presets[0],
          entities: {
            active_mode: "sensor.motion_sensor_living_room_active_mode",
            automatic: "switch.motion_sensor_living_room_follows_preset_mode",
          },
        },
      ],
    });
    const subject = resolveSubject(
      withoutSelector,
      "sensor.motion_sensor_living_room_active_mode",
    )!;
    expect(modeLockReason(hass({}), subject)).toBe("missing");
  });
});
