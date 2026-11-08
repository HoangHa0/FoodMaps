import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type GeoSuggestion = Schemas["GeoSuggestionOut"];
export type GeoPoint = Schemas["GeoPoint"];

/** Address search (backend `geo` module, guests allowed). Hooks and components never call `api.*` directly. */
export const geoApi = {
  /** Up to 10 suggestions for the text typed so far (the server returns [] below 2 characters). */
  suggest: async (q: string, signal?: AbortSignal) =>
    unwrap(await api.GET("/api/geo/suggest", { params: { query: { q } }, signal })),

  /** Coordinates of the suggestion the user picked. Call it only on selection. */
  resolve: async (refId: string) =>
    unwrap(await api.GET("/api/geo/resolve", { params: { query: { ref_id: refId } } })),
};
