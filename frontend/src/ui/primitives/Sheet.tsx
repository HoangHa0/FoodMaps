"use client";

import { type ReactNode, useEffect } from "react";

import { cn } from "../cn";
import { IconClose } from "../icons";

/**
 * Sheet for a focused task (login, review form, ...): bottom sheet on phones, centred dialog from
 * `sm` up. Closes with the X button, Escape, or a click on the dimmed background (modal).
 * For a sheet the user resizes over the map, use BottomSheet instead.
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
  /** true: dims the background and blocks interaction with the page behind */
  modal?: boolean;
}) {
  useEffect(() => {
    if (!open || !onClose) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // keep the page behind still while a modal sheet is open
  useEffect(() => {
    if (!open || !modal) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [open, modal]);

  if (!open) return null;
  return (
    <>
      {modal && <div className="fixed inset-0 z-40 bg-overlay" onClick={onClose} aria-hidden />}
      <section
        role="dialog"
        aria-modal={modal}
        aria-label={title}
        className={cn(
          "fixed inset-x-0 bottom-0 z-50 mx-auto max-h-[88dvh] w-full max-w-xl overflow-y-auto overscroll-contain",
          "rounded-t-sheet bg-surface-raised p-4 pt-3 shadow-sheet sm:p-6 sm:pt-4",
          "sm:bottom-auto sm:top-1/2 sm:-translate-y-1/2 sm:rounded-sheet",
        )}
      >
        <div className="mb-2 flex items-center justify-between gap-3">
          {title ? <h2 className="font-display text-lg font-semibold">{title}</h2> : <span />}
          {onClose && (
            <button
              type="button"
              onClick={onClose}
              aria-label="Đóng"
              className="-mr-1 inline-flex size-9 shrink-0 items-center justify-center rounded-full text-fg-muted hover:bg-primary-soft hover:text-fg"
            >
              <IconClose className="size-5" aria-hidden />
            </button>
          )}
        </div>
        {children}
      </section>
    </>
  );
}
