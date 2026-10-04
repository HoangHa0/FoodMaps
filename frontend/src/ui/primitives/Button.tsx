import type { ButtonHTMLAttributes } from "react";

import { cn } from "../cn";
import { Spinner } from "./Spinner";

type Variant = "primary" | "secondary" | "ghost" | "danger" | "accent";
type Size = "sm" | "md" | "lg";

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
  fullWidth?: boolean;
}

// Every "how does it look" decision lives in these two tables: a redesign edits them only.
const VARIANT: Record<Variant, string> = {
  primary: "bg-primary text-primary-fg shadow-card hover:brightness-95",
  secondary: "bg-surface text-fg border border-border hover:bg-primary-soft",
  ghost: "bg-transparent text-fg hover:bg-primary-soft",
  danger: "bg-danger text-primary-fg hover:opacity-90",
  accent: "bg-accent text-accent-fg hover:opacity-90",
};
const SIZE: Record<Size, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-5",
  lg: "h-12 px-6 text-base",
};

export function Button({
  variant = "primary",
  size = "md",
  loading,
  fullWidth,
  disabled,
  className,
  children,
  ...rest
}: ButtonProps) {
  return (
    <button
      {...rest}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-control font-bold",
        "transition ease-standard disabled:opacity-50 disabled:pointer-events-none",
        VARIANT[variant],
        SIZE[size],
        fullWidth && "w-full",
        className,
      )}
    >
      {loading && <Spinner size="sm" />}
      {children}
    </button>
  );
}
