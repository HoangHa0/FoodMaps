import type { HTMLAttributes } from "react";

import { cn } from "../cn";

export function Card({ className, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      {...rest}
      className={cn("rounded-card bg-surface border border-border/60 shadow-card p-4", className)}
    />
  );
}
