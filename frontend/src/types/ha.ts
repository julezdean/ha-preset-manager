/**
 * The parts of Home Assistant this card actually touches.
 *
 * Declared here rather than pulled from a helper package: the card needs a
 * dozen fields of a very large object, and a dependency on somebody else's
 * snapshot of the frontend types is a dependency that goes stale without
 * anything here changing.
 */

export interface HassEntityAttributes {
  friendly_name?: string;
  icon?: string;
  unit_of_measurement?: string;
  device_class?: string;
  [key: string]: unknown;
}

export interface HassEntity {
  entity_id: string;
  state: string;
  attributes: HassEntityAttributes;
  last_changed: string;
  last_updated: string;
}

export interface HassEntityRegistryEntry {
  entity_id: string;
  device_id: string | null;
  hidden_by: string | null;
  disabled_by: string | null;
}

export interface HassConnection {
  subscribeEvents<T>(
    callback: (event: T) => void,
    eventType: string,
  ): Promise<() => Promise<void>>;
  subscribeMessage<T>(
    callback: (message: T) => void,
    subscription: Record<string, unknown>,
  ): Promise<() => Promise<void>>;
}

export interface HomeAssistant {
  states: Record<string, HassEntity>;
  entities: Record<string, HassEntityRegistryEntry>;
  connection: HassConnection;
  language: string;
  locale: unknown;
  themes: unknown;
  user?: { is_admin: boolean };
  callWS<T>(message: Record<string, unknown>): Promise<T>;
  callService(
    domain: string,
    service: string,
    data?: Record<string, unknown>,
    target?: Record<string, unknown>,
  ): Promise<unknown>;
  /** Formats a state the way every core card shows it, unit and all. */
  formatEntityState(entity: HassEntity, state?: string): string;
  formatEntityAttributevalue?: (entity: HassEntity, attribute: string) => string;
  localize(key: string, ...args: unknown[]): string;
}

/** The action config shared by every Home Assistant card. */
export interface ActionConfig {
  action:
    | "more-info"
    | "toggle"
    | "navigate"
    | "url"
    | "perform-action"
    | "call-service"
    | "assist"
    | "none";
  entity?: string;
  navigation_path?: string;
  url_path?: string;
  perform_action?: string;
  service?: string;
  data?: Record<string, unknown>;
  service_data?: Record<string, unknown>;
  target?: Record<string, unknown>;
  confirmation?: unknown;
}

export interface LovelaceCard extends HTMLElement {
  hass?: HomeAssistant;
  setConfig(config: Record<string, unknown>): void;
  getCardSize?(): number | Promise<number>;
}

export interface LovelaceCardEditor extends HTMLElement {
  hass?: HomeAssistant;
  setConfig(config: Record<string, unknown>): void;
}
