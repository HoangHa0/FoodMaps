/**
 * Google Maps links, shared by every feature (no API key, no API call: plain redirect links that open
 * the Maps app on phones). Replaces the copies in features/group, features/match and features/explore.
 * Docs: https://developers.google.com/maps/documentation/urls/get-started
 */

export interface MapsTarget {
  /** Google place id: when given, Google routes to the real place. */
  placeId?: string | null;
  /** The team's own name of the place. Required by the URL format together with `placeId`. */
  name?: string | null;
  lat?: number | null;
  lng?: number | null;
}

const FALLBACK_NAME = "Quán đã chọn";

/**
 * "Chỉ đường": directions to the place from the user's current location.
 * Prefers `placeId` (+ name), then coordinates, then the name. Returns "" when there is nothing to go to.
 */
export function directionsUrl(target: MapsTarget): string {
  const query = new URLSearchParams({ api: "1" });
  if (target.placeId) {
    query.set("destination", target.name || FALLBACK_NAME);
    query.set("destination_place_id", target.placeId);
  } else if (target.lat != null && target.lng != null) {
    query.set("destination", `${target.lat},${target.lng}`);
  } else if (target.name) {
    query.set("destination", target.name);
  } else {
    return "";
  }
  return `https://www.google.com/maps/dir/?${query}`;
}

/**
 * "Mở Google Maps": the place's own Google Maps link when the data has one (`places.google_maps_url`),
 * otherwise a search by place id / coordinates / name. Returns "" when there is nothing to open.
 */
export function openInMapsUrl(target: MapsTarget & { googleMapsUrl?: string | null }): string {
  if (target.googleMapsUrl) return target.googleMapsUrl;
  const query = new URLSearchParams({ api: "1" });
  if (target.lat != null && target.lng != null) query.set("query", `${target.lat},${target.lng}`);
  else if (target.name) query.set("query", target.name);
  else return "";
  if (target.placeId) query.set("query_place_id", target.placeId);
  return `https://www.google.com/maps/search/?${query}`;
}