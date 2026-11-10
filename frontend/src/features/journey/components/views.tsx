"use client";

/**
 * Food Journey views: props in, markup out. No API calls here (see JourneyScreen / SharedJourneyScreen).
 */
import Link from "next/link";
import { type ReactNode, useState } from "react";

import {
  Button,
  IconButton,
  IconChevronDown,
  IconClose,
  IconDirections,
  IconShare,
  IconTrips,
  cn,
} from "@/ui";

import { NOTE_MAX_LENGTH, TITLE_MAX_LENGTH } from "../lib/limits";
import type { StopView } from "../lib/stops";
import { formatDistance, formatMinutes, walkingMinutes } from "../lib/route";

const vnd = new Intl.NumberFormat("vi-VN");
const dateFmt = new Intl.DateTimeFormat("vi-VN", { weekday: "short", day: "2-digit", month: "2-digit", year: "numeric" });
const shortDate = new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "2-digit", year: "numeric" });

export const formatPlannedDate = (d: string) => (d ? dateFmt.format(new Date(`${d}T00:00:00`)) : "");
export const formatShortDate = (iso: string) => shortDate.format(new Date(iso));

// =========================================================================== header

export type SaveState = "saved" | "changed" | "unsaved" | "empty";

const SAVE_LABEL: Record<SaveState, string> = {
  saved: "Đã lưu vào tài khoản",
  changed: "Có thay đổi chưa lưu",
  unsaved: "Chưa lưu vào tài khoản",
  empty: "",
};

export function JourneyHeader({ saveState, onNew }: { saveState: SaveState; onNew?: () => void }) {
  return (
    <header className="flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="font-display text-3xl font-bold">Chuyến đi ẩm thực</h1>
        <p className="mt-1 text-sm text-fg-muted md:text-base">
          Gom các quán muốn ghé thành một lịch trình, xem quãng đường và chi phí, rồi đi theo chỉ đường.
        </p>
      </div>
      <div className="flex items-center gap-2">
        {saveState !== "empty" && (
          <span
            className={cn(
              "rounded-control px-3 py-1 text-xs font-semibold",
              saveState === "saved" ? "bg-primary-soft text-fg" : "bg-surface text-fg-muted shadow-card",
            )}
            role="status"
          >
            {SAVE_LABEL[saveState]}
          </span>
        )}
        {onNew && (
          <Button variant="secondary" size="sm" onClick={onNew}>
            + Lịch trình mới
          </Button>
        )}
      </div>
    </header>
  );
}

/** "Lịch trình hiện tại có thay đổi chưa lưu…": asked before something replaces the draft. */
export function ReplaceBanner({ message, confirmLabel, onConfirm, onCancel }: { message: string; confirmLabel: string; onConfirm: () => void; onCancel: () => void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-card border border-warning/60 bg-surface p-3 text-sm shadow-card" role="alertdialog" aria-label="Xác nhận">
      <p className="min-w-0 flex-1">{message}</p>
      <div className="flex gap-2">
        <Button size="sm" onClick={onConfirm}>
          {confirmLabel}
        </Button>
        <Button size="sm" variant="secondary" onClick={onCancel}>
          Huỷ
        </Button>
      </div>
    </div>
  );
}

// =========================================================================== editor

const field =
  "h-10 w-full rounded-control border border-border bg-surface-raised px-4 text-sm outline-none transition ease-standard focus:ring-2 focus:ring-primary";

export function MetaFields({
  title,
  onTitle,
  date,
  onDate,
}: {
  title: string;
  onTitle: (v: string) => void;
  date: string;
  onDate: (v: string) => void;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_12rem]">
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-semibold">Tên lịch trình</span>
        <input
          value={title}
          onChange={(e) => onTitle(e.target.value)}
          maxLength={TITLE_MAX_LENGTH}
          placeholder="VD: Cuối tuần ăn sập phố cổ"
          className={field}
          data-testid="journey-title"
        />
      </label>
      <label className="flex flex-col gap-1.5">
        <span className="text-sm font-semibold">Ngày đi</span>
        <input type="date" value={date} onChange={(e) => onDate(e.target.value)} className={field} />
      </label>
    </div>
  );
}

export function EmptyStops() {
  return (
    <div className="flex flex-col items-center gap-2 rounded-card border border-dashed border-border px-4 py-8 text-center">
      <span className="text-3xl" aria-hidden>
        🧭
      </span>
      <p className="font-bold">Chưa có điểm dừng nào</p>
      <p className="max-w-sm text-sm text-fg-muted">
        Tìm quán ở ô phía trên, hoặc bấm “Thêm vào chuyến đi” khi xem một quán trên trang{" "}
        <Link href="/" className="font-semibold text-fg underline">
          Khám phá
        </Link>
        .
      </p>
    </div>
  );
}

/**
 * The stops as a numbered timeline, with the distance to the next stop between two cards.
 * Editable (time, note, move, remove) unless `readOnly`.
 */
export function StopTimeline({
  stops,
  readOnly = false,
  selectedPlaceId,
  onSelect,
  onTime,
  onNote,
  onMove,
  onRemove,
}: {
  stops: StopView[];
  readOnly?: boolean;
  selectedPlaceId?: string | null;
  onSelect?: (placeId: string) => void;
  onTime?: (key: string, v: string) => void;
  onNote?: (key: string, v: string) => void;
  onMove?: (key: string, by: -1 | 1) => void;
  onRemove?: (key: string) => void;
}) {
  return (
    <ol className="flex flex-col" aria-label="Các điểm dừng" data-testid="journey-stops">
      {stops.map((s, i) => {
        const selected = !!s.place && s.place.place_id === selectedPlaceId;
        return (
          <li key={s.key} id={s.place ? `stop-${s.place.place_id}` : undefined} className="scroll-mt-24">
            <div
              className={cn(
                "relative flex gap-3 rounded-card bg-surface-raised p-3 shadow-card transition ease-standard",
                selected && "ring-2 ring-primary",
              )}
            >
              <div className="flex shrink-0 flex-col items-center gap-1.5">
                <span className="grid size-8 place-items-center rounded-full bg-fg text-sm font-extrabold text-surface" aria-label={`Điểm ${i + 1}`}>
                  {i + 1}
                </span>
                <span className="text-lg" aria-hidden>
                  {s.icon}
                </span>
              </div>

              <div className="flex min-w-0 flex-1 flex-col gap-2">
                <div className="flex items-start justify-between gap-2">
                  <button
                    type="button"
                    onClick={() => s.place && onSelect?.(s.place.place_id)}
                    className="min-w-0 text-left"
                    disabled={!s.place || !onSelect}
                  >
                    <span className="block truncate font-bold text-fg">{s.place?.name ?? "Quán không còn trong dữ liệu"}</span>
                    {s.place && (
                      <span className="block truncate text-xs text-fg-muted">
                        {s.place.category}
                        {s.place.price_per_person != null && ` · ~${vnd.format(s.place.price_per_person)}đ/người`}
                        {s.place.address && ` · ${s.place.address}`}
                      </span>
                    )}
                  </button>
                  {!readOnly && (
                    <div className="-mr-1 -mt-1 flex shrink-0 items-center">
                      <IconButton
                        variant="plain"
                        size="sm"
                        label={`Đưa điểm ${i + 1} lên trước`}
                        icon={<IconChevronDown className="size-4 rotate-180" />}
                        onClick={() => onMove?.(s.key, -1)}
                        disabled={i === 0}
                        className="disabled:opacity-30"
                      />
                      <IconButton
                        variant="plain"
                        size="sm"
                        label={`Đưa điểm ${i + 1} xuống sau`}
                        icon={<IconChevronDown className="size-4" />}
                        onClick={() => onMove?.(s.key, 1)}
                        disabled={i === stops.length - 1}
                        className="disabled:opacity-30"
                      />
                      <IconButton
                        variant="plain"
                        size="sm"
                        label={`Bỏ điểm ${i + 1} khỏi lịch trình`}
                        icon={<IconClose className="size-4" />}
                        onClick={() => onRemove?.(s.key)}
                      />
                    </div>
                  )}
                </div>

                {readOnly ? (
                  (s.planned_time || s.note) && (
                    <p className="text-sm">
                      {s.planned_time && <span className="mr-2 font-bold">🕒 {s.planned_time}</span>}
                      {s.note && <span className="text-fg-muted">{s.note}</span>}
                    </p>
                  )
                ) : (
                  <div className="grid gap-2 sm:grid-cols-[9rem_minmax(0,1fr)]">
                    <label className="flex flex-col gap-1">
                      <span className="text-xs font-semibold text-fg-muted">Giờ ghé</span>
                      <input
                        type="time"
                        value={s.planned_time}
                        onChange={(e) => onTime?.(s.key, e.target.value)}
                        className={cn(field, "h-9 px-3", s.timeOutOfOrder && "border-warning")}
                        aria-describedby={s.timeOutOfOrder ? `${s.key}-time` : undefined}
                      />
                    </label>
                    <label className="flex flex-col gap-1">
                      <span className="text-xs font-semibold text-fg-muted">Ghi chú</span>
                      <input
                        value={s.note}
                        onChange={(e) => onNote?.(s.key, e.target.value)}
                        maxLength={NOTE_MAX_LENGTH}
                        placeholder="VD: gọi món bún chả, đặt bàn trước"
                        className={cn(field, "h-9 px-3")}
                      />
                    </label>
                  </div>
                )}
                {s.timeOutOfOrder && (
                  <p id={`${s.key}-time`} className="text-xs text-warning">
                    Giờ này sớm hơn điểm trước. Đổi giờ hoặc sắp lại thứ tự nhé.
                  </p>
                )}
              </div>
            </div>

            {s.legToNext !== undefined && (
              <div className="ml-6.5 flex items-center gap-2 border-l-2 border-dashed border-border py-2 pl-5 text-xs text-fg-muted">
                <span aria-hidden>🚶</span>
                <span>
                  {formatDistance(s.legToNext)} · khoảng {formatMinutes(walkingMinutes(s.legToNext))} đi bộ
                </span>
              </div>
            )}
          </li>
        );
      })}
    </ol>
  );
}

// =========================================================================== summary + actions

export function JourneySummary({
  stopCount,
  totalCost,
  unknownCost,
  totalDistance,
}: {
  stopCount: number;
  totalCost: number;
  unknownCost: number;
  totalDistance: number;
}) {
  const items: { label: string; value: string; hint?: string }[] = [
    { label: "Điểm dừng", value: String(stopCount) },
    {
      label: "Chi phí ước tính",
      value: totalCost ? `~${vnd.format(totalCost)}đ` : "Chưa rõ",
      hint: unknownCost ? `${unknownCost} quán chưa có giá` : "mỗi người",
    },
    {
      label: "Quãng đường",
      value: stopCount > 1 ? formatDistance(totalDistance) : "–",
      hint: stopCount > 1 ? `khoảng ${formatMinutes(walkingMinutes(totalDistance))} đi bộ` : undefined,
    },
  ];
  return (
    <dl className="grid grid-cols-3 gap-2 rounded-card bg-primary-soft/60 p-3" aria-label="Tổng kết lịch trình">
      {items.map((it) => (
        <div key={it.label} className="flex min-w-0 flex-col">
          <dt className="text-xs font-semibold text-fg-muted">{it.label}</dt>
          <dd className="truncate text-lg font-extrabold text-fg">{it.value}</dd>
          {it.hint && <dd className="truncate text-xs text-fg-muted">{it.hint}</dd>}
        </div>
      ))}
      <p className="col-span-3 text-xs text-fg-muted">Quãng đường tính theo đường chim bay; thời gian đi bộ là ước tính.</p>
    </dl>
  );
}

/** Walking directions in Google Maps: one link, or one per leg when the journey has many stops. */
export function DirectionsLinks({ links }: { links: string[] }) {
  if (links.length === 0) return null;
  const cls =
    "inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary px-5 font-bold text-primary-fg shadow-card transition ease-standard hover:brightness-95";
  if (links.length === 1)
    return (
      <a href={links[0]} target="_blank" rel="noopener noreferrer" className={cls} data-testid="journey-directions">
        <IconDirections className="size-4.5" aria-hidden /> Chỉ đường trên Google Maps
      </a>
    );
  return (
    <div className="flex flex-wrap gap-2" data-testid="journey-directions">
      {links.map((href, i) => (
        <a key={href} href={href} target="_blank" rel="noopener noreferrer" className={cls}>
          <IconDirections className="size-4.5" aria-hidden /> Chặng {i + 1}/{links.length}
        </a>
      ))}
      <p className="w-full text-xs text-fg-muted">Google Maps nhận tối đa 11 điểm mỗi lần, nên lịch trình được chia thành nhiều chặng nối tiếp.</p>
    </div>
  );
}

// =========================================================================== library

export interface LibraryRow {
  id: string;
  title?: string | null;
  planned_date?: string | null;
  updated_at: string;
  stop_count: number;
  open: boolean; // the one in the editor
}

export function LibraryList({
  rows,
  max,
  loading,
  error,
  onRetry,
  onOpen,
  onDelete,
  deletingId,
  guest,
  onLogin,
}: {
  rows: LibraryRow[];
  max: number;
  loading: boolean;
  error?: string;
  onRetry: () => void;
  onOpen: (id: string) => void;
  onDelete: (id: string) => void;
  deletingId: string | null;
  guest: boolean;
  onLogin: () => void;
}) {
  const [confirmId, setConfirmId] = useState<string | null>(null);
  return (
    <section className="flex flex-col gap-3" aria-labelledby="library-title">
      <div className="flex items-baseline justify-between gap-2">
        <h2 id="library-title" className="text-lg font-extrabold">
          Lịch trình đã lưu
        </h2>
        {!guest && !loading && !error && (
          <span className="text-sm text-fg-muted">
            {rows.length}/{max}
          </span>
        )}
      </div>

      {guest ? (
        <div className="rounded-card bg-surface p-4 text-sm shadow-card">
          <p>Đăng nhập để lưu lịch trình vào tài khoản và mở lại trên máy khác. Không đăng nhập vẫn lập và chia sẻ được.</p>
          <Button size="sm" className="mt-3" onClick={onLogin}>
            Đăng nhập
          </Button>
        </div>
      ) : loading ? (
        <div className="flex flex-col gap-2" aria-busy aria-label="Đang tải lịch trình">
          {[0, 1].map((i) => (
            <span key={i} className="h-16 animate-pulse rounded-card bg-surface shadow-card" />
          ))}
        </div>
      ) : error ? (
        <p className="rounded-card bg-surface p-4 text-sm shadow-card" role="alert">
          <span className="text-danger">{error}</span>{" "}
          <button type="button" onClick={onRetry} className="font-semibold underline">
            Thử lại
          </button>
        </p>
      ) : rows.length === 0 ? (
        <p className="rounded-card bg-surface p-4 text-sm text-fg-muted shadow-card">Bạn chưa lưu lịch trình nào.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {rows.map((r) => (
            <li key={r.id} className={cn("rounded-card bg-surface p-3 shadow-card", r.open && "ring-2 ring-primary")}>
              {confirmId === r.id ? (
                <div className="flex flex-wrap items-center gap-2 text-sm" role="alertdialog" aria-label="Xác nhận xoá">
                  <p className="min-w-0 flex-1">Xoá “{r.title ?? "Chuyến đi chưa đặt tên"}”? Không thể hoàn tác.</p>
                  <Button size="sm" variant="danger" loading={deletingId === r.id} onClick={() => onDelete(r.id)}>
                    Xoá
                  </Button>
                  <Button size="sm" variant="secondary" onClick={() => setConfirmId(null)}>
                    Giữ lại
                  </Button>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <span className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary-soft" aria-hidden>
                    <IconTrips className="size-5" />
                  </span>
                  <button type="button" onClick={() => onOpen(r.id)} className="min-w-0 flex-1 text-left" disabled={r.open}>
                    <span className="block truncate font-bold">{r.title ?? "Chuyến đi chưa đặt tên"}</span>
                    <span className="block truncate text-xs text-fg-muted">
                      {r.stop_count} điểm
                      {r.planned_date && ` · ${formatPlannedDate(r.planned_date)}`} · sửa {formatShortDate(r.updated_at)}
                      {r.open && " · đang mở"}
                    </span>
                  </button>
                  <IconButton variant="plain" size="sm" label={`Xoá ${r.title ?? "lịch trình"}`} icon={<IconClose className="size-4" />} onClick={() => setConfirmId(r.id)} />
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

// =========================================================================== share

export function ShareResult({ url, expiresAt, onCopy, copied, onNativeShare }: { url: string; expiresAt: string; onCopy: () => void; copied: boolean; onNativeShare?: () => void }) {
  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-fg-muted">
        Ai có link đều xem được lịch trình này, không cần tài khoản. Link dùng được tới hết ngày{" "}
        <strong className="text-fg">{formatShortDate(expiresAt)}</strong>.
      </p>
      <div className="flex gap-2">
        <input readOnly value={url} onFocus={(e) => e.currentTarget.select()} aria-label="Link chia sẻ" className={cn(field, "min-w-0 flex-1")} data-testid="share-url" />
        <Button onClick={onCopy}>{copied ? "Đã sao chép" : "Sao chép"}</Button>
      </div>
      {onNativeShare && (
        <Button variant="secondary" onClick={onNativeShare}>
          <IconShare className="size-4" aria-hidden /> Gửi qua ứng dụng khác
        </Button>
      )}
      <p className="text-xs text-fg-muted">
        Link là một bản chụp của lịch trình lúc này. Sửa lịch trình sau đó không làm đổi link: hãy tạo link mới để chia sẻ bản mới.
      </p>
    </div>
  );
}

export function Panel({ children, className }: { children: ReactNode; className?: string }) {
  return <section className={cn("flex flex-col gap-4 rounded-sheet bg-surface p-4 shadow-card sm:p-5", className)}>{children}</section>;
}
