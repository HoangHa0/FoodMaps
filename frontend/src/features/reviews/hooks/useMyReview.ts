"use client";

import { useQuery } from "@tanstack/react-query";

import { useMe } from "@/features/auth";

import { reviewsApi } from "../api";

/** Query keys of M4, so every mutation (and later the analysis panel) refreshes the right data. */
export const reviewKeys = {
  mine: (placeId: string) => ["reviews", "mine", placeId] as const,
  place: (placeId: string) => ["reviews", "place", placeId] as const,
};

/**
 * The logged-in user's own review of a place, used to pre-fill the form.
 * data = null: not reviewed yet. A guest never calls the API (it would answer 401).
 */
export function useMyReview(placeId: string) {
  const { data: me } = useMe();
  return useQuery({
    queryKey: reviewKeys.mine(placeId),
    queryFn: () => reviewsApi.mine(placeId),
    enabled: !!me,
  });
}
