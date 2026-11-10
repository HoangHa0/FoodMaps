"use client";

import { useSyncExternalStore } from "react";

import type { JourneyIn, JourneyOut, SharedJourney } from "../api";
import { MAX_STOPS_PER_JOURNEY } from "./limits";
import { hhmm } from "./route";

/**
 * The journey being edited, kept in this browser (localStorage) so that:
 *   - a guest can plan without an account (saving to the account needs login, sharing does not)
 *   - a reload or a visit to another page loses nothing
 *   - "Thêm vào chuyến đi" on the home screen can add a stop from anywhere
 * `rev` counts the edits, so a save that finishes after more edits does not mark them as saved.
 * `journeyId` links the draft to a saved journey (PUT instead of POST); `dirty` = changed since
 * the last save or load.
 */
export interface DraftStop {
  key: string; // stable React key, never sent to the API
  place_id: string;
  planned_time: string; // "HH:MM" or ""
  note: string;
}

export interface Draft {
  journeyId: string | null;
  title: string;
  planned_date: string; // "YYYY-MM-DD" or ""
  stops: DraftStop[];
  dirty: boolean;
  rev: number;
}

const STORAGE_KEY = "foodmaps.journeyDraft";
const EMPTY: Draft = { journeyId: null, title: "", planned_date: "", stops: [], dirty: false, rev: 0 };

let current: Draft | null = null;
const listeners = new Set<() => void>();

const newKey = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : `${Date.now()}-${Math.random()}`;

function load(): Draft {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return EMPTY;
    const d = JSON.parse(raw) as Partial<Draft>;
    return {
      journeyId: typeof d.journeyId === "string" ? d.journeyId : null,
      title: typeof d.title === "string" ? d.title : "",
      planned_date: typeof d.planned_date === "string" ? d.planned_date : "",
      stops: Array.isArray(d.stops)
        ? d.stops
            .filter((s): s is DraftStop => !!s && typeof s.place_id === "string")
            .slice(0, MAX_STOPS_PER_JOURNEY)
            .map((s) => ({ key: s.key || newKey(), place_id: s.place_id, planned_time: s.planned_time ?? "", note: s.note ?? "" }))
        : [],
      dirty: d.dirty === true,
      rev: typeof d.rev === "number" ? d.rev : 0,
    };
  } catch {
    return EMPTY; // blocked storage or bad JSON: start empty
  }
}

function getSnapshot(): Draft {
  current ??= load();
  return current;
}

function set(next: Draft) {
  current = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // not persisted: still works until the page is closed
  }
  listeners.forEach((l) => l());
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) {
      current = load(); // edited in another tab
      listener();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", onStorage);
  };
}

const edit = (change: (d: Draft) => Partial<Draft>) => {
  const d = getSnapshot();
  set({ ...d, ...change(d), dirty: true, rev: d.rev + 1 });
};

/** Every change the planner can make. All of them mark the draft as changed. */
export const draftActions = {
  setTitle: (title: string) => edit(() => ({ title })),
  setDate: (planned_date: string) => edit(() => ({ planned_date })),
  /** false when the journey is full or the place is already in it */
  addStop: (placeId: string): "added" | "duplicate" | "full" => {
    const d = getSnapshot();
    if (d.stops.some((s) => s.place_id === placeId)) return "duplicate";
    if (d.stops.length >= MAX_STOPS_PER_JOURNEY) return "full";
    edit(() => ({ stops: [...d.stops, { key: newKey(), place_id: placeId, planned_time: "", note: "" }] }));
    return "added";
  },
  updateStop: (key: string, patch: Partial<Pick<DraftStop, "planned_time" | "note">>) =>
    edit((d) => ({ stops: d.stops.map((s) => (s.key === key ? { ...s, ...patch } : s)) })),
  removeStop: (key: string) => edit((d) => ({ stops: d.stops.filter((s) => s.key !== key) })),
  moveStop: (key: string, by: -1 | 1) =>
    edit((d) => {
      const i = d.stops.findIndex((s) => s.key === key);
      const j = i + by;
      if (i < 0 || j < 0 || j >= d.stops.length) return {};
      const stops = [...d.stops];
      [stops[i], stops[j]] = [stops[j], stops[i]];
      return { stops };
    }),
  /** Start over (an empty, unsaved journey). */
  reset: () => set(EMPTY),
  /** Open a saved journey from the library. */
  loadSaved: (j: JourneyOut) =>
    set({
      journeyId: j.id,
      title: j.title ?? "",
      planned_date: j.planned_date ?? "",
      stops: j.stops.map((s) => ({ key: newKey(), place_id: s.place.place_id, planned_time: hhmm(s.planned_time), note: s.note ?? "" })),
      dirty: false,
      rev: getSnapshot().rev + 1,
    }),
  /** Copy a shared journey into a new, unsaved draft. */
  copyShared: (j: SharedJourney) =>
    set({
      journeyId: null,
      title: j.title ?? "",
      planned_date: j.planned_date ?? "",
      stops: j.stops.map((s) => ({ key: newKey(), place_id: s.place.place_id, planned_time: hhmm(s.planned_time), note: s.note ?? "" })),
      dirty: true,
      rev: getSnapshot().rev + 1,
    }),
  /**
   * After a successful save of the draft as it was at `savedRev`. Edits made while the request ran
   * are not in the saved journey, so the draft stays "changed" in that case.
   */
  markSaved: (journeyId: string, savedRev: number) => {
    const d = getSnapshot();
    set({ ...d, journeyId, dirty: d.rev !== savedRev });
  },
  /** The saved journey behind the draft was deleted: keep the content, as a new unsaved draft. */
  detach: () => set({ ...getSnapshot(), journeyId: null, dirty: true }),
};

/** What the API expects: blank text is sent as null, the order of `stops` is the order shown. */
export function toJourneyIn(d: Draft): JourneyIn {
  return {
    title: d.title.trim() || null,
    planned_date: d.planned_date || null,
    stops: d.stops.map((s) => ({ place_id: s.place_id, planned_time: s.planned_time || null, note: s.note.trim() || null })),
  };
}

/** The draft, shared by every component that shows or edits it (the server renders an empty one). */
export function useJourneyDraft(): Draft {
  return useSyncExternalStore(subscribe, getSnapshot, () => EMPTY);
}
