/**
 * Default pin icon for a place category.
 *
 * `places.category` is a free string, so matching is by keyword, not by exact value. Replace or extend
 * RULES once the real category values are known (select category, count(*) from places group by 1).
 * Order matters: the first matching rule wins.
 */
const RULES: ReadonlyArray<readonly [RegExp, string]> = [
  [/cafe|cà phê|ca phe|coffee/i, "☕"],
  [/trà|tea|boba/i, "🧋"],
  [/bakery|bánh|banh/i, "🥐"],
  [/dessert|tráng miệng|kem|ice/i, "🍨"],
  [/bar|pub|beer|bia/i, "🍺"],
  [/noodle|phở|pho|bún|bun|mì/i, "🍜"],
];

export const DEFAULT_PIN_ICON = "🍽️";

export function categoryIcon(category: string): string {
  const match = RULES.find(([pattern]) => pattern.test(category));
  return match ? match[1] : DEFAULT_PIN_ICON;
}