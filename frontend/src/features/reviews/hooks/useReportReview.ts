"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { type ReportReason, reviewsApi } from "../api";
import { reviewKeys } from "./useMyReview";

/**
 * Reports one review. Afterwards the place's review list is refreshed: the third different reporter
 * flags the review and the API stops listing it.
 */
export function useReportReview(placeId: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ reviewId, reason, note }: { reviewId: string; reason: ReportReason; note: string | null }) =>
      reviewsApi.report(reviewId, reason, note),
    onSettled: () => qc.invalidateQueries({ queryKey: reviewKeys.place(placeId) }),
  });
}
