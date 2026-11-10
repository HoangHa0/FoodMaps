"use client";

/**
 * Origin picker view: props in, markup out, built from @/ui. No API calls, no browser APIs and no state
 * here: the container (OriginPicker.tsx) owns them.
 */
import type { KeyboardEvent } from "react";

import { Chip, IconClose, IconLocate, Spinner } from "@/ui";

import type { GeoSuggestion } from "../api";
import { DISTRICTS } from "../lib/districts";
import { MY_LOCATION_LABEL, type Origin, radiusLabel } from "../lib/origin";

export interface OriginPickerViewProps {
  legend: string;
  value: Origin | null;
  radius: number;
  radii: readonly number[];
  onRadius: (m: number) => void;
  /** Clears the chosen starting point (back to "search everywhere"). */
  onClear: () => void;

  onLocate: () => void;
  locating: boolean;
  locateError?: string;

  onDistrict: (name: string) => void;

  text: string;
  onText: (t: string) => void;
  /** The user typed enough to expect a list. */
  suggestionsActive: boolean;
  suggestions: GeoSuggestion[] | undefined;
  searching: boolean;
  searchError?: string;
  onSuggestion: (s: GeoSuggestion) => void;
  /** A picked suggestion is being turned into coordinates. */
  resolving: boolean;
  resolveError?: string;
}

export function OriginPickerView(p: OriginPickerViewProps) {
  return (
    <fieldset className="flex flex-col gap-2" data-testid="origin-picker">
      <legend className="mb-1 text-sm font-semibold">{p.legend}</legend>
      {p.value ? <ChosenOrigin {...p} value={p.value} /> : <ChooseOrigin {...p} />}
    </fieldset>
  );
}

/** A starting point is set: one chip to remove it, then the radius. */
function ChosenOrigin({ value, radius, radii, onRadius, onClear }: OriginPickerViewProps & { value: Origin }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Chip selected icon={<IconLocate className="size-4" aria-hidden />} onClick={onClear} data-testid="origin-chosen">
        <span className="max-w-56 truncate">{value.label}</span>
        <IconClose className="size-3.5" aria-label="Bỏ điểm xuất phát" />
      </Chip>
      {radii.map((r) => (
        <Chip key={r} selected={radius === r} onClick={() => onRadius(r)}>
          {radiusLabel(r)}
        </Chip>
      ))}
    </div>
  );
}

/** No starting point yet: my location + quick districts, and a field for any other address. */
function ChooseOrigin(p: OriginPickerViewProps) {
  const typing = p.text.trim().length > 0;

  // Enter picks the first suggestion and must NOT submit the form around the picker.
  // Escape clears the text first (a second Escape then closes the overlay or sheet).
  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter") {
      e.preventDefault();
      const first = p.suggestions?.[0];
      if (first && p.suggestionsActive && !p.resolving) p.onSuggestion(first);
    } else if (e.key === "Escape" && p.text) {
      e.preventDefault();
      e.nativeEvent.stopPropagation();
      p.onText("");
    }
  }

  return (
    <>
      {/* one row that scrolls sideways on a phone, wraps on a wide screen */}
      <div className="flex gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:overflow-visible">
        <Chip
          icon={<IconLocate className="size-4" aria-hidden />}
          onClick={p.onLocate}
          disabled={p.locating}
          className="shrink-0"
        >
          {p.locating ? "Đang lấy vị trí…" : MY_LOCATION_LABEL}
        </Chip>
        {!typing &&
          DISTRICTS.map((d) => (
            <Chip key={d.name} onClick={() => p.onDistrict(d.name)} className="shrink-0">
              {d.name}
            </Chip>
          ))}
      </div>

      {/* same box as the mood field above (rounded-card), so the two inputs look alike */}
      <input
        type="text"
        aria-label="Nhập địa chỉ hoặc khu vực khác"
        placeholder="Hoặc nhập địa chỉ, khu vực khác…"
        value={p.text}
        onChange={(e) => p.onText(e.target.value)}
        onKeyDown={onKeyDown}
        maxLength={100}
        autoComplete="off"
        enterKeyHint="search"
        className="h-12 w-full rounded-card border border-border bg-surface-raised px-4 text-base outline-none focus:ring-2 focus:ring-primary"
        data-testid="origin-input"
      />

      {p.suggestionsActive && <SuggestionList {...p} />}

      {p.locateError && <p className="text-sm text-warning">{p.locateError}</p>}
      {p.resolveError && <p className="text-sm text-warning">{p.resolveError}</p>}
      {!typing && !p.locateError && <p className="text-sm text-fg-muted">Không chọn: tìm ở mọi khu vực.</p>}
    </>
  );
}

function SuggestionList({ suggestions, searching, searchError, onSuggestion, resolving }: OriginPickerViewProps) {
  if (searchError) return <p className="text-sm text-warning">{searchError}</p>;

  const items = suggestions ?? [];
  return (
    <div className="flex flex-col gap-2" aria-live="polite">
      {items.length > 0 && (
        <ul
          className="flex flex-col divide-y divide-border overflow-hidden rounded-card bg-surface-raised shadow-card"
          aria-label="Gợi ý địa điểm"
        >
          {items.map((s) => (
            <li key={s.ref_id}>
              <button
                type="button"
                disabled={resolving}
                onClick={() => onSuggestion(s)}
                className="flex w-full flex-col items-start gap-0.5 px-4 py-2.5 text-left transition ease-standard hover:bg-primary-soft focus-visible:bg-primary-soft focus-visible:outline-none disabled:opacity-60"
              >
                <span className="text-sm font-semibold">{s.name}</span>
                {s.address && <span className="text-xs text-fg-muted">{s.address}</span>}
              </button>
            </li>
          ))}
        </ul>
      )}
      {(searching || resolving) && (
        <p className="flex items-center gap-2 text-sm text-fg-muted">
          <Spinner size="sm" /> {resolving ? "Đang lấy toạ độ…" : "Đang tìm…"}
        </p>
      )}
      {!searching && !resolving && items.length === 0 && (
        <p className="text-sm text-fg-muted">Không thấy địa điểm nào. Thử gõ tên đường hoặc quận khác nhé.</p>
      )}
    </div>
  );
}