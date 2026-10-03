/**
 * Persists the participant token per room code in localStorage, so a page reload or a reopened
 * tab stays in the room. Key: `fm.group.<CODE>` -> JSON {participantId, token, isHost}.
 * Every storage access is wrapped in try/catch: it can throw in private browsing or when blocked.
 */
export interface StoredParticipant {
  participantId: string;
  token: string;
  isHost: boolean;
}

const key = (code: string) => `fm.group.${code.toUpperCase()}`;
// "storage" only fires in OTHER tabs; this event tells components in THIS tab to re-read.
const CHANGE_EVENT = "fm-group-participant";

/** Raw JSON string (or null). Strings compare by value, so useSyncExternalStore stays stable. */
export function readParticipantRaw(code: string): string | null {
  try {
    return window.localStorage.getItem(key(code));
  } catch {
    return null;
  }
}

export function parseParticipant(raw: string | null): StoredParticipant | null {
  if (!raw) return null;
  try {
    const p = JSON.parse(raw) as Partial<StoredParticipant>;
    return typeof p.token === "string" && typeof p.participantId === "string"
      ? { participantId: p.participantId, token: p.token, isHost: !!p.isHost }
      : null;
  } catch {
    return null; // corrupted value: behave as "not joined yet"
  }
}

export function loadParticipant(code: string): StoredParticipant | null {
  return parseParticipant(readParticipantRaw(code));
}

export function saveParticipant(code: string, p: StoredParticipant): void {
  try {
    window.localStorage.setItem(key(code), JSON.stringify(p));
  } catch {
    // Storage unavailable: the user stays in the room until the tab is reloaded
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function clearParticipant(code: string): void {
  try {
    window.localStorage.removeItem(key(code));
  } catch {
    // ignore
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

/** For useSyncExternalStore: re-read when this tab or another tab changes the stored token. */
export function subscribeParticipant(onChange: () => void): () => void {
  window.addEventListener(CHANGE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(CHANGE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}
