"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { useMe } from "@/features/auth";
import { ApiError } from "@/lib/api/errors";

import { type JourneyIn, journeyApi } from "../api";

export const journeyKeys = {
  all: ["journeys"] as const,
  list: (user: string | null) => ["journeys", "list", user] as const,
  shared: (code: string) => ["journeys", "shared", code] as const,
};

/** The logged-in user's library (guests: never requested). */
export function useJourneyLibrary() {
  const { data: me } = useMe();
  return useQuery({
    queryKey: journeyKeys.list(me?.username ?? null),
    queryFn: journeyApi.list,
    enabled: !!me,
  });
}

/** Create (no id yet) or overwrite (id) a journey; refreshes the library. */
export function useSaveJourney() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ journeyId, body }: { journeyId: string | null; body: JourneyIn }) =>
      journeyId ? journeyApi.replace(journeyId, body) : journeyApi.create(body),
    onSettled: () => qc.invalidateQueries({ queryKey: journeyKeys.all }),
  });
}

/** Open one saved journey (fetched on demand, when the user picks it in the library). */
export function useOpenJourney() {
  return useMutation({ mutationFn: (journeyId: string) => journeyApi.get(journeyId) });
}

export function useDeleteJourney() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (journeyId: string) => journeyApi.remove(journeyId),
    onSettled: () => qc.invalidateQueries({ queryKey: journeyKeys.all }),
  });
}

export function useShareJourney() {
  return useMutation({ mutationFn: (body: JourneyIn) => journeyApi.share(body) });
}

/** A shared journey by its code. 404 (wrong or expired link) is an answer, not retried. */
export function useSharedJourney(code: string) {
  return useQuery({
    queryKey: journeyKeys.shared(code),
    queryFn: () => journeyApi.readShare(code),
    retry: (count, e) => !(e instanceof ApiError && e.status === 404) && count < 1,
  });
}
