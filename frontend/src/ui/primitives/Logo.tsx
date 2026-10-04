import { cn } from "../cn";
import { Mascot } from "./Mascot";

/** Brand lockup: mascot + "FoodMaps" wordmark (+ optional tagline). */
export function Logo({ tagline, compact = false }: { tagline?: string; compact?: boolean }) {
  return (
    <span className="inline-flex items-center gap-2">
      <Mascot variant="round" outlined className={compact ? "size-9" : "size-16"} />
      <span className="flex flex-col">
        <span className={cn("font-brand font-bold leading-none tracking-tight text-fg", compact ? "text-2xl" : "text-[2.05rem]")}>
          FoodMaps
        </span>
        {tagline && !compact && <span className="mt-2 max-w-32 text-xs leading-snug text-fg-muted">{tagline}</span>}
      </span>
    </span>
  );
}
