"use client";

import { useEffect, useRef } from "react";

import {
  createPlacesLayer,
  type MapPin,
  type PlacesLayerController,
  type PlacesLayerOptions,
  type PlacesMap,
} from "../lib/placesLayer";

interface Params {
  /** The map instance once it exists (null before). Keep it in state, not only in a ref. */
  map: PlacesMap | null;
  places: readonly MapPin[];
  selectedId: string | null;
  savedIds?: ReadonlySet<string>;
  options: PlacesLayerOptions;
}

const NO_SAVED: ReadonlySet<string> = new Set();

/**
 * Keeps the places symbol layer in sync with React state.
 *
 * - Creates the layer when the map is ready and removes its listeners on unmount.
 * - Pushes new data when places / selection / saved set change.
 * - Flies to the place when `selectedId` changes (picked from a list or the preview), not on first render.
 *
 * `options` must be stable (module constant or useMemo): the layer is rebuilt when it changes.
 */
export function usePlacesLayer({ map, places, selectedId, savedIds = NO_SAVED, options }: Params): void {
  const controller = useRef<PlacesLayerController | null>(null);
  const lastFlownTo = useRef<string | null>(null);

  useEffect(() => {
    if (!map) return;
    const created = createPlacesLayer(map, options);
    controller.current = created;
    return () => {
      created.destroy();
      controller.current = null;
    };
  }, [map, options]);

  useEffect(() => {
    controller.current?.setData(places, selectedId, savedIds);
  }, [map, options, places, selectedId, savedIds]);

  useEffect(() => {
    if (!selectedId || selectedId === lastFlownTo.current) return;
    lastFlownTo.current = selectedId;
    controller.current?.flyTo(selectedId);
  }, [map, options, selectedId]);
}

/**
 * Reads a CSS design token (e.g. "--color-fg") and converts it into a map-compatible colour string,
 * so canvas drawing and map paint follow the theme without hard-coded colours. The value is resolved
 * through a 1px canvas because the token may use a syntax the map's colour parser does not support.
 * Returns "" on the server or when the token does not exist.
 */
export function readToken(name: string): string { // design-ok: convert CSS design token to map-compatible rgba
  if (typeof window === "undefined") return "";
  const raw = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  if (!raw) return "";
  const ctx = document.createElement("canvas").getContext("2d", { willReadFrequently: true });
  if (!ctx) return raw;
  ctx.fillStyle = raw;
  ctx.fillRect(0, 0, 1, 1);
  const [r, g, b, a] = ctx.getImageData(0, 0, 1, 1).data;
  return `rgba(${r}, ${g}, ${b}, ${a / 255})`; // design-ok: derived from CSS design token
}

export type { MapPin };