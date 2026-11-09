"use client";

import { type PointerEvent, type ReactNode, useCallback, useEffect, useRef, useState } from "react";

import { cn } from "../cn";

export type SheetSnap = "peek" | "half" | "full";

const MAX_VIEWPORT_SHARE = 0.82; // the sheet never covers more than this share of the screen
const DRAG_THRESHOLD = 5; // px of movement before a press on the handle counts as a drag

/**
 * Non-modal bottom sheet that floats over the map and can be resized like the sheets of map apps:
 *   - drag the handle up / down; on release it snaps to the nearest height (peek, half, full)
 *   - a tap on the handle switches between peek and the full content
 *   - a press anywhere outside the sheet, or Escape, lowers it to peek so the map stays usable
 *   - when `resetKey` changes (e.g. a new place is shown) it opens to `defaultSnap` again
 * "full" is the height of the content, capped at 82% of the screen; the content scrolls inside.
 */
export function BottomSheet({
  children,
  label,
  peekHeight = 128,
  defaultSnap = "full",
  resetKey,
  className,
  "data-testid": testId,
}: {
  children: ReactNode;
  /** Accessible name of the sheet. */
  label: string;
  /** Visible height when lowered: enough for the handle and the first line of content. */
  peekHeight?: number;
  defaultSnap?: SheetSnap;
  resetKey?: string | number | null;
  /** Extra classes, e.g. a max width ("lg:max-w-xl"). The position is built in. */
  className?: string;
  "data-testid"?: string;
}) {
  const sheetRef = useRef<HTMLElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const drag = useRef<{ y: number; h: number; moved: boolean } | null>(null);
  const [snap, setSnap] = useState<SheetSnap>(defaultSnap);
  const [dragHeight, setDragHeight] = useState<number | null>(null);
  const [contentHeight, setContentHeight] = useState(0);
  const [viewport, setViewport] = useState(800);

  // reopen when the content changes identity (new place, new search)
  const [shownKey, setShownKey] = useState(resetKey);
  if (shownKey !== resetKey) {
    setShownKey(resetKey);
    setSnap(defaultSnap);
  }

  useEffect(() => {
    const update = () => setViewport(window.innerHeight);
    update();
    window.addEventListener("resize", update);
    return () => window.removeEventListener("resize", update);
  }, []);

  useEffect(() => {
    const el = contentRef.current;
    if (!el) return;
    const observer = new ResizeObserver(() => setContentHeight(el.offsetHeight));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  const HANDLE = 28;
  const full = Math.max(peekHeight, Math.min(contentHeight + HANDLE + 16, viewport * MAX_VIEWPORT_SHARE));
  const half = Math.round(viewport * 0.5);
  const heights: Record<SheetSnap, number> = { peek: Math.min(peekHeight, full), half, full };
  // "half" only makes sense when it sits clearly between the two others
  const snaps: SheetSnap[] = half > peekHeight + 60 && half < full - 60 ? ["peek", "half", "full"] : ["peek", "full"];
  const height = dragHeight ?? heights[snaps.includes(snap) ? snap : "full"];

  const lower = useCallback(() => setSnap("peek"), []);

  // outside press / Escape: lower, never close (the result must stay reachable)
  useEffect(() => {
    if (snap === "peek") return;
    const onDown = (e: globalThis.PointerEvent) => {
      if (!sheetRef.current?.contains(e.target as Node)) lower();
    };
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && lower();
    document.addEventListener("pointerdown", onDown, true);
    window.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onDown, true);
      window.removeEventListener("keydown", onKey);
    };
  }, [snap, lower]);

  function onPointerDown(e: PointerEvent<HTMLButtonElement>) {
    drag.current = { y: e.clientY, h: height, moved: false };
    e.currentTarget.setPointerCapture(e.pointerId);
  }

  function onPointerMove(e: PointerEvent<HTMLButtonElement>) {
    const d = drag.current;
    if (!d) return;
    const dy = d.y - e.clientY;
    if (!d.moved && Math.abs(dy) < DRAG_THRESHOLD) return;
    d.moved = true;
    setDragHeight(Math.min(full, Math.max(heights.peek * 0.7, d.h + dy)));
  }

  function onPointerUp() {
    const d = drag.current;
    drag.current = null;
    if (!d) return;
    if (!d.moved) {
      setSnap(snap === "peek" ? "full" : "peek"); // a tap toggles
      return;
    }
    const h = dragHeight ?? d.h;
    const nearest = snaps.reduce((best, s) => (Math.abs(heights[s] - h) < Math.abs(heights[best] - h) ? s : best), snaps[0]);
    setSnap(nearest);
    setDragHeight(null);
  }

  const lowered = snap === "peek" && dragHeight === null;

  return (
    <section
      ref={sheetRef}
      aria-label={label}
      data-testid={testId}
      data-snap={snap}
      style={{ height }}
      className={cn(
        // phones / tablets: floats above the tab bar; desktop: docked to the bottom edge
        "fixed inset-x-0 bottom-[calc(6.75rem+env(safe-area-inset-bottom))] z-40 mx-auto flex w-[calc(100%-1rem)] flex-col overflow-hidden",
        "rounded-sheet bg-surface-raised shadow-sheet lg:bottom-0 lg:w-full lg:rounded-b-none",
        dragHeight === null && "transition-[height] duration-300 ease-standard",
        className,
      )}
    >
      <button
        type="button"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={(e) => {
          if (e.key === "ArrowUp") setSnap("full");
          if (e.key === "ArrowDown") setSnap("peek");
        }}
        aria-expanded={!lowered}
        aria-label={lowered ? "Kéo lên hoặc nhấn để mở rộng" : "Kéo xuống hoặc nhấn để thu gọn"}
        className="flex h-7 w-full shrink-0 cursor-grab touch-none items-center justify-center active:cursor-grabbing"
      >
        <span className="h-1.5 w-12 rounded-control bg-border" aria-hidden />
      </button>
      <div className={cn("min-h-0 flex-1 overscroll-contain", lowered ? "overflow-hidden" : "overflow-y-auto")}>
        <div ref={contentRef} className="px-4 pb-4">
          {children}
        </div>
      </div>
    </section>
  );
}
