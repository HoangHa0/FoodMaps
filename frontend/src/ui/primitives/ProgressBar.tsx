import { cn } from "../cn";

/** Progress bar, e.g. likes per place in a group session. `marker` draws a threshold line. */
export function ProgressBar({
  value,
  max,
  marker,
  label,
}: {
  value: number;
  max: number;
  marker?: number;
  label?: string;
}) {
  const pct = max > 0 ? Math.min(100, (value / max) * 100) : 0;
  return (
    <div
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={max}
      aria-valuenow={value}
      aria-label={label}
      className="relative h-2 w-full overflow-hidden rounded-control bg-bg border border-border"
    >
      <div className={cn("h-full bg-accent transition-all ease-standard")} style={{ width: `${pct}%` }} />
      {marker !== undefined && max > 0 && (
        <div className="absolute inset-y-0 w-0.5 bg-fg" style={{ left: `${(marker / max) * 100}%` }} />
      )}
    </div>
  );
}
