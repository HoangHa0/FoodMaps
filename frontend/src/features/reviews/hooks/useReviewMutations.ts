"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/errors";

import { type Review, type ReviewBody, reviewsApi } from "../api";
import { reviewKeys } from "./useMyReview";

/**
 * Save = create the first time, edit afterwards. `existing` is the user's review from useMyReview.
 * If the server says 409 review_exists (the user reviewed on another tab/device), look the old
 * review up and edit it instead, so the user never sees that error.
 */
export function useSaveReview(placeId: string, existing: Review | null | undefined) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (body: ReviewBody): Promise<Review> => {
      if (existing) return reviewsApi.update(existing.id, body);
      try {
        return await reviewsApi.create({ ...body, place_id: placeId });
      } catch (e) {
        if (e instanceof ApiError && e.code === "review_exists") {
          const mine = await reviewsApi.mine(placeId);
          if (mine) return reviewsApi.update(mine.id, body);
        }
        throw e;
      }
    },
    onSuccess: (review) => {
      qc.setQueryData(reviewKeys.mine(placeId), review);
      void qc.invalidateQueries({ queryKey: reviewKeys.place(placeId) });
    },
  });
}

export function useDeleteReview(placeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: reviewsApi.remove,
    onSuccess: () => {
      qc.setQueryData(reviewKeys.mine(placeId), null);
      void qc.invalidateQueries({ queryKey: reviewKeys.place(placeId) });
    },
  });
}
