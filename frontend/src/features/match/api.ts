import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type MatchCriteria = Schemas["MatchCriteria"];
export type MatchResult = Schemas["MatchResult"];
export type MatchResponse = Schemas["MatchResponse"];
export type RejectReason = Schemas["RejectReason"];
export type WhyOut = Schemas["WhyOut"];
export type InsightsOut = Schemas["InsightsOut"];

/** M3 API calls (guests allowed). Hooks and components never call `api.*` directly. */
export const matchApi = {
  /** One best place + up to 3 backups. */
  match: async (criteria: MatchCriteria) => unwrap(await api.POST("/api/match", { body: criteria })),

  /** "Không hợp": reorder the backups the client still holds (the server keeps no state). */
  reject: async (body: Schemas["RejectIn"]) => unwrap(await api.POST("/api/match/reject", { body })),

  /** "Why this place?": 3-4 bullets picked by similarity to the mood (no LLM at request time). */
  why: async (placeId: string, mood: string) =>
    unwrap(
      await api.GET("/api/match/{place_id}/why", {
        params: { path: { place_id: placeId }, query: { mood } },
      }),
    ),

  /**
   * AI summary, pros/cons, answers to the preset questions and most mentioned dishes of one place,
   * written offline (no LLM at request time). 404 = no insights for this place yet.
   */
  insights: async (placeId: string) =>
    unwrap(await api.GET("/api/match/{place_id}/insights", { params: { path: { place_id: placeId } } })),
};
