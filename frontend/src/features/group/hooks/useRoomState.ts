"use client";

import type { RoomState } from "../api";

/**
 * Polls the room state. ALL real-time logic lives in this hook; views only receive props,
 * so switching to SSE later means changing this file only.
 * TODO(M5):
 *   - useQuery with refetchInterval = state.poll_interval_ms; stop once decided/expired
 *   - send since_version; when the response has changed=false, keep the previous data
 *   - TanStack Query pauses polling while the tab is hidden (refetchIntervalInBackground=false)
 */
export function useRoomState(_code: string, _token: string | null): {
  state: RoomState | undefined;
  isLoading: boolean;
  error: unknown;
} {
  return { state: undefined, isLoading: false, error: null };
}
