import type { LatLng } from "@/lib/geolocation";

/**
 * The starting point of a search: where the user wants to eat around. `label` and `source` are for the
 * UI only; the backend receives just `point` (`MatchCriteria.origin`).
 */
export interface Origin {
  point: LatLng;
  label: string;
  /** gps: the device position; search: a typed address; preset: a quick district chip. */
  source: "gps" | "search" | "preset";
}

export const MY_LOCATION_LABEL = "Vị trí của tôi";

/** Radius options; they only apply when a starting point is known (the backend filters from `origin`). */
export const DEFAULT_RADII: readonly number[] = [500, 1000, 2000, 5000];

export const radiusLabel = (m: number) => (m < 1000 ? `${m} m` : `${m / 1000} km`);

/**
 * The device position, asked for only when the user presses the button. Browsers allow it only on https
 * or localhost, so on a phone opening http://<LAN-IP>:3000 it rejects with a readable message
 * instead of hanging. Rejects with an Error whose message is ready to show.
 */
export function getDevicePosition(): Promise<LatLng> {
  return new Promise((resolve, reject) => {
    if (typeof navigator === "undefined" || !("geolocation" in navigator) || !window.isSecureContext) {
      reject(new Error("Trình duyệt không cho lấy vị trí trên trang này"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude }),
      (e) =>
        reject(
          new Error(e.code === e.PERMISSION_DENIED ? "Bạn đã chặn quyền vị trí" : "Không lấy được vị trí, thử lại"),
        ),
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    );
  });
}
