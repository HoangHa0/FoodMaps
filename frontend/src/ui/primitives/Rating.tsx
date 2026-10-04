import { cn } from "../cn";
import { IconStar } from "../icons";

/** "★ 4.8 (1.2k)" — star rating with an optional review count. */
export function Rating({
  value,
  count,
  size = "md",
  className,
}: {
  value: number;
  /** Already formatted, e.g. "1.2k reviews" or "982". */
  count?: string;
  size?: "sm" | "md";
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-1", size === "sm" ? "text-xs" : "text-sm", className)}>
      <IconStar className={cn("fill-rating text-rating", size === "sm" ? "size-3.5" : "size-4")} aria-hidden />
      <span className="font-semibold text-fg">{value.toFixed(1)}</span>
      {count && <span className="text-fg-muted">({count})</span>}
    </span>
  );
}
