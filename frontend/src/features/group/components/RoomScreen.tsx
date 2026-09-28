"use client";

import { loadParticipant } from "../lib/participantStore";
import { useRoomState } from "../hooks/useRoomState";

/**
 * Container. Reads the stored token; without one, shows the join form. Otherwise polls the room
 * and picks a view by status:
 *   lobby -> LobbyView | voting -> VoteDeckView (+ HostProgressView for the host)
 *   decided -> ResultView | expired -> "room expired" message.   TODO(M5)
 */
export function RoomScreen({ code }: { code: string }) {
  const me = loadParticipant(code);
  const { state } = useRoomState(code, me?.token ?? null);
  return (
    <main className="p-6">
      Phòng {code} — {state?.status ?? "TODO"}
    </main>
  );
}
