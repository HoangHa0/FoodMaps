import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type Review = Schemas["ReviewOut"];
/** What the form sends: the 4 scores, comment and optional tags/price (same for POST and PUT). */
export type ReviewBody = Schemas["ReviewUpdateIn"];

/** M4 API calls. Hooks and components never call `api.*` directly. */
export const reviewsApi = {
  /** The caller's own review of a place (any status). null = not reviewed yet (404). */
  mine: async (placeId: string) => {
    const res = await api.GET("/api/reviews/mine", { params: { query: { place_id: placeId } } });
    if (res.response.status === 404) return null;
    return unwrap(res);
  },
  create: async (body: Schemas["ReviewIn"]) => unwrap(await api.POST("/api/reviews", { body })),
  update: async (reviewId: string, body: ReviewBody) =>
    unwrap(await api.PUT("/api/reviews/{review_id}", { params: { path: { review_id: reviewId } }, body })),
  remove: async (reviewId: string) => {
    unwrap(await api.DELETE("/api/reviews/{review_id}", { params: { path: { review_id: reviewId } } }));
  },
};
