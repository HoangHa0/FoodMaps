import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type RoomState = Schemas["RoomStateOut"];
export type Joined = Schemas["JoinedOut"];
export type Candidate = Schemas["CandidateOut"];
export type Participant = Schemas["ParticipantOut"];
export type Criteria = Schemas["MatchCriteria"];

/** Room-member authentication header, sent on EVERY request after joining. */
export const participantHeaders = (token: string) => ({ "X-Participant-Token": token });

/** All M5 calls. Each one returns data or throws ApiError (status + code + Vietnamese message). */
export const groupApi = {
  createRoom: async (displayName: string) =>
    unwrap(await api.POST("/api/groups", { body: { display_name: displayName } })),

  joinRoom: async (code: string, displayName: string) =>
    unwrap(
      await api.POST("/api/groups/{code}/join", {
        params: { path: { code } },
        body: { display_name: displayName },
      }),
    ),

  getState: async (code: string, token: string, sinceVersion?: number) =>
    unwrap(
      await api.GET("/api/groups/{code}", {
        params: {
          path: { code },
          query: { since_version: sinceVersion },
          header: participantHeaders(token),
        },
      }),
    ),

  start: async (code: string, token: string, criteria: Criteria) =>
    unwrap(
      await api.POST("/api/groups/{code}/start", {
        params: { path: { code }, header: participantHeaders(token) },
        body: { criteria },
      }),
    ),

  vote: async (code: string, token: string, candidateId: string, liked: boolean) =>
    unwrap(
      await api.POST("/api/groups/{code}/votes", {
        params: { path: { code }, header: participantHeaders(token) },
        body: { candidate_id: candidateId, liked },
      }),
    ),

  finalize: async (code: string, token: string) =>
    unwrap(
      await api.POST("/api/groups/{code}/finalize", {
        params: { path: { code }, header: participantHeaders(token) },
      }),
    ),
};
