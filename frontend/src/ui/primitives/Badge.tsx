import type { ReactNode } from "react";

import { cn } from "../cn";

type Tone = "neutral" | "accent" | "success" | "warning" | "danger";
const TONE: Record<Tone, string> = {
  neutral: "bg-primary-soft text-fg",
  accent: "bg-accent text-accent-fg",
  success: "bg-success text-primary-fg",
  warning: "bg-warning text-primary-fg",
  danger: "bg-danger text-primary-fg",
};

export function Badge({ tone = "neutral", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span className={cn("inline-flex items-center rounded-control px-3.5 py-1 text-[0.82rem] font-medium", TONE[tone])}>
      {children}
    </span>
  );
}
