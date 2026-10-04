import type { ReactNode } from "react";

import { cn } from "../cn";

/**
 * Handwritten note ("Good food is always a good idea!", map labels). Decorative text in the
 * hand font; `tilt` rotates it a few degrees like the mock-up.
 */
export function HandNote({
  children,
  tilt = 0,
  className,
}: {
  children: ReactNode;
  /** Degrees, negative = counter-clockwise. */
  tilt?: number;
  className?: string;
}) {
  return (
    <span
      className={cn("inline-block font-hand leading-tight text-fg", className)}
      style={tilt ? { transform: `rotate(${tilt}deg)` } : undefined}
    >
      {children}
    </span>
  );
}

/** Three short "pop" strokes drawn next to the mascot and the headline. */
export function PopLines({ className, flip = false }: { className?: string; flip?: boolean }) {
  return (
    <svg viewBox="0 0 24 40" className={cn("shrink-0", className)} style={flip ? { transform: "scaleX(-1)" } : undefined} aria-hidden>
      <path d="M4 4 L14 11 M4 20 L19 19 M5 36 L14 30" className="stroke-fg" strokeWidth="2.6" strokeLinecap="round" fill="none" />
    </svg>
  );
}

/** Brush-stroke underline in the primary colour (under "Near You"). */
export function BrushUnderline({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 240 16" preserveAspectRatio="none" className={className} aria-hidden>
      <path
        d="M3 12 C40 8 90 5 140 6 C175 6.5 205 5 237 3"
        className="stroke-primary"
        strokeWidth="6"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}
