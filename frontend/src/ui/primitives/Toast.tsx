"use client";

import Link from "next/link";
import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { cn } from "../cn";
import { IconAlert, IconClose, IconSuccess } from "../icons";
import { Portal } from "./Portal";

export interface ToastOptions {
  tone?: "success" | "error" | "info";
  /** Optional link shown after the message ("Xem"). */
  action?: { label: string; href: string };
}

interface ToastItem extends ToastOptions {
  id: number;
  message: string;
}

type ShowToast = (message: string, options?: ToastOptions) => void;
const ToastContext = createContext<ShowToast | null>(null);

const DURATION_MS = 3500;

/**
 * Short confirmation messages ("Đã lưu quán"), announced to screen readers. Mount the provider once;
 * call `const toast = useToast(); toast("Đã lưu")` anywhere below it.
 * Phones: above the tab bar. Desktop: bottom right.
 */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([]);
  const nextId = useRef(0);

  const dismiss = useCallback((id: number) => setItems((all) => all.filter((t) => t.id !== id)), []);
  const show = useCallback<ShowToast>((message, options) => {
    const id = ++nextId.current;
    setItems((all) => [...all.slice(-2), { id, message, ...options }]); // at most 3 on screen
  }, []);

  const value = useMemo(() => show, [show]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <Portal>
        <div
          aria-live="polite"
          className="pointer-events-none fixed inset-x-3 bottom-[calc(7.25rem+env(safe-area-inset-bottom))] z-60 flex flex-col items-center gap-2 lg:inset-x-auto lg:bottom-6 lg:right-6 lg:items-end"
        >
          {items.map((t) => (
            <ToastView key={t.id} item={t} onDismiss={dismiss} />
          ))}
        </div>
      </Portal>
    </ToastContext.Provider>
  );
}

function ToastView({ item, onDismiss }: { item: ToastItem; onDismiss: (id: number) => void }) {
  useEffect(() => {
    const timer = setTimeout(() => onDismiss(item.id), DURATION_MS);
    return () => clearTimeout(timer);
  }, [item.id, onDismiss]);
  const tone = item.tone ?? "success";
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className="pointer-events-auto flex w-full max-w-sm items-center gap-3 rounded-card bg-fg py-3 pl-4 pr-2 text-sm text-surface shadow-float"
    >
      {tone === "error" ? (
        <IconAlert className="size-5 shrink-0 text-accent" aria-hidden />
      ) : (
        <IconSuccess className={cn("size-5 shrink-0", tone === "success" ? "text-primary" : "text-surface")} aria-hidden />
      )}
      <span className="flex-1">{item.message}</span>
      {item.action && (
        <Link href={item.action.href} onClick={() => onDismiss(item.id)} className="shrink-0 rounded-control px-2 py-1 font-bold text-primary hover:bg-surface/10">
          {item.action.label}
        </Link>
      )}
      <button
        type="button"
        onClick={() => onDismiss(item.id)}
        aria-label="Đóng thông báo"
        className="inline-flex size-8 shrink-0 items-center justify-center rounded-full text-surface/70 hover:bg-surface/10 hover:text-surface"
      >
        <IconClose className="size-4" aria-hidden />
      </button>
    </div>
  );
}

/** Shows a toast. Outside a ToastProvider it does nothing (e.g. in isolated previews). */
export function useToast(): ShowToast {
  return useContext(ToastContext) ?? noop;
}
const noop: ShowToast = () => {};
