import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type JourneyIn = Schemas["JourneyIn"];
export type JourneyOut = Schemas["JourneyOut"];
export type JourneySummary = Schemas["JourneySummaryOut"];
export type ShareCreated = Schemas["ShareCreatedOut"];
export type SharedJourney = Schemas["SharedJourneyOut"];
export type JourneyPlace = Schemas["PlaceOut"];

const byId = (journeyId: string) => ({ params: { path: { journey_id: journeyId } } });

/** M6 calls. The library needs login; the two share calls do not. */
export const journeyApi = {
  list: async () => unwrap(await api.GET("/api/journeys")),
  get: async (journeyId: string) => unwrap(await api.GET("/api/journeys/{journey_id}", byId(journeyId))),
  /** 409 = the account already keeps the maximum number of journeys. */
  create: async (body: JourneyIn) => unwrap(await api.POST("/api/journeys", { body })),
  /** Overwrites the whole journey (title, date and the stops exactly as sent). */
  replace: async (journeyId: string, body: JourneyIn) =>
    unwrap(await api.PUT("/api/journeys/{journey_id}", { ...byId(journeyId), body })),
  remove: async (journeyId: string) => {
    unwrap(await api.DELETE("/api/journeys/{journey_id}", byId(journeyId)));
  },
  /** A read-only snapshot of the journey as sent (saved or not), valid for 7 days. 429 = too many links. */
  share: async (body: JourneyIn) =>
    unwrap(await api.POST("/api/journeys/shares", { body: { ...body, stops: body.stops ?? [] } })),
  /** 404 = wrong or expired code. */
  readShare: async (code: string) =>
    unwrap(await api.GET("/api/journeys/shares/{code}", { params: { path: { code } } })),
};
