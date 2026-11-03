"use client";

import { cn, IconStar } from "@/ui";

/** 1-5 star picker for one aspect (food, space, price, service). 0 = nothing chosen yet. */
export function ScoreInput({
  label,
  value,
  onChange,
  required,
}: {
  label: string;
  value: number;
  onChange: (score: number) => void;
  /** Shows a red * after the label. */
  required?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="text-sm font-semibold">
        {label}
        {required && (
          <span aria-hidden className="text-danger">
            {" "}*
          </span>
        )}
      </span>
      <div role="radiogroup" aria-label={label} aria-required={required || undefined} className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            role="radio"
            aria-checked={value === n}
            aria-label={`${n} sao`}
            onClick={() => onChange(n)}
            className="rounded-control p-1 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fg"
          >
            <IconStar
              className={cn("size-7 transition ease-standard", n <= value ? "fill-rating text-rating" : "text-border")}
              aria-hidden
            />
          </button>
        ))}
      </div>
    </div>
  );
}