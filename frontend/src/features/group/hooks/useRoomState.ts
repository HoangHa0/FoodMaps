"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { ApiError } from "@/lib/api/errors";

import { groupApi, type RoomState } from "../api";
import { clearParticipant } from "../lib/participantStore";

/** Server state + how far the server clock is ahead of this device (for the countdown). */
export type RoomView = RoomState & { clockOffsetMs: number };

export const roomKey = (code: string) => ["group", code] as const;

/** Attach the clock offset. Call it on EVERY server response that goes into the cache. */
export function withClockOffset(s: RoomState): RoomView {
  return { ...s, clockOffsetMs: Date.parse(s.server_time) - Date.now() };
}

/**
 * Polls the room state. ALL real-time logic lives in this hook; views only receive props,
 * so switching to SSE later means changing this file only.
 *   - interval = state.poll_interval_ms (server-controlled); stops once decided/expired
 *   - sends since_version; on changed=false keeps the SAME object -> no re-render
 *   - TanStack Query pauses polling while the tab is hidden (refetchIntervalInBackground=false)
 */
export function useRoomState(code: string, token: string | null) {
  const qc = useQueryClient();
  const key = roomKey(code);
  const query = useQuery({
    queryKey: key,
    enabled: !!token,
    queryFn: async (): Promise<RoomView> => {
      const prev = qc.getQueryData<RoomView>(key);
      try {
        const next = await groupApi.getState(code, token!, prev?.version);
        if (prev && (!next.changed || next.version < prev.version)) return prev; // nothing new / stale
        return withClockOffset(next);
      } catch (e) {
        // Token unknown to the server (e.g. database reset): forget it -> the join form shows again
        if (e instanceof ApiError && e.status === 401) clearParticipant(code);
        throw e;
      }
    },
    refetchInterval: (q) => {
      const s = q.state.data;
      if (s && (s.status === "decided" || s.status === "expired")) return false; // stop polling
      if (q.state.error) return false; // 401/404: polling again will not help
      return s?.poll_interval_ms ?? 3000;
    },
    retry: (count, e) => !(e instanceof ApiError && e.status < 500) && count < 2,
  });
  return { state: query.data, isLoading: query.isPending && !!token, error: query.error };
}
