"use client";

import { useQuery } from "@tanstack/react-query";

import { mapApi } from "../api";

/** Every place of the FoodMaps data (one cached request shared by the map, the list and the sidebar). */
export function usePlaces() {
  return useQuery({ queryKey: ["map", "places"], queryFn: mapApi.places, staleTime: 60_000 });
}
