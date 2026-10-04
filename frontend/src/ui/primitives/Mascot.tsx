import { cn } from "../cn";

/**
 * The FoodMaps mascot: a sunny blob with two dot eyes. Pure SVG, coloured with theme tokens
 * (fill-primary / fill-fg), so it follows the active theme.
 *
 *   variant="blob"   hero / footer: slightly squashed shape with a flat lower-right side
 *   variant="round"  logo / avatar: rounder shape, optional light outline
 *   variant="flying" tiny doodle with motion lines, used before section titles
 */
export function Mascot({
  variant = "blob",
  outlined = false,
  className,
  title,
}: {
  variant?: "blob" | "round" | "flying";
  outlined?: boolean;
  className?: string;
  /** Accessible name; omit for a decorative mascot (aria-hidden). */
  title?: string;
}) {
  const a11y = title ? { role: "img", "aria-label": title } : { "aria-hidden": true };
  if (variant === "flying") {
    return (
      <svg viewBox="0 0 32 26" className={cn("shrink-0", className)} {...a11y}>
        <path d="M2 9 L9 6 M3 15 L9 13" className="stroke-fg" strokeWidth="2" strokeLinecap="round" fill="none" />
        <path
          d="M12 9 C14 3 22 1 27 5 C31 8 31 14 28 18 C24 23 17 25 13 21 C10 18 10 13 12 9 Z"
          className="fill-primary stroke-fg"
          strokeWidth="1.4"
        />
        <path d="M17 10 L22 7 L23 14 Z" className="fill-surface-raised" opacity="0.6" />
        <circle cx="16.5" cy="13" r="1.3" className="fill-fg" />
        <circle cx="19.5" cy="13" r="1.3" className="fill-fg" />
      </svg>
    );
  }
  if (variant === "round") {
    return (
      <svg viewBox="0 0 100 92" className={cn("shrink-0", className)} {...a11y}>
        <path
          d="M50 3 C80 2 98 22 97 48 C96 74 76 90 49 89 C21 88 3 72 3 46 C3 21 22 4 50 3 Z"
          className={cn("fill-primary", outlined && "stroke-surface-raised")}
          strokeWidth={outlined ? 3 : 0}
        />
        <ellipse cx="27" cy="28" rx="4" ry="4.6" className="fill-fg" />
        <ellipse cx="37" cy="27" rx="4" ry="4.6" className="fill-fg" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 170 152" className={cn("shrink-0", className)} {...a11y}>
      <path
        d="M86 3 C130 1 166 30 168 70 C169 92 158 103 140 113 C118 126 100 141 74 149
           C44 156 10 136 3 101 C-4 62 22 6 86 3 Z"
        className="fill-primary"
      />
      <ellipse cx="57" cy="44" rx="5" ry="5.6" className="fill-fg" />
      <ellipse cx="70" cy="43" rx="5" ry="5.6" className="fill-fg" />
    </svg>
  );
}
