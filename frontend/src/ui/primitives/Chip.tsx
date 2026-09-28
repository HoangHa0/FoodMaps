import type { ButtonHTMLAttributes } from "react";

import { cn } from "../cn";

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
}

export function Chip({ selected, className, ...rest }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      {...rest}
      className={cn(
        "h-8 rounded-control border px-3 text-sm transition ease-standard",
        selected ? "bg-primary text-primary-fg border-primary" : "bg-surface border-border",
        className,
      )}
    />
  );
}
