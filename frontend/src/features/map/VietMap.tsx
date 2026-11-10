"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  IconButton,
  IconChevronRight,
  IconList,
  IconLocate,
  IconMinus,
  IconPlus,
  useToast,
} from "@/ui";
import type { MapPlace } from "./api";
import { readToken, usePlacesLayer } from "./hooks/usePlacesLayer";
import type { PlacesLayerOptions, PlacesMap } from "./lib/placesLayer";

const TILE_KEY = process.env.NEXT_PUBLIC_VIETMAP_TILE_KEY;
const SCRIPT_URL = "https://unpkg.com/@vietmap/vietmap-gl-js@6.0.0/dist/vietmap-gl.js";
const STYLE_URL = "https://unpkg.com/@vietmap/vietmap-gl-js@6.0.0/dist/vietmap-gl.css";
const INITIAL_CENTER: [number, number] = [105.8342, 21.0278];

interface VietMapInstance {
  on(event: "style.load", callback: () => void): void;
  on(event: "error", callback: (event: { error?: Error }) => void): void;
  addControl(control: unknown, position: "top-right"): void;
  flyTo(options: { center: [number, number]; zoom: number }): void;
  fitBounds(
    bounds: [[number, number], [number, number]],
    options: { padding: number; maxZoom: number },
  ): void;
  zoomIn(): void;
  zoomOut(): void;
  resize(): void;
  remove(): void;
}

interface VietMapGL {
  Map: new (options: {
    container: HTMLElement;
    style: string;
    center: [number, number];
    zoom: number;
  }) => VietMapInstance;
  NavigationControl: new (options: { showCompass: boolean }) => unknown;
}

declare global {
  interface Window {
    vietmapgl?: VietMapGL;
  }
}

let libraryPromise: Promise<VietMapGL> | undefined;

function loadVietMap(): Promise<VietMapGL> {
  if (window.vietmapgl) return Promise.resolve(window.vietmapgl);
  if (libraryPromise) return libraryPromise;

  const pending = new Promise<VietMapGL>((resolve, reject) => {
    if (!document.querySelector("#foodmaps-vietmap-popup-style")) {
      const popupStyle = document.createElement("style");
      popupStyle.id = "foodmaps-vietmap-popup-style";
      popupStyle.textContent = ".vietmapgl-popup{z-index:50!important}";
      document.head.append(popupStyle);
    }

    if (!document.querySelector(`link[href="${STYLE_URL}"]`)) {
      const stylesheet = document.createElement("link");
      stylesheet.rel = "stylesheet";
      stylesheet.href = STYLE_URL;
      document.head.append(stylesheet);
    }

    const script = document.createElement("script");
    script.src = SCRIPT_URL;
    script.async = true;
    script.onload = () => {
      if (window.vietmapgl) resolve(window.vietmapgl);
      else reject(new Error("Thư viện bản đồ VietMap không khởi tạo được."));
    };
    script.onerror = () => reject(new Error("Không tải được thư viện bản đồ VietMap. Kiểm tra kết nối mạng."));
    document.head.append(script);
  }).catch((error: unknown) => {
    libraryPromise = undefined;
    throw error;
  });

  libraryPromise = pending;
  return pending;
}

export function VietMap({
  places,
  selectedId,
  onSelect,
  onBackgroundClick,
  savedIds,
  savedIcons,
  preview,
  listView,
  onToggleList,
  list,
}: {
  places: MapPlace[];
  /** The place the user picked (not a default). Changing it flies the map to that place. */
  selectedId: string | null;
  onSelect: (id: string) => void;
  /** Click on empty map. */
  onBackgroundClick?: () => void;
  savedIds?: ReadonlySet<string>;
  /** place_id -> icon of the list that holds the saved place */
  savedIcons?: ReadonlyMap<string, string>
  preview?: React.ReactNode;
  /** Optional "list inside the map" toggle: shown only when all three are given. */
  listView?: boolean;
  onToggleList?: () => void;
  list?: React.ReactNode;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<VietMapInstance | null>(null);
  const hasFitPlacesRef = useRef(false);
  const onSelectRef = useRef(onSelect);
  const onBackgroundClickRef = useRef(onBackgroundClick);
  const [loaded, setLoaded] = useState(false);
  const [placesMap, setPlacesMap] = useState<PlacesMap | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState(0);
  const toast = useToast();

  useEffect(() => {
    onSelectRef.current = onSelect;
    onBackgroundClickRef.current = onBackgroundClick;
  }, [onSelect, onBackgroundClick]);

  useEffect(() => {
    if (!containerRef.current) return;
    if (!TILE_KEY) return;

    let active = true;
    let instance: VietMapInstance | undefined;

    void loadVietMap()
      .then((vietmapgl) => {
        if (!active || !containerRef.current) return;
        const style = `https://tools.vietmap.vn/map-editor/maps/styles/9fae55aa4f/style.json?apikey=${encodeURIComponent(TILE_KEY)}`;
        instance = new vietmapgl.Map({
          container: containerRef.current,
          style,
          center: INITIAL_CENTER,
          zoom: 13,
        });
        mapRef.current = instance;
        instance.resize();
        // no NavigationControl: the zoom / locate buttons below are the map's only controls
        instance.on("style.load", () => {
          if (active) {
            instance?.resize();
            setLoaded(true);
            // The real SDK object has every method PlacesMap needs; our local type lists fewer.
            setPlacesMap(instance as unknown as PlacesMap);
          }
        });
        instance.on("error", (event) => {
          // A missing font file or glyph range is not a broken map: names may not draw, the pins still do.
          const detail = `${(event.error as { url?: string } | undefined)?.url ?? ""} ${event.error?.message ?? ""}`;
          if (detail.includes("/fonts/")) {
            console.warn("[VietMap] glyph request failed:", detail.trim());
            return;
          }
          if (active) {
            setError(
              "VietMap không tải được dữ liệu nền. Kiểm tra quyền Tile API key và domain localhost trong VietMap.",
            );
          }
        });
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(cause instanceof Error ? cause.message : "Không tải được bản đồ VietMap.");
        }
      });

    const observer = new ResizeObserver(() => mapRef.current?.resize());
    observer.observe(containerRef.current);
    return () => {
      active = false;
      observer.disconnect();

      if (mapRef.current === instance) {
        mapRef.current = null;
      }

      if (instance) {
        instance.remove();
      }
    };
  }, [retry]);

  // Fit the first non-empty list of places once.
  useEffect(() => {
    const instance = mapRef.current;
    if (!loaded || !instance || places.length === 0 || hasFitPlacesRef.current) return;
    const longitudes = places.map((place) => place.lng);
    const latitudes = places.map((place) => place.lat);
    instance.fitBounds(
      [
        [Math.min(...longitudes), Math.min(...latitudes)],
        [Math.max(...longitudes), Math.max(...latitudes)],
      ],
      { padding: 48, maxZoom: 15 },
    );
    hasFitPlacesRef.current = true;
  }, [loaded, places]);

  // Stable callbacks: the layer is rebuilt whenever `layerOptions` changes.
  const handleSelect = useCallback((id: string) => onSelectRef.current(id), []);
  const handleBackground = useCallback(() => onBackgroundClickRef.current?.(), []);

  // Colours come from the design tokens (names follow the Tailwind classes used in this file).
  const layerOptions = useMemo<PlacesLayerOptions>(
    () => ({
      pinColors: {
        fill: {
          default: readToken("--color-surface-raised"),
          saved: readToken("--color-primary-soft"),
          selected: readToken("--color-primary"),
        },
        stroke: readToken("--color-surface"),
      },
      textColors: { text: readToken("--color-fg"), halo: readToken("--color-surface-raised") },
      onSelect: handleSelect,
      onBackgroundClick: handleBackground,
    }),
    [handleSelect, handleBackground],
  );

    usePlacesLayer({
      map: placesMap,
      places,
      selectedId,
      savedIds,
      iconByPlace: savedIcons,
      options: layerOptions,
    });

  // A location problem is not a map problem: say it in a toast, keep the map as it is
  function locate() {
    if (!navigator.geolocation) {
      toast("Trình duyệt không hỗ trợ lấy vị trí.", { tone: "error" });
      return;
    }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        mapRef.current?.flyTo({ center: [coords.longitude, coords.latitude], zoom: 15 });
      },
      () => toast("Không lấy được vị trí. Hãy cho phép trình duyệt truy cập vị trí.", { tone: "error" }),
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    );
  }

  const mapError = TILE_KEY ? error : "Thiếu NEXT_PUBLIC_VIETMAP_TILE_KEY trong frontend/.env.local.";

  return (
    <div className="@container absolute inset-0 overflow-hidden rounded-card bg-surface" data-testid="explore-map">
      <div ref={containerRef} className="absolute inset-0 h-full w-full" aria-label="Bản đồ VietMap" />

      {!loaded && !mapError && (
        <p className="absolute left-1/2 top-1/2 z-10 -translate-x-1/2 -translate-y-1/2 rounded-lg bg-surface-raised px-3 py-2 text-sm shadow-card">
          Đang tải bản đồ…
        </p>
      )}
      {mapError && (
        <div className="absolute inset-x-4 top-4 z-20 rounded-card bg-surface-raised p-3 text-sm shadow-card" role="alert">
          <p>{mapError}</p>
          {TILE_KEY && (
            <button type="button" className="mt-2 font-semibold text-primary" onClick={() => { setError(null); setRetry((value) => value + 1); }}>
              Thử tải lại
            </button>
          )}
        </div>
      )}

      {!listView && preview && (
        <div className="absolute inset-x-3 top-3 z-10 md:right-auto md:w-[min(42%,300px)]">
          {preview}
        </div>
      )}

      {listView && list && (
        <div className="absolute inset-0 z-10 overflow-y-auto bg-bg/95 p-4 pb-20">
          {list}
        </div>
      )}

      <div className="absolute right-3 top-3 z-10 hidden w-10 flex-col overflow-hidden rounded-control bg-surface-raised shadow-float md:flex">
        <IconButton variant="plain" label="Phóng to" icon={<IconPlus className="size-5" />} className="w-full rounded-none" onClick={() => mapRef.current?.zoomIn()} />
        <span className="mx-2 h-px bg-border" aria-hidden />
        <IconButton variant="plain" label="Thu nhỏ" icon={<IconMinus className="size-5" />} className="w-full rounded-none" onClick={() => mapRef.current?.zoomOut()} />
        <span className="mx-2 h-px bg-border" aria-hidden />
        <IconButton variant="plain" label="Vị trí của tôi" icon={<IconLocate className="size-5" />} className="w-full rounded-none" onClick={locate} />
      </div>

      {/* phones: pinch to zoom, so only "my location" is shown */}
      <IconButton label="Vị trí của tôi" icon={<IconLocate className="size-5" />} className="absolute bottom-9 right-3 z-10 md:hidden" onClick={locate} />

      {onToggleList && (
        <>
          {/* bottom-9, not bottom-3: the map's own attribution sits in the bottom corner and must stay visible */}
          <button
            type="button"
            onClick={onToggleList}
            aria-pressed={listView}
            className="absolute bottom-9 right-3 z-20 inline-flex h-9 items-center gap-2 rounded-control bg-surface-raised px-4 text-sm font-semibold shadow-float transition ease-standard hover:bg-primary-soft"
          >
            <IconList className="size-4" aria-hidden />
            {listView ? "Xem bản đồ" : "Xem danh sách"}
            <IconChevronRight className={listView ? "size-4 rotate-90" : "size-4 -rotate-90"} aria-hidden />
          </button>
        </>
      )}
    </div>
  );
}