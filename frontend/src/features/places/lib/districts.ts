import type { LatLng } from "@/lib/geolocation";

/**
 * Quick-pick districts of central Hanoi for the origin picker: a tap needs no network call.
 * The points are approximate district centres (WGS84): enough for "eat around here" with a radius of
 * 500 m to 5 km. To add a district, add a line; the picker shows every entry.
 */
export const DISTRICTS: readonly { name: string; point: LatLng }[] = [
  { name: "Hoàn Kiếm", point: { lat: 21.0285, lng: 105.8522 } },
  { name: "Ba Đình", point: { lat: 21.0356, lng: 105.8196 } },
  { name: "Đống Đa", point: { lat: 21.018, lng: 105.827 } },
  { name: "Hai Bà Trưng", point: { lat: 21.009, lng: 105.857 } },
  { name: "Cầu Giấy", point: { lat: 21.0333, lng: 105.7914 } },
  { name: "Tây Hồ", point: { lat: 21.07, lng: 105.823 } },
];
