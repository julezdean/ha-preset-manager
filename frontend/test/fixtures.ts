/**
 * A setup the tests can reason about.
 *
 * It is the example from the README, so a test that fails says something about
 * a real configuration rather than about a shape invented for it: a "House
 * Mode" with four modes, a motion sensor preset following it with three
 * parameters, and a shutter preset that lost its preset mode.
 */

import type { PresetManagerConfig } from "../src/types/data";
import type { HassEntity, HomeAssistant } from "../src/types/ha";

export const MODES = [
  { key: "home", name: "Home", icon: "mdi:home" },
  { key: "away", name: "Away", icon: null },
  { key: "night", name: "Night", icon: "mdi:weather-night" },
  { key: "window_open", name: "Window open", icon: null },
];

export function structure(
  overrides: Partial<PresetManagerConfig> = {},
): PresetManagerConfig {
  return {
    preset_modes: [
      {
        id: "pm1",
        name: "House Mode",
        device_id: "dev-pm1",
        modes: MODES,
        source_entity: null,
        has_conditions: true,
        entities: { mode: "sensor.house_mode_mode" },
      },
    ],
    presets: [
      {
        id: "p1",
        name: "Motion Sensor Living Room",
        device_id: "dev-p1",
        preset_mode: "pm1",
        blueprint: null,
        modes: MODES,
        parameters: [
          {
            key: "brightness",
            name: "Brightness",
            type: "number",
            entity: "sensor.motion_sensor_living_room_brightness",
            editors: {
              home: "number.motion_sensor_living_room_home_brightness",
              away: "number.motion_sensor_living_room_away_brightness",
              night: "number.motion_sensor_living_room_night_brightness",
              window_open: "number.motion_sensor_living_room_window_open_brightness",
            },
          },
          {
            key: "off_delay",
            name: "Off delay",
            type: "number",
            entity: "sensor.motion_sensor_living_room_off_delay",
            editors: { night: "number.motion_sensor_living_room_night_off_delay" },
          },
        ],
        entities: {
          active_mode: "sensor.motion_sensor_living_room_active_mode",
          mode_selection: "select.motion_sensor_living_room_mode_selection",
          automatic: "switch.motion_sensor_living_room_follows_preset_mode",
        },
      },
      {
        id: "p2",
        name: "Shutter Living Room",
        device_id: "dev-p2",
        // Its preset mode was deleted; it keeps everything but the dimension.
        preset_mode: null,
        blueprint: "bp1",
        modes: MODES,
        parameters: [],
        entities: {
          active_mode: "sensor.shutter_living_room_active_mode",
          mode_selection: "select.shutter_living_room_mode_selection",
          automatic: "switch.shutter_living_room_follows_preset_mode",
        },
      },
    ],
    blueprints: [{ id: "bp1", name: "Shutters" }],
    ...overrides,
  };
}

export function entity(
  entityId: string,
  state: string,
  attributes: Record<string, unknown> = {},
): HassEntity {
  return {
    entity_id: entityId,
    state,
    attributes,
    last_changed: "2026-09-09T10:00:00+00:00",
    last_updated: "2026-09-09T10:00:00+00:00",
  };
}

export function hass(
  states: Record<string, HassEntity> = {},
  overrides: Partial<HomeAssistant> = {},
): HomeAssistant {
  return {
    states,
    entities: {},
    connection: {
      subscribeEvents: async () => async () => undefined,
      subscribeMessage: async () => async () => undefined,
    },
    language: "en",
    locale: {},
    themes: {},
    callWS: async () => ({}) as never,
    callService: async () => undefined,
    formatEntityState: (item: HassEntity) =>
      item.attributes.unit_of_measurement
        ? `${item.state} ${item.attributes.unit_of_measurement}`
        : item.state,
    localize: (key: string) => key,
    ...overrides,
  };
}
