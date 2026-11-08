// Kiểu dữ liệu tọa độ chuẩn [lng, lat] dùng chung cho toàn bộ module map
export type LngLat = [lng: number, lat: number];

// Tọa độ mặc định (Hà Nội) nếu không có GPS/địa điểm

export const DEFAULT_CENTER: LngLat = [105.854444, 21.028511];
export const DEFAULT_ZOOM = 14;

export async function loadVietMapGL(): Promise<any> {
  if (typeof window === "undefined") return null;

  const getSDK = () => (window as any).vietmapgl;

  // SDK đã tải xong
  if (getSDK()?.Map) {
    return getSDK();
  }

  const script = document.getElementById(
    "vietmap-gl-js"
  ) as HTMLScriptElement | null;

  if (!script) {
    console.error("[VietMap] Không tìm thấy SDK script");
    return null;
  }

  return new Promise((resolve) => {
    const onLoad = () => {
      const sdk = getSDK();

      if (sdk?.Map) {
        console.log("[VietMap] SDK loaded successfully");
        resolve(sdk);
      } else {
        console.error("[VietMap] Script loaded nhưng không tìm thấy Map");
        resolve(null);
      }
    };

    const onError = () => {
      console.error("[VietMap] Không thể tải SDK");
      resolve(null);
    };

    script.addEventListener("load", onLoad, { once: true });
    script.addEventListener("error", onError, { once: true });

    // Kiểm tra lại để tránh bỏ lỡ sự kiện load
    if (getSDK()?.Map) {
      resolve(getSDK());
    }
  });
}

export function getVietMapStyleUrl(): string {
  const styleUrl =
    process.env.NEXT_PUBLIC_VIETMAP_STYLE_URL ||
    "https://maps.vietmap.vn/mt/default/style.json";

  const apiKey = process.env.NEXT_PUBLIC_VIETMAP_TILE_KEY;

  console.log(
    "[VietMap] API key exists:",
    Boolean(process.env.NEXT_PUBLIC_VIETMAP_TILE_KEY)
  );

  if (!apiKey) {
    console.error("Missing NEXT_PUBLIC_VIETMAP_TILE_KEY");
    return styleUrl;
  }

  const separator = styleUrl.includes("?") ? "&" : "?";

  return `${styleUrl}${separator}apikey=${encodeURIComponent(apiKey)}`;
}