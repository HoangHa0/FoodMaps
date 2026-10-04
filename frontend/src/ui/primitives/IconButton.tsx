import type { ButtonHTMLAttributes, ReactNode } from "react";

import { cn } from "../cn";

export interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  /** Required: an icon-only button needs an accessible name. */
  label: string;
  icon: ReactNode;
  /** floating: white disc over photos / the map. plain: no background. */
  variant?: "floating" | "plain";
  size?: "sm" | "md";
  /** For toggles such as "saved": exposes aria-pressed. */
  pressed?: boolean;
}

export function IconButton({ label, icon, variant = "floating", size = "md", pressed, className, ...rest }: IconButtonProps) {
  return (
    <button
      type="button"
      aria-label={label}
      title={label}
      aria-pressed={pressed}
      {...rest}
      className={cn(
        "inline-flex shrink-0 items-center justify-center rounded-full text-fg transition ease-standard",
        "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-fg",
        variant === "floating" && "bg-surface-raised shadow-float hover:scale-105",
        variant === "plain" && "hover:bg-primary-soft",
        size === "md" ? "size-10" : "size-7",
        className,
      )}
    >
      {icon}
    </button>
  );
}
