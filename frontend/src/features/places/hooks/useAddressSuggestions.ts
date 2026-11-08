"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { geoApi } from "../api";

const MIN_CHARS = 2; // below this the server returns nothing, so no request is made
const DEBOUNCE_MS = 300;

/** The value of `text` once it has stayed unchanged for `ms`. */
function useDebounced(text: string, ms: number): string {
  const [settled, setSettled] = useState(text);
  useEffect(() => {
    const t = setTimeout(() => setSettled(text), ms);
    return () => clearTimeout(t);
  }, [text, ms]);
  return settled;
}

/**
 * Address suggestions for what the user is typing: waits 300 ms after the last key, asks the backend,
 * keeps the previous list on screen while the next one loads, and caches each text for 5 minutes.
 * An error (e.g. the server has no VietMap key) arrives as a ready-to-show message.
 */
export function useAddressSuggestions(text: string) {
  const typed = text.trim();
  const settled = useDebounced(typed, DEBOUNCE_MS);
  const enabled = settled.length >= MIN_CHARS;

  const query = useQuery({
    queryKey: ["geo", "suggest", settled],
    queryFn: ({ signal }) => geoApi.suggest(settled, signal),
    enabled,
    staleTime: 5 * 60_000,
    retry: false,
    placeholderData: keepPreviousData,
  });

  return {
    /** The user typed enough to expect a list. */
    active: typed.length >= MIN_CHARS,
    suggestions: query.data,
    /** Waiting for the debounce or for the answer. */
    searching: typed.length >= MIN_CHARS && (settled !== typed || query.isFetching),
    error: query.error?.message,
  };
}
