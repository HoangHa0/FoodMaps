"use client";

import { type KeyboardEvent, useId, useState } from "react";

import { Button, Chip, cn, Input } from "@/ui";

import {
  addTags,
  hasTag,
  MAX_TAG_LENGTH,
  MAX_TAGS,
  parseTags,
  removeTag,
  SUITABLE_PRESETS,
} from "../lib/validation";

/**
 * "Hợp với" as chips: tap a quick choice to select or unselect it, or type your own tag.
 * Tags already saved in an old review (including custom ones) show up as selected chips,
 * so editing a review never drops them.
 */
export function SuitableForPicker({
  value,
  onChange,
  error,
}: {
  value: string[];
  onChange: (tags: string[]) => void;
  error?: string;
}) {
  const labelId = useId();
  const [draft, setDraft] = useState("");
  const full = value.length >= MAX_TAGS;
  const custom = value.filter((t) => !hasTag(SUITABLE_PRESETS, t));

  const toggle = (tag: string) => onChange(hasTag(value, tag) ? removeTag(value, tag) : addTags(value, [tag]));

  function commitDraft() {
    const tags = parseTags(draft);
    if (tags.length === 0) return;
    onChange(addTags(value, tags));
    setDraft("");
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key !== "Enter") return;
    e.preventDefault(); // Enter adds the tag; it must not submit the review
    commitDraft();
  }

  return (
    <div role="group" aria-labelledby={labelId} className="flex flex-col gap-2">
      <span id={labelId} className="text-sm font-semibold">
        Hợp với
      </span>
      <div className="flex flex-wrap gap-2">
        {[...SUITABLE_PRESETS, ...custom].map((tag) => {
          const selected = hasTag(value, tag);
          return (
            <Chip
              key={tag}
              selected={selected}
              disabled={!selected && full}
              onClick={() => toggle(tag)}
              // Selected chips use the same colour as the "Đăng review" button. Chip is plain clsx
              // (no class merging), so "!" makes these win over its default dark selected style.
              className={cn(
                "disabled:pointer-events-none disabled:opacity-50",
                selected && "bg-primary! text-primary-fg! hover:brightness-95",
              )}
            >
              {tag}
            </Chip>
          );
        })}
      </div>
      <div className="flex items-start gap-2">
        <div className="flex-1">
          <Input
            aria-label="Thêm ý khác"
            placeholder="Thêm ý khác, ví dụ: sinh nhật"
            value={draft}
            maxLength={MAX_TAG_LENGTH}
            disabled={full}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKeyDown}
            hint={full ? `Đã chọn tối đa ${MAX_TAGS} mục` : undefined}
            error={error}
          />
        </div>
        <Button type="button" variant="secondary" className="h-11" disabled={full || !draft.trim()} onClick={commitDraft}>
          Thêm
        </Button>
      </div>
    </div>
  );
}