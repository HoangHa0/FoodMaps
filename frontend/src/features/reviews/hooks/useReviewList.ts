"use client";

import { useQuery } from "@tanstack/react-query";

import { useMe } from "@/features/auth";

import { reviewsApi } from "../api";
import { reviewKeys } from "./useMyReview";

/** How many reviews the sidebar loads. The newest come first; the API allows up to 50. */
export const REVIEW_PAGE_SIZE = 20;

/**
 * Reviews written on the website for one place (newest first, guests allowed).
 * The key starts with reviewKeys.place(placeId), so saving or deleting a review (useReviewMutations)
 * refreshes this list. The login state is part of the key because `is_mine` depends on it.
 */
export function useReviewList(placeId: string) {
  const { data: me } = useMe();
  return useQuery({
    queryKey: [...reviewKeys.place(placeId), "list", !!me],
    queryFn: () => reviewsApi.list(placeId, REVIEW_PAGE_SIZE),
  });
}