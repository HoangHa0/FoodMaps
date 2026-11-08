"use client";

import { useEffect, useRef } from "react";
import { DEFAULT_CENTER, DEFAULT_ZOOM, getVietMapStyleUrl, loadVietMapGL, LngLat } from "../lib/vietmap";
// import "@vietmap/vietmap-gl-js/vietmap-gl.css";

export interface MapMarker {
  id: string;
  lngLat: LngLat;
  icon?: string;
  label?: string;
  variant?: "saved" | "match" | "numbered";
}

interface MapViewProps {
  center?: LngLat;
  zoom?: number;
  markers?: MapMarker[];
  onMarkerClick?: (marker: MapMarker) => void;
  onBoundsChange?: (bounds: { minLat: number; minLng: number; maxLat: number; maxLng: number }) => void;
}

export default function MapView({
  center = DEFAULT_CENTER,
  zoom = DEFAULT_ZOOM,
  markers = [],
  onMarkerClick,
  onBoundsChange,
}: MapViewProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<Map<string, any>>(new Map());

  // 1. Khởi tạo Map
  useEffect(() => {
    let isMounted = true;

    async function initMap() {
      console.log("[VietMap] Initializing...");

      const vietmapgl = await loadVietMapGL();

      if (!isMounted) {
        console.log("[VietMap] Initialization cancelled after cleanup");
        return;
      }

      if (!vietmapgl?.Map) {
        console.error("[VietMap] SDK Map constructor unavailable");
        return;
      }

      if (!mapContainerRef.current) {
        console.error("[VietMap] Map container not found");
        return;
      }

      const styleUrl = getVietMapStyleUrl();

      console.log("[VietMap] Style URL:", styleUrl.replace(
        /apikey=[^&]*/,
        "apikey=***"
      ));

      const map = new vietmapgl.Map({
        container: mapContainerRef.current,
        style: styleUrl,
        center,
        zoom,
      });

      mapInstanceRef.current = map;

      map.on("load", () => {
        if (!isMounted) return;

        console.log("[VietMap] MAP LOADED");
        map.resize();
        emitBoundsChange(map);
      });

      map.on("error", (e: any) => {
        console.error("[VietMap] MAP ERROR:", e.error ?? e);
      });
    }

    initMap();

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // Hàm phát sự kiện tọa độ khung nhìn (bbox) cho API map places
  const emitBoundsChange = (map: any) => {
    if (!onBoundsChange) return;
    const bounds = map.getBounds();
    onBoundsChange({
      minLat: bounds.getSouth(),
      minLng: bounds.getWest(),
      maxLat: bounds.getNorth(),
      maxLng: bounds.getEast(),
    });
  };

  // 2. Cập nhật Marker động
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    loadVietMapGL().then((vietmapgl) => {
      if (!vietmapgl) return;

      const currentMarkerIds = new Set(markers.map((m) => m.id));

      // Gỡ marker cũ đã bị xóa khỏi danh sách props
      markersRef.current.forEach((markerInstance, id) => {
        if (!currentMarkerIds.has(id)) {
          markerInstance.remove();
          markersRef.current.delete(id);
        }
      });

      // Thêm hoặc cập nhật marker mới
      markers.forEach((m) => {
          const [lng, lat] = m.lngLat;

        if (
          !Number.isFinite(lng) ||
          !Number.isFinite(lat) ||
          lng < -180 ||
          lng > 180 ||
          lat < -90 ||
          lat > 90
        ) {
          console.warn("[VietMap] Invalid marker coordinates:", {
            id: m.id,
            lngLat: m.lngLat,
            marker: m,
          });
          return;
        }

        if (!markersRef.current.has(m.id)) {
          const el = document.createElement("div");
          el.className = "flex items-center justify-center p-2 bg-white rounded-full shadow-md cursor-pointer text-xl border-2 border-primary-500 hover:scale-110 transition-transform";
          el.innerText = m.icon || "📍";

          el.addEventListener("click", (e) => {
            e.stopPropagation();
            onMarkerClick?.(m);
          });

          const markerInstance = new vietmapgl.Marker({ element: el })
            .setLngLat(m.lngLat)
            .addTo(map);

          markersRef.current.set(m.id, markerInstance);
        }
      });
    });
  }, [markers, onMarkerClick]);

  return (
    <div className="relative w-full h-full min-h-[400px]">
      <div ref={mapContainerRef} className="absolute inset-0 w-full h-full" />
    </div>
  );
}