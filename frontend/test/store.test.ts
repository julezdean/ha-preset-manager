import { beforeEach, describe, expect, it, vi } from "vitest";

import {
  cachedPresetManagerConfig,
  loadPresetManagerConfig,
  subscribePresetManagerConfig,
  WS_TYPE_CONFIG,
} from "../src/data/store";
import { hass, structure } from "./fixtures";
import type { HomeAssistant } from "../src/types/ha";

/** A `hass` whose websocket answers can be counted and swapped out. */
function connected(answers: unknown[]): {
  hass: HomeAssistant;
  calls: () => number;
  fire: () => void;
} {
  let index = 0;
  let handler: (() => void) | undefined;
  const callWS = vi.fn(async (message: Record<string, unknown>) => {
    expect(message.type).toBe(WS_TYPE_CONFIG);
    const answer = answers[Math.min(index, answers.length - 1)];
    index += 1;
    if (answer instanceof Error) throw answer;
    return answer as never;
  });
  const connection = {
    subscribeEvents: vi.fn(async (callback: () => void) => {
      handler = callback;
      return async () => undefined;
    }),
    subscribeMessage: vi.fn(async () => async () => undefined),
  };
  return {
    hass: hass({}, { callWS, connection } as Partial<HomeAssistant>),
    calls: () => callWS.mock.calls.length,
    fire: () => handler?.(),
  };
}

describe("the shared structure", () => {
  beforeEach(() => {
    vi.useRealTimers();
  });

  it("asks once, however many cards want it", async () => {
    const { hass: instance, calls } = connected([structure()]);
    const [first, second] = await Promise.all([
      loadPresetManagerConfig(instance),
      loadPresetManagerConfig(instance),
    ]);
    await loadPresetManagerConfig(instance);
    // Ten cards on a wall panel are ten requests without this.
    expect(calls()).toBe(1);
    expect(first).toBe(second);
  });

  it("answers from the cache without a round trip", async () => {
    const { hass: instance } = connected([structure()]);
    expect(cachedPresetManagerConfig(instance)).toBeUndefined();
    await loadPresetManagerConfig(instance);
    expect(cachedPresetManagerConfig(instance)?.presets).toHaveLength(2);
  });

  it("hands out an empty structure when the command is not there", async () => {
    // An integration that is not set up, or one older than this card. The card
    // draws its own message; this keeps every caller on one path.
    const { hass: instance } = connected([new Error("unknown command")]);
    const config = await loadPresetManagerConfig(instance);
    expect(config).toEqual({ preset_modes: [], presets: [], blueprints: [] });
  });

  it("keeps separate connections apart", async () => {
    const a = connected([structure()]);
    const b = connected([structure({ presets: [] })]);
    expect((await loadPresetManagerConfig(a.hass)).presets).toHaveLength(2);
    expect((await loadPresetManagerConfig(b.hass)).presets).toHaveLength(0);
  });

  it("refetches after a registry change and tells its subscribers", async () => {
    vi.useFakeTimers();
    const changed = structure({ blueprints: [] });
    const { hass: instance, calls, fire } = connected([structure(), changed]);
    const listener = vi.fn();
    const unsubscribe = subscribePresetManagerConfig(instance, listener);
    await loadPresetManagerConfig(instance);
    await vi.advanceTimersByTimeAsync(0);

    fire();
    await vi.advanceTimersByTimeAsync(500);
    expect(calls()).toBe(2);
    expect(listener).toHaveBeenLastCalledWith(changed);
    unsubscribe();
    vi.useRealTimers();
  });

  it("collapses the burst of events a reload produces into one refetch", async () => {
    vi.useFakeTimers();
    const { hass: instance, calls, fire } = connected([structure()]);
    const unsubscribe = subscribePresetManagerConfig(instance, () => undefined);
    await loadPresetManagerConfig(instance);
    await vi.advanceTimersByTimeAsync(0);

    // A reload of the hub fires one of these per entity.
    for (let i = 0; i < 40; i += 1) fire();
    await vi.advanceTimersByTimeAsync(500);
    expect(calls()).toBe(2);
    unsubscribe();
    vi.useRealTimers();
  });

  it("does not wake a card when the structure came back the same", async () => {
    vi.useFakeTimers();
    const { hass: instance, fire } = connected([structure(), structure()]);
    const listener = vi.fn();
    const unsubscribe = subscribePresetManagerConfig(instance, listener);
    await loadPresetManagerConfig(instance);
    await vi.advanceTimersByTimeAsync(0);
    listener.mockClear();

    fire();
    await vi.advanceTimersByTimeAsync(500);
    // Renaming an unrelated entity of another integration must not redraw.
    expect(listener).not.toHaveBeenCalled();
    unsubscribe();
    vi.useRealTimers();
  });
});
