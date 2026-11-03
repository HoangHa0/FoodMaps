import type { ReviewBody } from "../api";

/** Same rules as backend/app/modules/reviews/schemas.py: change both together. */
export const MAX_COMMENT = 1000;
export const MAX_TAGS = 8;
export const MAX_TAG_LENGTH = 60;
export const MIN_PRICE = 1_000;
export const MAX_PRICE = 5_000_000;

/** Quick choices for "Hợp với". Users can still add their own tag next to them. */
export const SUITABLE_PRESETS = ["Date", "Học bài", "Đi nhóm", "Gia đình", "Ăn một mình", "Làm việc", "Ăn khuya"];

/** What the form keeps in state: raw text for the fields the user types, 0 = no star chosen yet. */
export interface ReviewValues {
  scoreFood: number;
  scoreSpace: number;
  scorePrice: number;
  scoreService: number;
  comment: string;
  dishes: string; // "Phở bò, bún chả"
  suitableFor: string[]; // ["Date", "Học bài"], chosen with chips
  price: string; // "50.000" (dots and spaces are allowed)
}

export type ReviewErrors = Partial<Record<"comment" | "dishes" | "suitableFor" | "price", string>>;

export const EMPTY_VALUES: ReviewValues = {
  scoreFood: 0,
  scoreSpace: 0,
  scorePrice: 0,
  scoreService: 0,
  comment: "",
  dishes: "",
  suitableFor: [],
  price: "",
};

/** "Phở bò, bún chả" → ["Phở bò", "bún chả"]. Empty parts and repeats (ignoring case) are dropped. */
export function parseTags(raw: string): string[] {
  const seen = new Set<string>();
  const tags: string[] = [];
  for (const part of raw.split(",")) {
    const tag = part.trim();
    const key = tag.toLowerCase();
    if (tag && !seen.has(key)) {
      seen.add(key);
      tags.push(tag);
    }
  }
  return tags;
}

const sameTag = (a: string, b: string) => a.toLowerCase() === b.toLowerCase();

export const hasTag = (tags: string[], tag: string) => tags.some((t) => sameTag(t, tag));

/** Adds tags to a list: repeats (ignoring case) are skipped and the list stops at MAX_TAGS. */
export function addTags(current: string[], added: string[]): string[] {
  const next = [...current];
  for (const tag of added) {
    if (next.length >= MAX_TAGS) break;
    if (!hasTag(next, tag)) next.push(tag);
  }
  return next;
}

export const removeTag = (tags: string[], tag: string) => tags.filter((t) => !sameTag(t, tag));

/** "50.000" → 50000, "" → null. Everything that is not a digit is ignored. */
export function parsePrice(raw: string): number | null {
  const digits = raw.replace(/\D/g, "");
  return digits ? Number(digits) : null;
}

export const allScoresChosen = (v: ReviewValues) =>
  [v.scoreFood, v.scoreSpace, v.scorePrice, v.scoreService].every((s) => s >= 1);

export function validate(v: ReviewValues): ReviewErrors {
  const errors: ReviewErrors = {};
  if (v.comment.trim().length > MAX_COMMENT) errors.comment = `Tối đa ${MAX_COMMENT} ký tự`;

  const dishes = parseTags(v.dishes);
  if (dishes.length > MAX_TAGS) errors.dishes = `Tối đa ${MAX_TAGS} mục, cách nhau bằng dấu phẩy`;
  else if (dishes.some((t) => t.length > MAX_TAG_LENGTH)) errors.dishes = `Mỗi mục tối đa ${MAX_TAG_LENGTH} ký tự`;

  if (v.suitableFor.length > MAX_TAGS) errors.suitableFor = `Chọn tối đa ${MAX_TAGS} mục`;
  else if (v.suitableFor.some((t) => t.length > MAX_TAG_LENGTH)) errors.suitableFor = `Mỗi mục tối đa ${MAX_TAG_LENGTH} ký tự`;

  const price = parsePrice(v.price);
  if (price !== null && (price < MIN_PRICE || price > MAX_PRICE)) {
    errors.price = "Nhập số tiền từ 1.000đ đến 5.000.000đ, hoặc bỏ trống";
  }
  return errors;
}

export function toBody(v: ReviewValues): ReviewBody {
  return {
    score_food: v.scoreFood,
    score_space: v.scoreSpace,
    score_price: v.scorePrice,
    score_service: v.scoreService,
    comment: v.comment.trim() || null,
    recommended_dishes: parseTags(v.dishes),
    suitable_for: addTags([], v.suitableFor),
    price_per_person: parsePrice(v.price),
  };
}

/** The saved review → form state, to pre-fill the form when the user edits. */
export function fromReview(r: {
  score_food: number;
  score_space: number;
  score_price: number;
  score_service: number;
  comment: string | null;
  recommended_dishes: string[];
  suitable_for: string[];
  price_per_person: number | null;
}): ReviewValues {
  return {
    scoreFood: r.score_food,
    scoreSpace: r.score_space,
    scorePrice: r.score_price,
    scoreService: r.score_service,
    comment: r.comment ?? "",
    dishes: r.recommended_dishes.join(", "),
    suitableFor: [...r.suitable_for],
    price: r.price_per_person === null ? "" : String(r.price_per_person),
  };
}