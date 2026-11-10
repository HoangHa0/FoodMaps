"use client";

import { type KeyboardEvent, useId, useRef, useState } from "react";

import { IconClose, IconSearch, cn } from "@/ui";

import type { MapPlace } from "@/features/map";

import { highlightParts } from "../lib/listing";

export interface PlaceSuggestion {
  place: MapPlace;
  icon: string;
  /** hidden by another filter (category, price, rating): picking it clears those filters */
  outside: boolean;
}

/**
 * Search field for place NAMES (not the AI search), as a combobox:
 *   - typing filters the pins and the list live, and shows up to 6 places under the field
 *   - ↑ ↓ move through them, Enter opens the highlighted place, Esc closes the list (then clears)
 *   - the last row keeps the plain filter: "Xem cả N kết quả trong danh sách"
 * Only UI state lives here (open, highlighted row); the places come from the container.
 */
export function PlaceSearchBox({
  query,
  onQuery,
  suggestions,
  matchCount,
  onPick,
  className,
}: {
  query: string;
  onQuery: (q: string) => void;
  suggestions: PlaceSuggestion[];
  /** how many places the text matches (all of them are in the list below) */
  matchCount: number;
  onPick: (placeId: string) => void;
  className?: string;
}) {
  const listId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1); // -1: nothing highlighted
  const hasText = query.trim().length > 0;
  const showList = open && hasText;
  const optionId = (i: number) => `${listId}-opt-${i}`;

  function pick(i: number) {
    const s = suggestions[i];
    if (!s) return;
    onPick(s.place.place_id);
    setOpen(false);
    setActive(-1);
    inputRef.current?.blur(); // phones: hide the keyboard so the map and the details show
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    const n = suggestions.length;
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!showList) setOpen(true);
      if (n === 0) return;
      const step = e.key === "ArrowDown" ? 1 : -1;
      setActive((i) => (i < 0 ? (step > 0 ? 0 : n - 1) : (i + step + n) % n));
    } else if (e.key === "Enter") {
      e.preventDefault(); // never submit a surrounding form
      if (showList && active >= 0) pick(active);
      else setOpen(false); // Enter with nothing highlighted: keep the text as a filter
    } else if (e.key === "Escape") {
      if (showList) {
        e.preventDefault();
        setOpen(false);
        setActive(-1);
      } else if (hasText) {
        e.preventDefault();
        onQuery("");
      }
    } else if (e.key === "Tab") {
      setOpen(false);
    }
  }

  return (
    <div className={cn("relative min-w-0", className)}>
      <IconSearch className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-fg-muted" aria-hidden />
      <input
        ref={inputRef}
        type="text"
        role="combobox"
        aria-label="Tìm quán theo tên hoặc địa chỉ"
        aria-autocomplete="list"
        aria-expanded={showList}
        aria-controls={listId}
        aria-activedescendant={showList && active >= 0 ? optionId(active) : undefined}
        autoComplete="off"
        spellCheck={false}
        enterKeyHint="search"
        value={query}
        onChange={(e) => {
          onQuery(e.target.value);
          setOpen(true);
          setActive(-1);
        }}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onKeyDown={onKeyDown}
        placeholder="Tìm quán theo tên, địa chỉ…"
        className="h-10 w-full rounded-control border border-border bg-surface pl-10 pr-10 text-sm text-fg shadow-card outline-none transition ease-standard focus:ring-2 focus:ring-primary"
        data-testid="place-filter"
      />
      {hasText && (
        <button
          type="button"
          onMouseDown={(e) => e.preventDefault()} // keep the focus in the field
          onClick={() => {
            onQuery("");
            setActive(-1);
            inputRef.current?.focus();
          }}
          aria-label="Xoá chữ tìm kiếm"
          className="absolute right-1.5 top-1/2 inline-flex size-7 -translate-y-1/2 items-center justify-center rounded-full text-fg-muted hover:bg-primary-soft hover:text-fg"
        >
          <IconClose className="size-4" aria-hidden />
        </button>
      )}

      <div
        className={cn(
          "absolute inset-x-0 top-full z-30 mt-1.5 overflow-hidden rounded-card border border-border bg-surface-raised shadow-sheet",
          !showList && "hidden",
        )}
        // a press inside the list must not blur the field before the click lands
        onMouseDown={(e) => e.preventDefault()}
      >
        <ul id={listId} role="listbox" aria-label="Gợi ý quán" className="max-h-80 overflow-y-auto py-1">
          {suggestions.map((s, i) => (
            <li
              key={s.place.place_id}
              id={optionId(i)}
              role="option"
              aria-selected={i === active}
              onClick={() => pick(i)}
              onMouseMove={() => setActive(i)}
              className={cn("flex cursor-pointer items-center gap-3 px-3 py-2", i === active && "bg-primary-soft")}
              data-testid="place-suggestion"
            >
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary-soft text-lg" aria-hidden>
                {s.icon}
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate text-sm text-fg">
                  {highlightParts(s.place.name, query).map((part, k) =>
                    part.match ? (
                      <strong key={k} className="font-extrabold">
                        {part.text}
                      </strong>
                    ) : (
                      <span key={k}>{part.text}</span>
                    ),
                  )}
                </span>
                <span className="block truncate text-xs text-fg-muted">
                  {[s.place.category, s.place.address].filter(Boolean).join(" · ")}
                </span>
              </span>
              {s.outside && (
                <span className="shrink-0 rounded-control bg-surface px-2 py-0.5 text-xs text-fg-muted" title="Quán này đang bị bộ lọc khác ẩn">
                  ngoài bộ lọc
                </span>
              )}
            </li>
          ))}
        </ul>
        {suggestions.length === 0 ? (
          <p className="px-4 py-3 text-sm text-fg-muted" role="status">
            Không có quán nào khớp “{query.trim()}”. Thử tên khác, hoặc dùng tìm kiếm AI để mô tả điều bạn muốn.
          </p>
        ) : (
          <button
            type="button"
            onClick={() => {
              setOpen(false);
              document.getElementById("place-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
            }}
            className="flex w-full items-center justify-between gap-2 border-t border-border px-4 py-2.5 text-left text-sm font-semibold text-fg hover:bg-primary-soft"
          >
            Xem cả {matchCount} kết quả trong danh sách
            <span aria-hidden>↓</span>
          </button>
        )}
      </div>
    </div>
  );
}
