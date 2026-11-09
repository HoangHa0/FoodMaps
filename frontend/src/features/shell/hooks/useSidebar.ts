"use client";

import { useCallback, useEffect, useSyncExternalStore } from "react";

import { SIDEBAR } from "../nav";

const STORAGE_KEY = "foodmaps.sidebar";

interface SidebarState {
  collapsed: boolean;
  width: number;
}

const DEFAULT: SidebarState = { collapsed: false, width: SIDEBAR.default };

// A tiny store: the state lives here (read once from localStorage), components subscribe to it.
let current: SidebarState | null = null;
const listeners = new Set<() => void>();

function load(): SidebarState {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT;
    const v = JSON.parse(raw) as Partial<SidebarState>;
    const width = typeof v.width === "number" ? Math.min(SIDEBAR.max, Math.max(SIDEBAR.min, v.width)) : SIDEBAR.default;
    return { collapsed: v.collapsed === true, width };
  } catch {
    return DEFAULT; // private mode, blocked storage, bad JSON
  }
}

function getSnapshot(): SidebarState {
  current ??= load();
  return current;
}

function setState(next: (s: SidebarState) => SidebarState) {
  current = next(getSnapshot());
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(current));
  } catch {
    // not persisted: still works for this visit
  }
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

/** Collapsed / width of the desktop sidebar, remembered per browser. Ctrl+B (⌘B) toggles it. */
export function useSidebar() {
  const state = useSyncExternalStore(subscribe, getSnapshot, () => DEFAULT);

  const toggle = useCallback(() => setState((s) => ({ ...s, collapsed: !s.collapsed })), []);
  const resize = useCallback(
    (w: number | "collapse") => setState((s) => (w === "collapse" ? { ...s, collapsed: true } : { collapsed: false, width: w })),
    [],
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && !e.altKey && e.key.toLowerCase() === "b") {
        const t = e.target as HTMLElement | null;
        if (t?.isContentEditable || t?.tagName === "TEXTAREA" || t?.tagName === "INPUT") return; // leave text editing alone
        e.preventDefault();
        toggle();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [toggle]);

  return { ...state, toggle, resize };
}
