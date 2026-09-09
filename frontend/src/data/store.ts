/**
 * One copy of the integration's structure per browser connection.
 *
 * Every card on a dashboard needs the same answer, so they share it: the
 * websocket command is called once, and each card subscribes to the result.
 * Ten cards on a wall panel would otherwise send ten identical requests on
 * every page load, and again after every reload of the integration.
 *
 * **When it goes stale.** The structure changes only through the config flow -
 * a mode added, a parameter renamed, a preset moved - and every one of those
 * ends in the entity or the device registry. So the store listens to those two
 * events rather than polling, and rather than asking for admin rights it does
 * not need: `config_entries/subscribe` would be the direct signal and is
 * admin-only, which would leave exactly the non-admin dashboard user with a
 * card that never updates. Values never come through here at all - they are
 * states, and states arrive on their own.
 */

import type { HomeAssistant } from "../types/ha";
import type { PresetManagerConfig } from "../types/data";

export const WS_TYPE_CONFIG = "preset_manager/config";

/** Registry events arrive in bursts after a reload; one refetch is enough. */
const REFRESH_DELAY = 400;

const EMPTY: PresetManagerConfig = {
  preset_modes: [],
  presets: [],
  blueprints: [],
};

type Listener = (config: PresetManagerConfig) => void;

class ConfigStore {
  private _config?: PresetManagerConfig;
  private _pending?: Promise<PresetManagerConfig>;
  private _listeners = new Set<Listener>();
  private _unsubscribes: Array<() => void> = [];
  private _timer?: ReturnType<typeof setTimeout>;
  private _serialised?: string;

  constructor(private _hass: HomeAssistant) {}

  /** The last known structure, or `undefined` before the first answer. */
  get current(): PresetManagerConfig | undefined {
    return this._config;
  }

  async load(hass: HomeAssistant): Promise<PresetManagerConfig> {
    // A card can outlive the connection object it was first given; the newest
    // one is always the one that works.
    this._hass = hass;
    if (this._config) return this._config;
    if (!this._pending) this._pending = this._fetch();
    return this._pending;
  }

  subscribe(listener: Listener): () => void {
    this._listeners.add(listener);
    if (this._listeners.size === 1) void this._watch();
    return () => {
      this._listeners.delete(listener);
      if (!this._listeners.size) this._stop();
    };
  }

  private async _fetch(): Promise<PresetManagerConfig> {
    try {
      const config = await this._hass.callWS<PresetManagerConfig>({
        type: WS_TYPE_CONFIG,
      });
      this._apply(config);
      return config;
    } catch (_err) {
      // An integration that is not set up, or one older than this card. Either
      // way the card has nothing to draw and says so itself; an empty
      // structure is a truthful answer and keeps every caller on one path.
      this._apply(EMPTY);
      return EMPTY;
    } finally {
      this._pending = undefined;
    }
  }

  private _apply(config: PresetManagerConfig): void {
    const serialised = JSON.stringify(config);
    // Registry events fire for every entity of a reload. Comparing here is
    // what keeps that from becoming one re-render of every card per entity.
    if (serialised === this._serialised) return;
    this._serialised = serialised;
    this._config = config;
    for (const listener of this._listeners) listener(config);
  }

  private async _watch(): Promise<void> {
    for (const event of ["entity_registry_updated", "device_registry_updated"]) {
      try {
        const unsubscribe = await this._hass.connection.subscribeEvents(
          () => this._scheduleRefresh(),
          event,
        );
        // Unsubscribed while the subscription was still being set up.
        if (!this._listeners.size) void unsubscribe();
        else this._unsubscribes.push(() => void unsubscribe());
      } catch (_err) {
        // Without the subscription the card still works; it just needs a page
        // reload to notice a new mode. Not worth an error on the dashboard.
      }
    }
  }

  private _scheduleRefresh(): void {
    if (this._timer) clearTimeout(this._timer);
    this._timer = setTimeout(() => {
      this._timer = undefined;
      this._config = undefined;
      // Through `_pending`, so a card calling `load` in this very moment
      // joins the refetch instead of starting a second one. `_fetch` handles
      // its own failure, so nothing is left floating here.
      this._pending = this._fetch();
    }, REFRESH_DELAY);
  }

  private _stop(): void {
    if (this._timer) clearTimeout(this._timer);
    this._timer = undefined;
    while (this._unsubscribes.length) this._unsubscribes.pop()!();
  }
}

const stores = new WeakMap<object, ConfigStore>();

function storeFor(hass: HomeAssistant): ConfigStore {
  let store = stores.get(hass.connection);
  if (!store) {
    store = new ConfigStore(hass);
    stores.set(hass.connection, store);
  }
  return store;
}

/** Return the structure, from the shared cache or from the integration. */
export function loadPresetManagerConfig(
  hass: HomeAssistant,
): Promise<PresetManagerConfig> {
  return storeFor(hass).load(hass);
}

/** What the store already knows, without waiting for a round trip. */
export function cachedPresetManagerConfig(
  hass: HomeAssistant,
): PresetManagerConfig | undefined {
  return storeFor(hass).current;
}

/** Follow every later change of the structure. Returns the unsubscribe. */
export function subscribePresetManagerConfig(
  hass: HomeAssistant,
  listener: (config: PresetManagerConfig) => void,
): () => void {
  return storeFor(hass).subscribe(listener);
}
