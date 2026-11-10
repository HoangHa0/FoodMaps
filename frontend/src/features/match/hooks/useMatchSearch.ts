"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import type { Origin } from "@/features/places";

import { type MatchCriteria, type MatchResult, matchApi, type RejectReason } from "../api";

/** One search and what is left of it: the place on screen + the backups the client still holds. */
export interface MatchSession {
  criteria: MatchCriteria;
  /** The starting point as the user picked it (with its name); `criteria.origin` holds only its coordinates. */
  origin: Origin | null;
  best: MatchResult | null;
  backups: MatchResult[];
  /** The reason of the "Không hợp" that left nothing (undefined: ran out of backups, or a place is shown). */
  emptyAfter?: RejectReason;
}

/**
 * All AI Match state of the app. The server keeps no state between calls (DECISIONS D12), so the
 * backups live here and are sent back on "Không hợp".
 */
export function useMatchSearch() {
  const [session, setSession] = useState<MatchSession | null>(null);

  const search = useMutation({
    mutationFn: async ({ criteria, origin }: { criteria: MatchCriteria; origin: Origin | null }): Promise<MatchSession> => {
      const r = await matchApi.match(criteria);
      return { criteria, origin, best: r.best, backups: r.backups ?? [] };
    },
    onSuccess: setSession,
  });

  const reject = useMutation({
    mutationFn: async ({ current, reason }: { current: MatchSession; reason: RejectReason }) => {
      if (!current.best || current.backups.length === 0) return { best: null, backups: [], emptyAfter: undefined }; // ran out
      const r = await matchApi.reject({
        criteria: current.criteria,
        reason,
        rejected_place_id: current.best.place_id,
        remaining: current.backups.map((b) => b.place_id),
      });
      return { best: r.best, backups: r.backups ?? [], emptyAfter: r.best ? undefined : reason };
    },
    onSuccess: (r) => setSession((s) => (s ? { ...s, ...r } : s)),
  });

  const rejectCurrent = useCallback(
    (reason: RejectReason) => {
      if (session) reject.mutate({ current: session, reason });
    },
    [reject, session],
  );

  const close = useCallback(() => {
    setSession(null);
    search.reset();
    reject.reset();
  }, [search, reject]);

  return { session, search, reject, rejectCurrent, close };
}

/** "Why this place?" for the place on screen. Errors (e.g. AI not configured) just hide the box. */
export function useWhy(placeId: string | undefined, mood: string | undefined) {
  return useQuery({
    queryKey: ["match", "why", placeId, mood],
    queryFn: () => matchApi.why(placeId!, mood!),
    enabled: !!placeId && !!mood,
    staleTime: Infinity, // the bullets only change when the offline job runs again
    retry: false,
  });
}
