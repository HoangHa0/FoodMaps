import { api, type Schemas } from "@/lib/api/client";

export type RoomState = Schemas["RoomStateOut"];
export type Joined = Schemas["JoinedOut"];

/** Room-member authentication header, sent on EVERY request after joining. */
export const participantHeaders = (token: string) => ({ "X-Participant-Token": token });

/**
 * TODO(M5): createRoom, joinRoom, getState(code, token, sinceVersion), start, vote, finalize.
 * Pattern:
 *   unwrap(await api.GET("/api/groups/{code}", {
 *     params: { path: { code }, query: { since_version }, header: participantHeaders(token) },
 *   }))
 */
export const groupApi = { _client: api };
