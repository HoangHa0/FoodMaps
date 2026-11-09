import type { RejectReason } from "../api";

/** Quick suggestions under the mood field (spec 1.1): a tap adds the words to the sentence. */
export const MOOD_CHIPS = ["Hẹn hò", "Học bài", "Đói bụng", "Dưới 100k", "Món quen thuộc", "Ăn khuya", "Ngồi một mình", "Đi nhóm"];

/** Radius options; they only apply when a starting point is known (the backend needs `origin`). */
export const RADII = [500, 1000, 2000, 5000];
export const DEFAULT_RADIUS = 2000;

export interface Budget {
  label: string;
  min: number | null;
  max: number | null;
}

/** VND per person, same unit as `MatchCriteria.price_min/price_max`. */
export const BUDGETS: Budget[] = [
  { label: "Bất kỳ", min: null, max: null },
  { label: "Dưới 50k", min: null, max: 50_000 },
  { label: "50k – 100k", min: 50_000, max: 100_000 },
  { label: "100k – 200k", min: 100_000, max: 200_000 },
  { label: "Trên 200k", min: 200_000, max: null },
];

/** The 4 quick reasons of "Không hợp" (spec 1.3), in the order they are shown. */
/** Shown when "Không hợp" leaves nothing. */
export const EMPTY_MESSAGE =
  "Không còn quán nào khớp tiêu chí. Thử mô tả khác, nới bán kính, khoảng giá hoặc đổi khu vực nhé.";

/**
 * Only these two reasons remove places (the server drops backups that are not cheaper / closer than the
 * rejected one, DECISIONS D18), so only they can empty the list while backups were left.
 */
export const EMPTY_MESSAGE_AFTER: Partial<Record<RejectReason, string>> = {
  too_far: "Không còn quán nào gần hơn quán vừa rồi. Thử nới bán kính hoặc đổi mô tả nhé.",
  too_expensive: "Không còn quán nào rẻ hơn quán vừa rồi. Thử nâng khoảng giá hoặc đổi mô tả nhé.",
};

export const REJECT_REASONS: { reason: RejectReason; label: string }[] = [
  { reason: "too_far", label: "Quá xa" },
  { reason: "too_expensive", label: "Quá đắt" },
  { reason: "too_crowded", label: "Quá đông" },
  { reason: "wrong_vibe", label: "Sai vibe" },
];

export const radiusLabel = (m: number) => (m < 1000 ? `${m} m` : `${m / 1000} km`);

/** Adds a chip's words to the sentence once ("yên tĩnh" + "Date" -> "yên tĩnh, date"). */
export function addChip(text: string, chip: string): string {
  const current = text.trim();
  if (current.toLowerCase().includes(chip.toLowerCase())) return text;
  return current ? `${current}, ${chip.toLowerCase()}` : chip;
}

/** The budget option matching a min/max pair (falls back to "Bất kỳ"). */
export function budgetIndex(min: number | null | undefined, max: number | null | undefined): number {
  const i = BUDGETS.findIndex((b) => b.min === (min ?? null) && b.max === (max ?? null));
  return i < 0 ? 0 : i;
}

/**
 * Google Maps directions deep link (no API key; opens the Maps app on phones). `destination` is
 * the team's own name of the place; Google routes by `destination_place_id` when it is a real ID.
 */
export function directionsUrl(placeId: string, name: string | null | undefined): string {
  const q = new URLSearchParams({ api: "1", destination: name ?? "Quán đã chọn", destination_place_id: placeId });
  return `https://www.google.com/maps/dir/?${q.toString()}`;
}
