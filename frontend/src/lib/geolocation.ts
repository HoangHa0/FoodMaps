"use client";

import { useCallback, useState } from "react";

/** A point in WGS84, the shape of the backend's `GeoPoint`. */
export interface LatLng {
  lat: number;
  lng: number;
}

export type PositionState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "ok"; point: LatLng }
  | { status: "error"; message: string };

/**
 * The device position, asked for only when the user presses a button (`request`), never on page
 * load. Browsers allow it only on https or localhost, so on a phone opening http://<LAN-IP>:3000
 * it fails with a readable message instead of hanging.
 */
export function useCurrentPosition() {
  const [state, setState] = useState<PositionState>({ status: "idle" });

  const request = useCallback(() => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator) || !window.isSecureContext) {
      setState({ status: "error", message: "Trình duyệt không cho lấy vị trí trên trang này" });
      return;
    }
    setState({ status: "loading" });
    navigator.geolocation.getCurrentPosition(
      (p) => setState({ status: "ok", point: { lat: p.coords.latitude, lng: p.coords.longitude } }),
      (e) =>
        setState({
          status: "error",
          message: e.code === e.PERMISSION_DENIED ? "Bạn đã chặn quyền vị trí" : "Không lấy được vị trí, thử lại",
        }),
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    );
  }, []);

  const clear = useCallback(() => setState({ status: "idle" }), []);

  return { position: state, request, clear };
}
