import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../cn";

export interface ChipProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  selected?: boolean;
  /** Optional leading icon (e.g. <IconTrending className="size-4" />). */
  icon?: ReactNode;
}

/** Filter / choice pill. Selected = dark ink pill; otherwise a light floating pill. */
export function Chip({ selected, icon, className, children, ...rest }: ChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      {...rest}
      className={cn(
        "inline-flex h-9 items-center gap-2 rounded-control px-3.5 text-[0.84rem] font-semibold transition ease-standard",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fg",
        selected
          ? "bg-fg text-surface shadow-card [&_svg]:text-primary"
          : "bg-surface text-fg shadow-card hover:bg-primary-soft",
        className,
      )}
    >
      {icon}
      {children}
    </button>
  );
}
