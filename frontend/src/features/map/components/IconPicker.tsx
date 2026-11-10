"use client";

import { useState } from "react";

import { cn } from "@/ui";

const PRESETS = ["❤️", "⭐", "☕", "🧋", "🍜", "🍲", "🍕", "🍣", "🍰", "🍺", "🥗", "🔥", "🎉", "📌"];

type Segmenter = new (
  locale?: string,
  options?: { granularity: "grapheme" },
) => { segment(text: string): Iterable<{ segment: string }> };

/** First visible character of what was typed (an emoji such as ❤️ is several code points). */
function firstGrapheme(text: string): string {
  const Seg = (Intl as unknown as { Segmenter?: Segmenter }).Segmenter;
  if (!Seg) return Array.from(text)[0] ?? "";
  for (const part of new Seg(undefined, { granularity: "grapheme" }).segment(text)) return part.segment;
  return "";
}

/** Ready-made icons plus a box to type any other emoji. */
export function IconPicker({ value, onChange }: { value: string; onChange: (icon: string) => void }) {
  const [custom, setCustom] = useState("");

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-1.5" role="radiogroup" aria-label="Chọn icon">
        {PRESETS.map((icon) => (
          <button
            key={icon}
            type="button"
            role="radio"
            aria-checked={value === icon}
            onClick={() => onChange(icon)}
            className={cn(
              "grid size-9 place-items-center rounded-control text-xl transition ease-standard",
              value === icon ? "bg-primary-soft ring-2 ring-primary" : "bg-surface hover:bg-primary-soft",
            )}
          >
            {icon}
          </button>
        ))}
      </div>
      <label className="flex items-center gap-2 text-sm text-fg-muted">
        Hoặc nhập emoji khác
        <input
          value={custom}
          onChange={(event) => {
            const icon = firstGrapheme(event.target.value);
            setCustom(icon);
            if (icon) onChange(icon);
          }}
          aria-label="Nhập emoji khác"
          className="h-9 w-14 rounded-control border border-border bg-surface-raised text-center text-xl outline-none focus:ring-2 focus:ring-primary"
        />
      </label>
    </div>
  );
}