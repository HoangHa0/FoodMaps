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
 * While the list of the SAME place reloads (e.g. right after logging in) the previous one stays on screen, so the
 * rows are not unmounted: a "Báo cáo" pressed as a guest can open its dialog after the login.
 */
export function useReviewList(placeId: string) {
  const { data: me } = useMe();
  return useQuery({
    queryKey: [...reviewKeys.place(placeId), "list", !!me],
    queryFn: () => reviewsApi.list(placeId, REVIEW_PAGE_SIZE),
    // same place only: another place must never show this one's reviews while it loads
    placeholderData: (previous, previousQuery) => (previousQuery?.queryKey[2] === placeId ? previous : undefined),
  });
}