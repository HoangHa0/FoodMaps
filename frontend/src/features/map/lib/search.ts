import type { MapPlace } from "../api";

/**
 * Place-name search on the places already loaded (client side, no request): accent-insensitive
 * matching, ranking for suggestions and highlighting. Used by the home search and the journey planner.
 */

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

/**
 * Up to `limit` places for the suggestion list under the search field, best first: the whole name
 * starts with the query, then names whose words start with it (shorter names first), then places
 * that match only by address or category. Pure client-side, on the places already loaded.
 */
export function suggestPlaces(places: readonly MapPlace[], query: string, limit = 6): MapPlace[] {
  const q = query.trim();
  if (!q) return [];
  const head = fold(q);
  return places
    .map((p) => ({ p, score: queryScore(p, q) * 10 + (fold(p.name).startsWith(head) ? 5 : 0) }))
    .filter((x) => x.score >= 10)
    .sort((a, b) => b.score - a.score || a.p.name.length - b.p.name.length || a.p.name.localeCompare(b.p.name, "vi"))
    .slice(0, limit)
    .map((x) => x.p);
}

/**
 * Splits a name into plain and matched parts for highlighting: in each word, the beginning that a
 * query word starts with ("pho" marks "Phở" in "Phở Bát Đàn"). Folding keeps one character per
 * character, so positions in the folded text are positions in the original.
 */
export function highlightParts(name: string, query: string): { text: string; match: boolean }[] {
  const raw = query.trim().toLowerCase();
  if (!raw) return [{ text: name, match: false }];
  const exact = fold(raw) !== raw.replace(/đ/g, "d");
  const norm = (s: string) => (exact ? s.toLowerCase() : [...s].map((c) => fold(c) || c).join(""));
  const tokens = words(norm(raw)).sort((a, b) => b.length - a.length);
  const parts: { text: string; match: boolean }[] = [];
  for (const piece of name.split(/([^\p{L}\p{N}]+)/u)) {
    const t = tokens.find((tok) => piece && norm(piece).startsWith(tok));
    if (t) {
      parts.push({ text: piece.slice(0, t.length), match: true });
      if (piece.length > t.length) parts.push({ text: piece.slice(t.length), match: false });
    } else if (piece) {
      parts.push({ text: piece, match: false });
    }
  }
  return parts;
}
