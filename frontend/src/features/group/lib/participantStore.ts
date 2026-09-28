/**
 * Persists the participant token per room code in localStorage, so a page reload or a reopened
 * tab stays in the room. Key: `fm.group.<CODE>` -> JSON {participantId, token, isHost}.
 * TODO(M5): implement; wrap storage access in try/catch (it can throw in private browsing).
 */
export interface StoredParticipant {
  participantId: string;
  token: string;
  isHost: boolean;
}

export function loadParticipant(_code: string): StoredParticipant | null {
  return null;
}

export function saveParticipant(_code: string, _p: StoredParticipant): void {}
