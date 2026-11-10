import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type SavedList = Schemas["SavedListOut"];
export type SavedPlace = Schemas["SavedPlaceOut"];

/** M2 saved places API calls (login required). Hooks and components never call `api.*` directly. */
export const savedApi = {
  lists: async () => unwrap(await api.GET("/api/saved-places/lists")),
  createList: async (body: Schemas["SavedListIn"]) =>
    unwrap(await api.POST("/api/saved-places/lists", { body })),
  updateList: async (listId: string, body: Schemas["SavedListUpdateIn"]) =>
    unwrap(
      await api.PATCH("/api/saved-places/lists/{list_id}", {
        params: { path: { list_id: listId } },
        body,
      }),
    ),
  deleteList: async (listId: string) => {
    unwrap(
      await api.DELETE("/api/saved-places/lists/{list_id}", { params: { path: { list_id: listId } } }),
    );
  },

  saved: async () => unwrap(await api.GET("/api/saved-places")),
  /** Save, or move / re-note when the place is already saved. */
  save: async (body: Schemas["SavedPlaceIn"]) => unwrap(await api.POST("/api/saved-places", { body })),
  updateSaved: async (savedId: string, body: Schemas["SavedPlaceUpdateIn"]) =>
    unwrap(
      await api.PATCH("/api/saved-places/{saved_id}", {
        params: { path: { saved_id: savedId } },
        body,
      }),
    ),
  removeSaved: async (savedId: string) => {
    unwrap(
      await api.DELETE("/api/saved-places/{saved_id}", { params: { path: { saved_id: savedId } } }),
    );
  },
};