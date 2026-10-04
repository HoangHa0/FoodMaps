import { cn } from "../cn";
import { IconCafe, IconRestaurant } from "../icons";

/**
 * Teardrop map pin. `tone` carries meaning, the theme decides the colour:
 *   highlight  featured / matched place (brand yellow, mascot face)
 *   neutral    an ordinary place
 *   hot        a trending place
 * The tip of the pin is at the bottom centre of the element: position it with
 * `translate(-50%, -100%)` at the place's point (see the map view).
 */
export function MapPin({
  tone = "neutral",
  kind = "restaurant",
  selected,
  label,
  onClick,
}: {
  tone?: "highlight" | "neutral" | "hot";
  kind?: "restaurant" | "cafe";
  selected?: boolean;
  label: string;
  onClick?: () => void;
}) {
  const Glyph = kind === "cafe" ? IconCafe : IconRestaurant;
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      aria-pressed={selected}
      title={label}
      className={cn(
        "group relative block h-11 w-9 transition-transform ease-standard hover:-translate-y-0.5",
        selected && "scale-115",
      )}
    >
      <svg viewBox="0 0 36 44" className="absolute inset-0 size-full drop-shadow-md" aria-hidden>
        <path
          d="M18 43 C14 35 3 27 3 17 C3 8.7 9.7 2 18 2 C26.3 2 33 8.7 33 17 C33 27 22 35 18 43 Z"
          className={cn(
            tone === "highlight" && "fill-primary",
            tone === "neutral" && "fill-pin-neutral",
            tone === "hot" && "fill-pin-hot",
            "stroke-surface-raised",
          )}
          strokeWidth="2"
        />
      </svg>
      <span className="absolute inset-x-0 top-1.5 flex justify-center">
        {tone === "highlight" ? (
          // mascot face
          <svg viewBox="0 0 20 18" className="size-5" aria-hidden>
            <ellipse cx="10" cy="9" rx="9" ry="8.4" className="fill-surface-raised" />
            <circle cx="7.6" cy="7.6" r="1.4" className="fill-fg" />
            <circle cx="10.6" cy="7.6" r="1.4" className="fill-fg" />
          </svg>
        ) : (
          <Glyph className={cn("size-4", tone === "neutral" && kind === "cafe" ? "text-primary" : "text-surface-raised")} strokeWidth={2.4} aria-hidden />
        )}
      </span>
    </button>
  );
}
