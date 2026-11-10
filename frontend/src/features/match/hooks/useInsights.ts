"use client";

import { useQuery } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/errors";

import { matchApi } from "../api";

/** Insights of one place. A 404 (no insights yet) is an answer, not a failure: it is not retried. */
export function useInsights(placeId: string) {
  return useQuery({
    queryKey: ["match", "insights", placeId],
    queryFn: () => matchApi.insights(placeId),
    staleTime: 10 * 60_000, // written by an offline job: they change rarely
    retry: (count, e) => !(e instanceof ApiError && e.status === 404) && count < 1,
  });
}
