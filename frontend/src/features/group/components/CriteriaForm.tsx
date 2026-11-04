"use client";

import { type FormEvent, useState } from "react";

import { useCurrentPosition } from "@/lib/geolocation";
import { Button, Chip, IconLocate, Input } from "@/ui";

import type { Criteria } from "../api";

/** Quick mood suggestions. Replace with M3's shared MoodChips once it exists. */
const MOODS = ["Ăn tối cùng nhóm", "Cà phê ngồi lâu", "Đồ nướng", "Ăn khuya", "Trà sữa", "Món chay"];
const BUDGETS: { label: string; max: number | null }[] = [
  { label: "Dưới 50k", max: 50_000 },
  { label: "Dưới 100k", max: 100_000 },
  { label: "Dưới 200k", max: 200_000 },
  { label: "Không giới hạn", max: null },
];
const RADII = [500, 1000, 2000, 5000];

const radiusLabel = (m: number) => (m < 1000 ? `${m} m` : `${m / 1000} km`);

/**
 * Host-only form, shown in a Sheet. The container decides what onSubmit does.
 * "Khu vực" = the host's position + a radius. Without a position the radius means nothing to the
 * backend (it filters by distance from `origin` only), so the radius chips appear only after the
 * position is known.
 */
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
  const { position, request, clear } = useCurrentPosition();
  const origin = position.status === "ok" ? position.point : null;

  function submit(e: FormEvent) {
    e.preventDefault();
    if (!mood.trim()) return;
    onSubmit({ mood: mood.trim(), origin, radius_m: radius, price_max: priceMax, categories: [] });
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
        <legend className="mb-1 text-sm font-medium">Khu vực</legend>
        <div className="flex flex-wrap gap-2">
          <Chip
            selected={!!origin}
            icon={<IconLocate className="size-4" aria-hidden />}
            onClick={() => (origin ? clear() : request())}
            disabled={position.status === "loading"}
          >
            {position.status === "loading" ? "Đang lấy vị trí…" : "Gần vị trí của tôi"}
          </Chip>
          {origin &&
            RADII.map((r) => (
              <Chip key={r} selected={radius === r} onClick={() => setRadius(r)}>
                {radiusLabel(r)}
              </Chip>
            ))}
        </div>
        {position.status === "error" && <p className="text-sm text-warning">{position.message}</p>}
        {!origin && position.status !== "error" && (
          <p className="text-sm text-fg-muted">Không chọn: tìm ở mọi khu vực.</p>
        )}
      </fieldset>

      {error && <p className="text-sm text-danger">{error}</p>}
      <Button type="submit" size="lg" fullWidth loading={loading} disabled={!mood.trim()}>
        Bắt đầu bình chọn
      </Button>
    </form>
  );
}
