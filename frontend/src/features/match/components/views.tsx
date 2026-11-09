"use client";

/**
 * AI Match views: props in, markup out, built from @/ui. No API calls here; the only local state
 * is the search form itself (text, options, the device position it may ask for).
 */
import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import { type PositionState, useCurrentPosition } from "@/lib/geolocation";
import {
  Badge,
  BottomSheet,
  Button,
  Card,
  Chip,
  cn,
  IconButton,
  IconClose,
  IconDirections,
  IconFilters,
  IconHeart,
  IconLocate,
  IconNotMatch,
  IconSparkles,
  IconWrite,
  IconPin,
  SearchInput,
  Spinner,
} from "@/ui";

import type { MatchCriteria, MatchResult, RejectReason, WhyOut } from "../api";
import {
  addChip,
  BUDGETS,
  budgetIndex,
  DEFAULT_RADIUS,
  EMPTY_MESSAGE,
  EMPTY_MESSAGE_AFTER,
  MOOD_CHIPS,
  RADII,
  radiusLabel,
  REJECT_REASONS,
} from "../lib/options";

// --------------------------------------------------------------------------- collapsed search bar

/** Search bar of the desktop top bar. Phones and tablets use the round button of the tab bar. */
export function SearchTrigger({ onOpen }: { onOpen: () => void }) {
  return (
    <SearchInput
      label="Tìm quán bằng AI"
      placeholder="Hôm nay bạn muốn ăn gì? Mô tả để AI tìm quán…"
      readOnly
      onFocus={onOpen}
      onClick={onOpen}
      onSearch={onOpen}
      className="hidden w-full max-w-154 cursor-pointer lg:flex"
      data-testid="match-trigger"
    />
  );
}

// --------------------------------------------------------------------------- overlay

/** Full-screen search: mood sentence, quick chips, options (area, budget), big CTA. */
export function MatchOverlay({
  initial,
  onSubmit,
  onClose,
  loading,
  error,
}: {
  initial?: MatchCriteria;
  onSubmit: (c: MatchCriteria) => void;
  onClose: () => void;
  loading?: boolean;
  error?: string;
}) {
  const [mood, setMood] = useState(initial?.mood ?? "");
  const [budget, setBudget] = useState(budgetIndex(initial?.price_min, initial?.price_max));
  const [radius, setRadius] = useState(initial?.radius_m ?? DEFAULT_RADIUS);
  const [optionsOpen, setOptionsOpen] = useState(false);
  const { position, request, clear } = useCurrentPosition();
  const origin = position.status === "ok" ? position.point : null;
  const textRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    textRef.current?.focus();
    const onKey = (e: globalThis.KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function submit(e?: FormEvent) {
    e?.preventDefault();
    if (!mood.trim() || loading) return;
    const b = BUDGETS[budget];
    onSubmit({ mood: mood.trim(), origin, radius_m: radius, price_min: b.min, price_max: b.max, categories: [] });
  }

  // Enter searches, Shift+Enter adds a new line
  function onTextKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  }

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-bg" role="dialog" aria-modal aria-label="Tìm quán bằng AI">
      <form className="mx-auto flex w-full max-w-2xl flex-col gap-5 px-4 py-6 sm:py-10" onSubmit={submit}>
        <div className="flex items-center justify-between gap-3">
          <h1 className="font-display text-2xl font-bold">Hôm nay ăn gì?</h1>
          <IconButton label="Đóng" icon={<IconClose className="size-5" />} onClick={onClose} />
        </div>

        <label className="flex flex-col gap-2">
          <span className="text-sm text-fg-muted">Mô tả tâm trạng, dịp hay món bạn đang thèm</span>
          <textarea
            ref={textRef}
            name="mood"
            rows={3}
            maxLength={300}
            value={mood}
            onChange={(e) => setMood(e.target.value)}
            onKeyDown={onTextKey}
            placeholder="Hôm nay mình muốn ăn gì đó nhẹ nhàng, ngồi một mình..."
            className="w-full resize-none rounded-card border border-border bg-surface-raised p-4 text-base outline-none focus:ring-2 focus:ring-primary"
            data-testid="match-mood"
          />
        </label>

        <div className="flex flex-wrap gap-2" aria-label="Gợi ý nhanh">
          {MOOD_CHIPS.map((c) => (
            <Chip key={c} onClick={() => setMood((m) => addChip(m, c))}>
              {c}
            </Chip>
          ))}
        </div>

        <div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setOptionsOpen((o) => !o)}
            aria-expanded={optionsOpen}
            type="button"
          >
            <IconFilters className="size-4" aria-hidden /> Tuỳ chọn
          </Button>
          {optionsOpen && (
            <div className="mt-3 flex flex-col gap-4">
              <AreaOptions
                position={position}
                hasOrigin={!!origin}
                onToggle={() => (origin ? clear() : request())}
                radius={radius}
                onRadius={setRadius}
              />
              <fieldset className="flex flex-col gap-2">
                <legend className="mb-1 text-sm font-semibold">Khoảng giá mỗi người</legend>
                <div className="flex flex-wrap gap-2">
                  {BUDGETS.map((b, i) => (
                    <Chip key={b.label} selected={budget === i} onClick={() => setBudget(i)}>
                      {b.label}
                    </Chip>
                  ))}
                </div>
              </fieldset>
            </div>
          )}
        </div>

        {error && <p className="text-sm text-danger">{error}</p>}
        <Button type="submit" size="lg" fullWidth loading={loading} disabled={!mood.trim()} data-testid="match-submit">
          <IconSparkles className="size-5" aria-hidden /> Tìm quán cho mình
        </Button>
      </form>
    </div>
  );
}

function AreaOptions({
  position,
  hasOrigin,
  onToggle,
  radius,
  onRadius,
}: {
  position: PositionState;
  hasOrigin: boolean;
  onToggle: () => void;
  radius: number;
  onRadius: (m: number) => void;
}) {
  return (
    <fieldset className="flex flex-col gap-2">
      <legend className="mb-1 text-sm font-semibold">Điểm xuất phát & bán kính</legend>
      <div className="flex flex-wrap gap-2">
        <Chip
          selected={hasOrigin}
          icon={<IconLocate className="size-4" aria-hidden />}
          onClick={onToggle}
          disabled={position.status === "loading"}
        >
          {position.status === "loading" ? "Đang lấy vị trí…" : "Vị trí của tôi"}
        </Chip>
        {hasOrigin &&
          RADII.map((r) => (
            <Chip key={r} selected={radius === r} onClick={() => onRadius(r)}>
              {radiusLabel(r)}
            </Chip>
          ))}
      </div>
      {position.status === "error" ? (
        <p className="text-sm text-warning">{position.message}</p>
      ) : (
        !hasOrigin && <p className="text-sm text-fg-muted">Không chọn: tìm ở mọi khu vực.</p>
      )}
    </fieldset>
  );
}

// --------------------------------------------------------------------------- result sheet

/** Draggable bottom sheet over the map: one place + why + actions (spec 1.3). */
export function MatchResultSheet({
  result,
  backupsLeft,
  emptyAfter,
  why,
  whyLoading,
  directionsUrl,
  onClose,
  onSearchAgain,
  onReject,
  rejecting,
  rejectError,
  onWriteReview,
  onShowOnMap,
  saved,
  onToggleSave,
}: {
  result: MatchResult | null;
  backupsLeft: number;
  emptyAfter?: RejectReason;
  why: WhyOut | undefined;
  whyLoading: boolean;
  directionsUrl: string;
  onClose: () => void;
  onSearchAgain: () => void;
  onReject: (reason: RejectReason) => void;
  rejecting: boolean;
  rejectError?: string;
  onWriteReview: () => void;
  onShowOnMap: () => void;
  saved: boolean;
  onToggleSave: () => void;
}) {
  const [askReason, setAskReason] = useState(false);
  // a new place arrived (after "Không hợp"): hide the reasons again
  const [shownId, setShownId] = useState(result?.place_id);
  if (shownId !== result?.place_id) {
    setShownId(result?.place_id);
    setAskReason(false);
  }

  return (
    <BottomSheet
      label="Kết quả tìm quán"
      resetKey={result?.place_id ?? "empty"}
      peekHeight={112}
      className="sm:max-w-xl"
      data-testid="match-result"
    >
      {result === null ? (
        <div className="flex flex-col gap-3 text-center">
          <div className="flex justify-end">
            <IconButton label="Đóng" variant="plain" icon={<IconClose className="size-5" />} onClick={onClose} />
          </div>
          <h2 className="font-display text-xl font-semibold">Chưa tìm được quán hợp</h2>
          <p className="text-fg-muted" data-testid="match-empty">
            {(emptyAfter && EMPTY_MESSAGE_AFTER[emptyAfter]) ?? EMPTY_MESSAGE}
          </p>
          <Button onClick={onSearchAgain}>Tìm lại</Button>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div className="flex items-start gap-3">
            <div className="min-w-0 flex-1">
              <h2 className="font-display text-xl font-bold" data-testid="match-name">
                {result.name ?? "Quán phù hợp nhất"}
              </h2>
              {/* One line of facts under the name: distance (only with an origin) · public rating.
                  The Why box keeps the price; it does not repeat the distance or the rating. */}
              <p className="mt-1 text-sm text-fg-muted" data-testid="match-meta">
                {[
                  result.distance_m != null ? `📍 Cách ${formatDistance(result.distance_m)}` : null,
                  result.avg_rating != null && result.review_count > 0
                    ? `★ ${result.avg_rating.toFixed(1)} (${result.review_count} đánh giá)`
                    : "Chưa có đánh giá",
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </p>
            </div>
            <Badge tone="accent">Hợp {Math.round(result.match_score * 100)}%</Badge>
            <IconButton label="Đóng" variant="plain" icon={<IconClose className="size-5" />} onClick={onClose} />
          </div>

          {(result.tags ?? []).length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {(result.tags ?? []).map((t) => (
                <Badge key={t}>{t}</Badge>
              ))}
            </div>
          )}

          <WhyBox
            why={why}
            loading={whyLoading}
            reasons={(result.reasons ?? []).filter((reason) => !reason.startsWith("⭐ ") && !reason.startsWith("📍 "))}
          />

          <div className="grid grid-cols-3 gap-2">
            <a
              href={directionsUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-10 items-center justify-center gap-1.5 whitespace-nowrap rounded-control bg-primary px-2 text-sm font-bold text-primary-fg shadow-card"
            >
              <IconDirections className="size-4" aria-hidden /> Chỉ đường
            </a>
            <Button variant="secondary" onClick={onToggleSave} aria-pressed={saved} className="whitespace-nowrap px-2 text-sm">
              <IconHeart className={cn("size-4", saved && "fill-accent text-accent")} aria-hidden /> {saved ? "Đã lưu" : "Lưu"}
            </Button>
            <Button
              variant="secondary"
              onClick={() => setAskReason((a) => !a)}
              aria-expanded={askReason}
              className="whitespace-nowrap px-2 text-sm"
              data-testid="match-reject"
            >
              <IconNotMatch className="size-4" aria-hidden /> Không hợp
            </Button>
          </div>

          {askReason && (
            <div className="flex flex-col gap-2" aria-label="Lý do không hợp">
              <p className="text-sm font-semibold">Chưa hợp vì…</p>
              <div className="flex flex-wrap gap-2">
                {REJECT_REASONS.map((r) => (
                  <Chip key={r.reason} disabled={rejecting} onClick={() => onReject(r.reason)}>
                    {r.label}
                  </Chip>
                ))}
                {rejecting && <Spinner size="sm" />}
              </div>
              {rejectError && <p className="text-sm text-danger">{rejectError}</p>}
            </div>
          )}

          <p className="-mt-2 text-xs text-fg-muted">
            {backupsLeft > 0
              ? `Còn ${backupsLeft} quán dự phòng: bấm “Không hợp” để xem quán tiếp theo.`
              : "Đây là quán cuối cùng khớp tiêu chí."}
          </p>

          <div className="flex flex-wrap items-center justify-between gap-1 border-t border-border pt-3">
            <div className="flex flex-wrap gap-1">
              <Button variant="ghost" size="sm" onClick={onShowOnMap}>
                <IconPin className="size-4" aria-hidden /> Xem trên bản đồ
              </Button>
              <Button variant="ghost" size="sm" onClick={onWriteReview}>
                <IconWrite className="size-4" aria-hidden /> Viết đánh giá
              </Button>
            </div>
            <Button variant="ghost" size="sm" onClick={onSearchAgain}>
              <IconSparkles className="size-4" aria-hidden /> Tìm lại
            </Button>
          </div>
        </div>
      )}
    </BottomSheet>
  );
}

/** "✨ Vì sao hợp với bạn?": bullets from the reviews (M3) + the score reasons (distance, price, rating). */
function WhyBox({ why, loading, reasons }: { why: WhyOut | undefined; loading: boolean; reasons: string[] }) {
  const points = why?.points ?? [];
  if (!loading && points.length === 0 && reasons.length === 0) return null;
  return (
    <Card className="flex flex-col gap-2 bg-primary-soft" data-testid="match-why">
      <h3 className="flex items-center gap-2 font-semibold">
        <IconSparkles className="size-4" aria-hidden /> Vì sao hợp với bạn?
      </h3>
      {loading && <Spinner size="sm" />}
      <ul className="flex list-disc flex-col gap-1 pl-5 text-sm">
        {points.map((p) => (
          <li key={p.text} className={cn(p.matched && "font-semibold")}>
            {p.text}
          </li>
        ))}
        {reasons.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
    </Card>
  );
}

const formatDistance = (m: number) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`);
