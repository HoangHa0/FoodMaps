"use client";

import { type FormEvent, useState } from "react";

import { Button, Chip, Input } from "@/ui";

import type { Criteria } from "../api";

/** Quick mood suggestions. Replace with M3's shared MoodChips once it exists. */
const MOODS = ["Ăn tối cùng nhóm", "Cà phê ngồi lâu", "Đồ nướng", "Ăn khuya", "Trà sữa", "Món chay"];
const BUDGETS: { label: string; max: number | null }[] = [
  { label: "Dưới 50k", max: 50_000 },
  { label: "Dưới 100k", max: 100_000 },
  { label: "Dưới 200k", max: 200_000 },
  { label: "Không giới hạn", max: null },
];
const RADII = [1000, 2000, 5000];

/** Host-only form, shown in a Sheet. Pure view: the container decides what onSubmit does. */
export function CriteriaForm({
  onSubmit,
  loading,
  error,
}: {
  onSubmit: (c: Criteria) => void;
  loading?: boolean;
  error?: string;
}) {
  const [mood, setMood] = useState("");
  const [priceMax, setPriceMax] = useState<number | null>(100_000);
  const [radius, setRadius] = useState(2000);

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!mood.trim()) return;
    onSubmit({ mood: mood.trim(), radius_m: radius, price_max: priceMax, categories: [] });
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={submit}>
      <Input
        label="Cả nhóm muốn gì?"
        name="mood"
        maxLength={300}
        placeholder="VD: quán nướng rộng rãi, ngồi đông người"
        value={mood}
        onChange={(e) => setMood(e.target.value)}
      />
      <div className="flex flex-wrap gap-2">
        {MOODS.map((m) => (
          <Chip key={m} selected={mood === m} onClick={() => setMood(m)}>
            {m}
          </Chip>
        ))}
      </div>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-1 text-sm font-medium">Ngân sách mỗi người</legend>
        <div className="flex flex-wrap gap-2">
          {BUDGETS.map((b) => (
            <Chip key={b.label} selected={priceMax === b.max} onClick={() => setPriceMax(b.max)}>
              {b.label}
            </Chip>
          ))}
        </div>
      </fieldset>

      <fieldset className="flex flex-col gap-2">
        <legend className="mb-1 text-sm font-medium">Bán kính</legend>
        <div className="flex flex-wrap gap-2">
          {RADII.map((r) => (
            <Chip key={r} selected={radius === r} onClick={() => setRadius(r)}>
              {r / 1000} km
            </Chip>
          ))}
        </div>
      </fieldset>

      {error && <p className="text-sm text-danger">{error}</p>}
      <Button type="submit" size="lg" fullWidth loading={loading} disabled={!mood.trim()}>
        Bắt đầu bình chọn
      </Button>
    </form>
  );
}
