import type { MapPlace } from "@/features/map";

/** Places per page of the list. */
export const PAGE_SIZE = 12;

/** VND per person. */
export const PRICE_RANGES: { label: string; min: number | null; max: number | null }[] = [
  { label: "Mọi giá", min: null, max: null },
  { label: "Dưới 50k", min: null, max: 50_000 },
  { label: "50k – 100k", min: 50_000, max: 100_000 },
  { label: "100k – 200k", min: 100_000, max: 200_000 },
  { label: "Trên 200k", min: 200_000, max: null },
];

export type SortId = "default" | "name" | "price-asc" | "price-desc";
export const SORTS: { id: SortId; label: string }[] = [
  { id: "default", label: "Mặc định" },
  { id: "name", label: "Tên A → Z" },
  { id: "price-asc", label: "Giá thấp → cao" },
  { id: "price-desc", label: "Giá cao → thấp" },
];

export function inPriceRange(p: MapPlace, index: number): boolean {
  const r = PRICE_RANGES[index] ?? PRICE_RANGES[0];
  if (r.min === null && r.max === null) return true;
  if (p.price_per_person === null) return false;
  return (r.min === null || p.price_per_person >= r.min) && (r.max === null || p.price_per_person < r.max);
}

export function sortPlaces(places: MapPlace[], sort: SortId): MapPlace[] {
  if (sort === "default") return places;
  const copy = [...places];
  const price = (p: MapPlace, missing: number) => p.price_per_person ?? missing;
  if (sort === "name") copy.sort((a, b) => a.name.localeCompare(b.name, "vi"));
  if (sort === "price-asc") copy.sort((a, b) => price(a, Infinity) - price(b, Infinity));
  if (sort === "price-desc") copy.sort((a, b) => price(b, -Infinity) - price(a, -Infinity));
  return copy;
}
