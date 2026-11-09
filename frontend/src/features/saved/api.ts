import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type SavedPlace = Schemas["SavedPlaceOut"];

/** M2 saved places (login required). Hooks and components never call `api.*` directly. */
export const savedApi = {
  list: async () => unwrap(await api.GET("/api/saved-places")),
  /** Saves into the default list ("Yêu thích"). */
  save: async (placeId: string) => unwrap(await api.POST("/api/saved-places", { body: { place_id: placeId } })),
  remove: async (savedId: string) =>
    unwrap(await api.DELETE("/api/saved-places/{saved_id}", { params: { path: { saved_id: savedId } } })),
};
