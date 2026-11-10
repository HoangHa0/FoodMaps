import { categoryIcon, type MapPlace } from "@/features/map";

import { googleMapsLinks, legs, totalCost } from "./route";

export interface StopInput {
  key: string;
  place_id: string;
  planned_time: string;
  note: string;
}

/** A stop ready to show: its place (null when the place left the data), time and note. */
export interface StopView {
  key: string;
  place: MapPlace | null;
  icon: string;
  planned_time: string;
  note: string;
  /** distance to the NEXT located stop, metres (undefined for the last one) */
  legToNext?: number;
  /** this stop's time is earlier than the time of an earlier stop */
  timeOutOfOrder: boolean;
}

/**
 * Joins the stops with their places and computes what the planner shows: the distance between
 * consecutive stops, time-order warnings, total distance and cost, Google Maps links. Pure.
 */
export function buildStopViews(stops: readonly StopInput[], places: readonly MapPlace[]) {
  const byId = new Map(places.map((p) => [p.place_id, p]));
  const resolved = stops.map((s) => ({ s, place: byId.get(s.place_id) ?? null }));
  const located = resolved.flatMap((r) => (r.place ? [{ s: r.s, place: r.place }] : []));
  const legMetres = legs(located.map((r) => r.place));
  const legByKey = new Map(legMetres.map((m, i) => [located[i].s.key, m]));

  // latest time seen so far, for each position: a stop earlier than it is out of order
  const latestBefore = resolved.map((_, i) =>
    resolved.slice(0, i).reduce((latest, r) => (r.s.planned_time > latest ? r.s.planned_time : latest), ""),
  );

  const views: StopView[] = resolved.map(({ s, place }, i) => ({
    key: s.key,
    place,
    icon: place ? categoryIcon(place.category) : "❔",
    planned_time: s.planned_time,
    note: s.note,
    legToNext: legByKey.get(s.key),
    timeOutOfOrder: !!s.planned_time && !!latestBefore[i] && s.planned_time < latestBefore[i],
  }));

  return {
    views,
    mapPlaces: located.map((r) => r.place),
    totalDistance: legMetres.reduce((a, b) => a + b, 0),
    cost: totalCost(located.map((r) => r.place.price_per_person)),
    links: googleMapsLinks(located.map((r) => r.place)),
  };
}
