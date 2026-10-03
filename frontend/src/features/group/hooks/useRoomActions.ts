"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { type Criteria, groupApi, type Joined } from "../api";
import { saveParticipant } from "../lib/participantStore";
import { roomKey, type RoomView, withClockOffset } from "./useRoomState";

/** Store the token returned by create/join, so a reload keeps the user in the room. */
function remember(j: Joined) {
  saveParticipant(j.code, { participantId: j.participant_id, token: j.participant_token, isHost: j.is_host });
}

export function useCreateRoom() {
  return useMutation({ mutationFn: groupApi.createRoom, onSuccess: remember });
}

export function useJoinRoom(code: string) {
  return useMutation({
    mutationFn: (displayName: string) => groupApi.joinRoom(code, displayName),
    onSuccess: remember,
  });
}

/** start / vote / finalize. Every write returns the new state: put it in the cache right away. */
export function useRoomActions(code: string, token: string | null) {
  const qc = useQueryClient();
  const key = roomKey(code);
  const store = (s: Parameters<typeof withClockOffset>[0]) => qc.setQueryData(key, withClockOffset(s));

  const start = useMutation({
    mutationFn: (criteria: Criteria) => groupApi.start(code, token!, criteria),
    onSuccess: store,
  });

  const vote = useMutation({
    mutationFn: (v: { candidateId: string; liked: boolean }) =>
      groupApi.vote(code, token!, v.candidateId, v.liked),
    // Optimistic update: the card leaves the deck immediately, before the server answers
    onMutate: async (v) => {
      await qc.cancelQueries({ queryKey: key }); // an in-flight poll must not overwrite it
      const prev = qc.getQueryData<RoomView>(key);
      if (prev) {
        qc.setQueryData<RoomView>(key, {
          ...prev,
          candidates: prev.candidates.map((c) => (c.id === v.candidateId ? { ...c, my_vote: v.liked } : c)),
        });
      }
      return { prev };
    },
    onError: (_e, _v, ctx) => {
      if (ctx?.prev) qc.setQueryData(key, ctx.prev); // put the card back
      void qc.invalidateQueries({ queryKey: key }); // e.g. room decided meanwhile -> fetch it
    },
    onSuccess: store,
  });

  const finalize = useMutation({
    mutationFn: () => groupApi.finalize(code, token!),
    onSuccess: store,
  });

  return { start, vote, finalize };
}
