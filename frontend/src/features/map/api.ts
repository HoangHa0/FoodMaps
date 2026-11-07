import { api, type Schemas } from "@/lib/api/client";
import { unwrap } from "@/lib/api/errors";

export type MapPlace = Schemas["MapPlace"];

export const mapApi = {
  places: async (): Promise<MapPlace[]> => unwrap(await api.GET("/api/match/places")),
};
