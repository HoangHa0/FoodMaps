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

/** Lower case, no Vietnamese accents: "Phở Bát Đàn" -> "pho bat dan", so typing without accents works. */
export function fold(s: string): string {
  return s
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "") // combining accents
    .replace(/đ/g, "d")
    .replace(/Đ/g, "D")
    .toLowerCase()
    .trim();
}

const words = (s: string) => s.split(/[^\p{L}\p{N}]+/u).filter(Boolean);

/**
 * How well a place matches the text filter: 2 = every word of the query starts a word of the name,
 * 1 = the same in the address or category, 0 = no match. Typed without accents ("pho") it ignores
 * accents (Phở, Phố, ...); typed with accents ("phở") it matches them exactly.
 */
export function queryScore(p: MapPlace, query: string): number {
  const raw = query.trim().toLowerCase();
  if (!raw) return 1;
  const exact = fold(raw) !== raw.replace(/đ/g, "d"); // the user typed accents
  const norm = (s: string) => (exact ? s.toLowerCase() : fold(s));
  const q = words(norm(raw));
  const hits = (text: string) => {
    const w = words(norm(text));
    return q.every((t) => w.some((x) => x.startsWith(t)));
  };
  if (hits(p.name)) return 2;
  if (hits(`${p.address ?? ""} ${p.category}`)) return 1;
  return 0;
}

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
