import { categoryIcon } from "./categoryIcons";

export interface CategoryCount {
  /** Display name, sentence case ("Tiệm bánh"). Also the value used in the `?loai=` filter. */
  name: string;
  count: number;
  icon: string;
}

/**
 * `places.category` is typed by hand in the sheet, so the same category comes in several spellings
 * ("Tiệm Bánh", "TIệm Bánh"). Compare and display one normalised form: trimmed, single spaces,
 * first letter upper case, the rest lower case.
 */
export function normalizeCategory(raw: string | null | undefined): string {
  const s = (raw ?? "").trim().replace(/\s+/g, " ").toLocaleLowerCase("vi");
  return s ? s.charAt(0).toLocaleUpperCase("vi") + s.slice(1) : "Khác";
}

/** Categories of the given places with their counts, the largest first. */
export function countCategories(places: ReadonlyArray<{ category: string }>): CategoryCount[] {
  const counts = new Map<string, number>();
  for (const p of places) {
    const name = normalizeCategory(p.category);
    counts.set(name, (counts.get(name) ?? 0) + 1);
  }
  return [...counts]
    .map(([name, count]) => ({ name, count, icon: categoryIcon(name) }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name, "vi"));
}

/** Query parameter of the home page that filters places by category: /?loai=Quán%20ăn */
export const CATEGORY_PARAM = "loai";

export function categoryHref(category: string | null): string {
  return category ? `/?${new URLSearchParams({ [CATEGORY_PARAM]: category }).toString()}` : "/";
}

/** Query parameter of the home page that opens one place on arrival: /?quan=<place_id> */
export const PLACE_PARAM = "quan";

export function placeHref(placeId: string): string {
  return `/?${new URLSearchParams({ [PLACE_PARAM]: placeId }).toString()}`;
}
