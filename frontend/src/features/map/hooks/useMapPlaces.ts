"use client";

import { useQuery } from "@tanstack/react-query";

import { mapApi } from "../api";

/** Query keys of the map feature, so a later mutation can refresh the right data. */
export const mapKeys = {
  places: ["map", "places"] as const,
};

/** The places table changes only when the team re-imports data, so a long cache is safe. */
const PLACES_STALE_MS = 30 * 60_000;
const PLACES_GC_MS = 60 * 60_000;

/**
 * Every place for the home map, loaded once and cached. Going to /me or /journey and back does not
 * call the API again within 30 minutes. The endpoint is public, so guests see the map too: this hook
 * deliberately does not wait for login (unlike useMyReview) and the key has no user in it.
 */
export function useMapPlaces() {
  return useQuery({
    queryKey: mapKeys.places,
    queryFn: mapApi.places,
    staleTime: PLACES_STALE_MS,
    gcTime: PLACES_GC_MS,
  });
}