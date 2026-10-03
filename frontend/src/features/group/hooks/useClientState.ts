"use client";

import { useMemo, useSyncExternalStore } from "react";

import { parseParticipant, readParticipantRaw, subscribeParticipant } from "../lib/participantStore";

/**
 * The stored participant for this room, or null. Read through useSyncExternalStore instead of
 * reading localStorage during render: the server render has no localStorage, so reading it
 * directly would cause a hydration mismatch.
 */
export function useStoredParticipant(code: string) {
  const raw = useSyncExternalStore(
    subscribeParticipant,
    () => readParticipantRaw(code),
    () => null, // server snapshot
  );
  // `ready` = false only during the server render / first hydration pass
  const ready = useSyncExternalStore(
    noopSubscribe,
    () => true,
    () => false,
  );
  return { participant: useMemo(() => parseParticipant(raw), [raw]), ready };
}

const noopSubscribe = () => () => {};

/** Seconds left until `expiresAt`, measured on the SERVER clock (wrong device clocks still agree). */
export function useSecondsLeft(expiresAt: string | undefined, clockOffsetMs: number | undefined) {
  const nowSec = useSyncExternalStore(subscribeEverySecond, currentSecond, () => 0);
  if (!expiresAt || clockOffsetMs === undefined || nowSec === 0) return null;
  const serverNowMs = nowSec * 1000 + clockOffsetMs;
  return Math.max(0, Math.round((Date.parse(expiresAt) - serverNowMs) / 1000));
}

const currentSecond = () => Math.floor(Date.now() / 1000);
function subscribeEverySecond(onTick: () => void) {
  const id = window.setInterval(onTick, 1000);
  return () => window.clearInterval(id);
}
