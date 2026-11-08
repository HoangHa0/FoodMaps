/**
 * Draws every place on the map as a symbol layer (icon + name), not as DOM markers.
 *
 * - Icon size grows with zoom; the name appears only from NAME_MIN_ZOOM.
 * - Collision thinning is done by the map: when pins overlap, the one with the lower `priority` wins
 *   (selected 0, saved 1, others 2). The name is dropped before the icon (`text-optional`).
 * - The selected place has its own layer on top: larger, never hidden by collisions.
 * - Click a pin -> onSelect(place_id). Click empty map -> onBackgroundClick().
 * - A style change removes sources, layers and images; `style.load` re-adds them from the latest data.
 *
 * The map object is typed structurally (PlacesMap) so this file does not depend on the SDK's type names.
 */

import { categoryIcon } from "./categoryIcons";
import { type PinColors, pinImageId, registerPinImages } from "./pinImages";

export interface MapPin {
  place_id: string;
  name: string;
  category: string;
  lat: number;
  lng: number;
}

export interface TextColors {
  text: string;
  halo: string;
}

interface Feature {
  type: "Feature";
  geometry: { type: "Point"; coordinates: [number, number] }; // [lng, lat]
  properties: { id: string; name: string; iconId: string; priority: number; selected: boolean };
}

export interface PinCollection {
  type: "FeatureCollection";
  features: Feature[];
}

interface ClickEvent {
  point: { x: number; y: number };
}

/** The slice of the VietMap / MapLibre map API used here. */
export interface PlacesMap {
  isStyleLoaded(): boolean;
  getSource(id: string): unknown;
  addSource(id: string, source: unknown): unknown;
  getLayer(id: string): unknown;
  addLayer(layer: Record<string, unknown>): unknown;
  getZoom(): number;
  flyTo(options: { center: [number, number]; zoom?: number; essential?: boolean }): unknown;
  queryRenderedFeatures(point: { x: number; y: number }, options?: { layers?: string[] }): unknown[];
  getCanvas(): { style: { cursor: string } };
  hasImage(id: string): boolean;
  addImage(id: string, image: ImageData, options?: { pixelRatio?: number }): unknown;
  on(type: string, listener: (event: never) => void): unknown;
  on(type: string, layerId: string, listener: (event: never) => void): unknown;
  off(type: string, listener: (event: never) => void): unknown;
  off(type: string, layerId: string, listener: (event: never) => void): unknown;
}

export const PLACES_SOURCE = "foodmaps-places";
export const PINS_LAYER = "foodmaps-places-pins";
export const SELECTED_LAYER = "foodmaps-places-selected";

const NAME_MIN_ZOOM = 13;
const FLY_TO_MIN_ZOOM = 15;

const PRIORITY = { selected: 0, saved: 1, other: 2 } as const;

/** Pure: places -> GeoJSON with the icon id and the collision priority of each pin. */
export function buildPinCollection(
  places: readonly MapPin[],
  selectedId: string | null,
  savedIds: ReadonlySet<string>,
): PinCollection {
  return {
    type: "FeatureCollection",
    features: places.map((place) => {
      const selected = place.place_id === selectedId;
      const saved = savedIds.has(place.place_id);
      const variant = selected ? "selected" : saved ? "saved" : "default";
      return {
        type: "Feature",
        geometry: { type: "Point", coordinates: [place.lng, place.lat] },
        properties: {
          id: place.place_id,
          name: place.name,
          iconId: pinImageId(variant, categoryIcon(place.category)),
          priority: selected ? PRIORITY.selected : saved ? PRIORITY.saved : PRIORITY.other,
          selected,
        },
      };
    }),
  };
}

export interface PlacesLayerOptions {
  pinColors: PinColors;
  textColors: TextColors;
  onSelect: (placeId: string) => void;
  onBackgroundClick: () => void;
  /** Font stack that exists in the map style and covers Vietnamese. Left to the style default if unset. */
  textFont?: string[];
}

export interface PlacesLayerController {
  setData(places: readonly MapPin[], selectedId: string | null, savedIds: ReadonlySet<string>): void;
  /** Fly to a place (used when the user picks one from a list). */
  flyTo(placeId: string): void;
  destroy(): void;
}

function sizeByZoom(scale: number) {
  return ["interpolate", ["linear"], ["zoom"], 10, 0.45 * scale, 14, 0.7 * scale, 17, 0.95 * scale];
}

function layerSpec(id: string, selected: boolean, options: PlacesLayerOptions): Record<string, unknown> {
  const layout: Record<string, unknown> = {
    "icon-image": ["get", "iconId"],
    "icon-size": sizeByZoom(selected ? 1.35 : 1),
    "icon-allow-overlap": selected,
    "icon-ignore-placement": selected,
    "text-field": ["step", ["zoom"], "", selected ? 0 : NAME_MIN_ZOOM, ["get", "name"]],
    "text-size": ["interpolate", ["linear"], ["zoom"], 13, 11, 17, 14],
    "text-anchor": "top",
    "text-offset": [0, 1.1 * (selected ? 1.3 : 1)],
    "text-optional": true, // under collision the name goes first, the icon stays
    "text-allow-overlap": selected,
    "symbol-sort-key": ["get", "priority"], // lower value is placed first, so it wins a collision
  };
  if (options.textFont) layout["text-font"] = options.textFont;

  return {
    id,
    type: "symbol",
    source: PLACES_SOURCE,
    filter: ["==", ["get", "selected"], selected],
    layout,
    paint: {
      "text-color": options.textColors.text,
      "text-halo-color": options.textColors.halo,
      "text-halo-width": 1.5,
    },
  };
}

export function createPlacesLayer(map: PlacesMap, options: PlacesLayerOptions): PlacesLayerController {
  let places: readonly MapPin[] = [];
  let collection = buildPinCollection([], null, new Set());

  const ensureLayers = () => {
    const source = map.getSource(PLACES_SOURCE) as { setData?: (data: PinCollection) => void } | undefined;
    if (!source) map.addSource(PLACES_SOURCE, { type: "geojson", data: collection });
    else source.setData?.(collection);
    if (!map.getLayer(PINS_LAYER)) map.addLayer(layerSpec(PINS_LAYER, false, options));
    if (!map.getLayer(SELECTED_LAYER)) map.addLayer(layerSpec(SELECTED_LAYER, true, options));
  };

  const unregisterImages = registerPinImages(map, options.pinColors);

  const onStyleLoad = () => ensureLayers();
  if (map.isStyleLoaded()) ensureLayers();
  map.on("style.load", onStyleLoad);

  const onPinClick = (event: { features?: Array<{ properties?: { id?: string } }> }) => {
    const id = event.features?.[0]?.properties?.id;
    if (id) options.onSelect(id);
  };
  const onMapClick = (event: ClickEvent) => {
    const hit = map.queryRenderedFeatures(event.point, { layers: [PINS_LAYER, SELECTED_LAYER] });
    if (hit.length === 0) options.onBackgroundClick();
  };
  const setPointer = () => {
    map.getCanvas().style.cursor = "pointer";
  };
  const clearPointer = () => {
    map.getCanvas().style.cursor = "";
  };

  for (const layer of [PINS_LAYER, SELECTED_LAYER]) {
    map.on("click", layer, onPinClick as never);
    map.on("mouseenter", layer, setPointer as never);
    map.on("mouseleave", layer, clearPointer as never);
  }
  map.on("click", onMapClick as never);

  return {
    setData(next, selectedId, savedIds) {
      places = next;
      collection = buildPinCollection(next, selectedId, savedIds);
      if (map.isStyleLoaded()) ensureLayers();
    },
    flyTo(placeId) {
      const place = places.find((p) => p.place_id === placeId);
      if (!place) return;
      map.flyTo({
        center: [place.lng, place.lat],
        zoom: Math.max(map.getZoom(), FLY_TO_MIN_ZOOM),
        essential: true,
      });
    },
    destroy() {
      map.off("style.load", onStyleLoad as never);
      map.off("click", onMapClick as never);
      for (const layer of [PINS_LAYER, SELECTED_LAYER]) {
        map.off("click", layer, onPinClick as never);
        map.off("mouseenter", layer, setPointer as never);
        map.off("mouseleave", layer, clearPointer as never);
      }
      unregisterImages();
    },
  };
}