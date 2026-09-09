/**
 * Small helpers that talk to Home Assistant.
 *
 * The card deliberately depends on almost nothing of the frontend: three of
 * its elements (`ha-card`, `ha-icon`, `ha-alert`), its CSS variables and its
 * events. Everything else it draws itself. A custom card that reaches deeper
 * breaks on a frontend release that renamed an internal component, and a
 * dashboard card is the worst possible place to find that out.
 */

import type { ActionConfig, HassEntity, HomeAssistant } from "../types/ha";

export const UNAVAILABLE = "unavailable";
export const UNKNOWN = "unknown";

/**
 * Return whether a state carries no usable value.
 *
 * Both of the two reasons: the entity is gone, or it has never been given one.
 * For *showing* a value the two are the same - there is nothing to show.
 */
export function hasNoValue(state: string | undefined): boolean {
  return state === undefined || state === UNAVAILABLE || state === UNKNOWN;
}

/**
 * Return whether the entity behind a state is not there at all.
 *
 * The distinction {@link hasNoValue} does not make, and the one that decides
 * whether a control may be used: `unknown` on an editor entity means the mode
 * has no value for this parameter yet, which is exactly what the control is
 * there to change. Disabling it was the one bug that made the editor useless
 * for a preset nobody had filled in yet - which is every new preset.
 */
export function isMissing(state: string | undefined): boolean {
  return state === undefined || state === UNAVAILABLE;
}

export function stateOf(
  hass: HomeAssistant | undefined,
  entityId: string | null | undefined,
): HassEntity | undefined {
  if (!hass || !entityId) return undefined;
  return hass.states[entityId];
}

export function fireEvent<T>(
  node: EventTarget,
  type: string,
  detail?: T,
): void {
  node.dispatchEvent(
    new CustomEvent(type, { detail, bubbles: true, composed: true }),
  );
}

/**
 * Format a state the way the rest of Home Assistant does.
 *
 * `formatEntityState` applies the unit, the display precision, the device
 * class and the user's own locale - the same call every core card makes, so a
 * temperature reads the same here as it does in a tile card. The fallback is
 * for an older frontend, not for a broken one.
 */
export function formatState(hass: HomeAssistant, entity: HassEntity): string {
  if (typeof hass.formatEntityState === "function") {
    return hass.formatEntityState(entity);
  }
  const unit = entity.attributes.unit_of_measurement;
  return unit ? `${entity.state} ${unit}` : entity.state;
}

/** The name of an entity without the device name Home Assistant prefixes. */
export function friendlyName(entity: HassEntity | undefined): string {
  return entity?.attributes.friendly_name ?? entity?.entity_id ?? "";
}

export function navigate(path: string): void {
  history.pushState(null, "", path);
  fireEvent(window, "location-changed", { replace: false });
}

export function showMoreInfo(node: EventTarget, entityId: string): void {
  fireEvent(node, "hass-more-info", { entityId });
}

export function hasAction(config: ActionConfig | undefined): boolean {
  return config !== undefined && config.action !== "none";
}

/**
 * Carry out one of the configured actions.
 *
 * Implemented here rather than delegated: the frontend's own `handleAction` is
 * an internal module with no stable way in from a custom card.
 */
export async function performAction(
  node: EventTarget,
  hass: HomeAssistant,
  action: ActionConfig | undefined,
  defaultEntityId: string | undefined,
): Promise<void> {
  if (!action || action.action === "none") return;
  const entityId = action.entity ?? defaultEntityId;

  switch (action.action) {
    case "more-info":
      if (entityId) showMoreInfo(node, entityId);
      return;
    case "toggle":
      if (entityId) {
        await hass.callService("homeassistant", "toggle", {}, { entity_id: entityId });
      }
      return;
    case "navigate":
      if (action.navigation_path) navigate(action.navigation_path);
      return;
    case "url":
      if (action.url_path) window.open(action.url_path, "_blank", "noreferrer");
      return;
    case "perform-action":
    case "call-service": {
      const name = action.perform_action ?? action.service;
      if (!name || !name.includes(".")) return;
      const [domain, service] = name.split(".", 2);
      await hass.callService(
        domain,
        service,
        action.data ?? action.service_data ?? {},
        action.target,
      );
      return;
    }
    default:
      return;
  }
}

/** Whether a Home Assistant element is loaded, so a fallback can be drawn. */
export function isDefined(tag: string): boolean {
  return typeof customElements !== "undefined" && !!customElements.get(tag);
}
