"use client";

import { type ReactNode, useEffect } from "react";

import { cn } from "../cn";

/**
 * Bottom sheet floating over the map (AI Match results, place details, lobby, ...).
 * Minimal, dependency-free version. For drag-to-dismiss, swap the internals for a library such
 * as `vaul` while keeping these props, and no feature needs to change.
 */
export function Sheet({
  open,
  onClose,
  title,
  children,
  modal = false,
}: {
  open: boolean;
  onClose?: () => void;
  title?: string;
  children: ReactNode;
  /** true: dims the background and blocks interaction with the map behind */
  modal?: boolean;
}) {
  useEffect(() => {
    if (!open || !onClose) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <>
      {modal && <div className="fixed inset-0 z-40 bg-overlay" onClick={onClose} aria-hidden />}
      <section
        role="dialog"
        aria-modal={modal}
        aria-label={title}
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 mx-auto max-h-[85vh] w-full max-w-xl overflow-y-auto",
          "rounded-t-sheet bg-surface-raised shadow-sheet p-4",
        )}
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-control bg-border" aria-hidden />
        {title && <h2 className="mb-3 font-display text-lg font-semibold">{title}</h2>}
        {children}
      </section>
    </>
  );
}
