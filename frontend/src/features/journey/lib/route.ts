/**
 * Distances, walking estimates, cost and Google Maps links of a journey. Pure functions.
 * Distances are straight lines ("đường chim bay"): the walking time adds a detour factor and is
 * always shown as an estimate.
 */

export interface RoutePoint {
  lat: number;
  lng: number;
}

const EARTH_RADIUS_M = 6_371_000;
const WALK_M_PER_MIN = 75; // ~4.5 km/h
const DETOUR = 1.3; // streets are longer than the straight line

export function straightLineM(a: RoutePoint, b: RoutePoint): number {
  const rad = (d: number) => (d * Math.PI) / 180;
  const h =
    Math.sin(rad(b.lat - a.lat) / 2) ** 2 +
    Math.cos(rad(a.lat)) * Math.cos(rad(b.lat)) * Math.sin(rad(b.lng - a.lng) / 2) ** 2;
  return 2 * EARTH_RADIUS_M * Math.asin(Math.sqrt(h));
}

/** Distance from each stop to the next one (n - 1 values). */
export function legs(points: RoutePoint[]): number[] {
  return points.slice(1).map((p, i) => straightLineM(points[i], p));
}

export const walkingMinutes = (metres: number) => Math.max(1, Math.round((metres * DETOUR) / WALK_M_PER_MIN));

export function formatDistance(m: number): string {
  const rounded = Math.round(m / 10) * 10; // 995 m would read "1000 m": switch to km from 1000
  return rounded < 1000 ? `${rounded} m` : `${(m / 1000).toFixed(1).replace(".", ",")} km`;
}

export function formatMinutes(min: number): string {
  if (min < 60) return `${min} phút`;
  const h = Math.floor(min / 60);
  const rest = min % 60;
  return rest ? `${h} giờ ${rest} phút` : `${h} giờ`;
}

/** Sum of the known prices per person, and how many stops have no price. */
export function totalCost(prices: (number | null)[]): { total: number; unknown: number } {
  return prices.reduce<{ total: number; unknown: number }>(
    (acc, p) => (p === null ? { ...acc, unknown: acc.unknown + 1 } : { ...acc, total: acc.total + p }),
    { total: 0, unknown: 0 },
  );
}

/** Google Maps takes an origin, a destination and up to 9 waypoints: 11 points per link. */
const POINTS_PER_LINK = 11;

/**
 * Walking directions through every stop, in order. Longer journeys are split into legs that share
 * their end points (stop 11 ends link 1 and starts link 2), so nothing is skipped.
 */
export function googleMapsLinks(points: RoutePoint[]): string[] {
  if (points.length < 2) return [];
  const coord = (p: RoutePoint) => `${p.lat},${p.lng}`;
  const links: string[] = [];
  for (let start = 0; start < points.length - 1; start += POINTS_PER_LINK - 1) {
    const chunk = points.slice(start, start + POINTS_PER_LINK);
    const q = new URLSearchParams({
      api: "1",
      origin: coord(chunk[0]),
      destination: coord(chunk[chunk.length - 1]),
      travelmode: "walking",
    });
    if (chunk.length > 2) q.set("waypoints", chunk.slice(1, -1).map(coord).join("|"));
    links.push(`https://www.google.com/maps/dir/?${q.toString()}`);
  }
  return links;
}

/** "14:30:00" (API) or "14:30" -> "14:30"; anything else -> "". */
export const hhmm = (t: string | null | undefined) => (t && /^\d{2}:\d{2}/.test(t) ? t.slice(0, 5) : "");
