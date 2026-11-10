"use client";

/**
 * Explore (home) views: props in, markup out. No data fetching here (see ExploreScreen).
 * Layout, top to bottom: short hero (one mascot), filters (search, price, categories), map, then the
 * list of places, one page at a time. Place details: side panel on wide screens, draggable sheet
 * otherwise.
 */
import type { ReactNode } from "react";

import {
  BrushUnderline,
  Chip,
  HandNote,
  IconButton,
  IconChevronRight,
  IconClose,
  IconDirections,
  IconHeart,
  IconPin,
  IconSort,
  IconStar,
  IconWrite,
  Mascot,
  Pagination,
  Rating,
  cn,
} from "@/ui";

import type { MapPlace } from "@/features/map";

import { PRICE_RANGES, SORTS, type SortId } from "../lib/listing";
import { PlaceSearchBox, type PlaceSuggestion } from "./PlaceSearchBox";

const vnd = new Intl.NumberFormat("vi-VN");

// =========================================================================== hero

export function ExploreHero({ placeCount, area }: { placeCount: number | null; area: string }) {
  return (
    <section className="flex items-end justify-between gap-6" aria-labelledby="explore-title">
      <div className="min-w-0">
        <h1 id="explore-title" className="font-display text-2xl font-bold leading-tight text-fg sm:text-3xl md:text-4xl">
          Khám phá quán ngon{" "}
          <span className="relative inline-block whitespace-nowrap">
            quanh bạn
            <BrushUnderline className="absolute -bottom-1.5 left-0 h-3 w-full" />
          </span>
        </h1>
        <p className="mt-3 hidden max-w-xl text-sm leading-relaxed text-fg-muted sm:block md:text-base">
          {placeCount ? `${placeCount} quán ở ${area} được cộng đồng FoodMaps đánh giá. ` : ""}
          Bấm vào ghim trên bản đồ để xem quán, hoặc mô tả món bạn muốn để được FoodMaps gợi ý.
        </p>
      </div>
      <div className="hidden shrink-0 items-end gap-2 md:flex" aria-hidden>
        <HandNote tilt={-8} className="mb-12 font-display text-lg font-semibold leading-snug">
          Ăn ngon
          <br />
          là chân ái!
        </HandNote>
        <Mascot className="w-24" />
      </div>
    </section>
  );
}

// =========================================================================== filters

export interface CategoryChip {
  name: string;
  icon: string;
  count: number;
}

const control =
  "h-10 rounded-control border border-border bg-surface px-3.5 text-sm text-fg shadow-card outline-none transition ease-standard focus:ring-2 focus:ring-primary";

/**
 * Place-name search with suggestions + price range. The text narrows both the pins and the list;
 * picking a suggestion opens that place.
 */
export function SearchFilters({
  query,
  onQuery,
  suggestions,
  matchCount,
  onPick,
  price,
  onPrice,
}: {
  query: string;
  onQuery: (q: string) => void;
  suggestions: PlaceSuggestion[];
  matchCount: number;
  onPick: (placeId: string) => void;
  price: number;
  onPrice: (i: number) => void;
}) {
  return (
    <div className="flex gap-2" role="search" aria-label="Tìm và lọc quán">
      <PlaceSearchBox
        query={query}
        onQuery={onQuery}
        suggestions={suggestions}
        matchCount={matchCount}
        onPick={onPick}
        className="flex-1"
      />
      <label className="flex shrink-0 items-center gap-2">
        <span className="sr-only text-sm font-semibold text-fg-muted sm:not-sr-only">Giá</span>
        <select
          value={price}
          onChange={(e) => onPrice(Number(e.target.value))}
          aria-label="Khoảng giá mỗi người"
          className={cn(control, "w-30 pr-7 sm:w-auto")}
        >
          {PRICE_RANGES.map((r, i) => (
            <option key={r.label} value={i}>
              {r.label}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

export function CategoryChips({
  categories,
  total,
  activeCategory,
  onCategory,
  topRated,
  onTopRated,
  showTopRated,
}: {
  categories: CategoryChip[];
  total: number;
  activeCategory: string | null;
  onCategory: (name: string | null) => void;
  topRated: boolean;
  onTopRated: () => void;
  /** hidden while no place has a rating (the filter would always be empty) */
  showTopRated: boolean;
}) {
  return (
    <div
      role="toolbar"
      aria-label="Danh mục"
      className="-mx-4 flex gap-2 overflow-x-auto px-4 pb-1 [scrollbar-width:none] md:mx-0 md:flex-wrap md:overflow-visible md:px-0 [&>button]:shrink-0"
    >
      <Chip selected={!activeCategory} onClick={() => onCategory(null)} icon={<IconPin className="size-4" aria-hidden />}>
        Tất cả {total > 0 && <span className="tabular-nums opacity-70">{total}</span>}
      </Chip>
      {categories.map((c) => (
        <Chip key={c.name} selected={activeCategory === c.name} onClick={() => onCategory(activeCategory === c.name ? null : c.name)}>
          <span aria-hidden>{c.icon}</span>
          {c.name} <span className="tabular-nums opacity-70">{c.count}</span>
        </Chip>
      ))}
      {showTopRated && (
        <Chip selected={topRated} onClick={onTopRated} title="Chỉ hiện quán từ 4.5 sao" icon={<IconStar className="size-4" aria-hidden />}>
          Đánh giá cao
        </Chip>
      )}
    </div>
  );
}

// =========================================================================== map overlay

export function PlaceEmoji({ icon, size = "md" }: { icon: string; size?: "sm" | "md" | "lg" }) {
  return (
    <span
      className={cn(
        "grid shrink-0 place-items-center rounded-xl bg-primary-soft",
        size === "sm" && "size-10 text-lg",
        size === "md" && "size-11 text-xl",
        size === "lg" && "size-14 text-2xl",
      )}
      aria-hidden
    >
      {icon}
    </span>
  );
}

function RatingLine({ place, size = "sm" }: { place: MapPlace; size?: "sm" | "md" }) {
  return place.avg_rating !== null && place.review_count > 0 ? (
    <Rating value={place.avg_rating} count={`${place.review_count} đánh giá`} size={size} />
  ) : (
    <span className={cn("text-fg-muted", size === "sm" ? "text-xs" : "text-sm")}>Chưa có đánh giá</span>
  );
}

/** Floating card over the map for the selected pin (narrow screens): opens the details. */
export function PlacePreview({ place, icon, onOpen, onClose }: { place: MapPlace; icon: string; onOpen: () => void; onClose: () => void }) {
  return (
    <div className="relative" data-testid="map-preview">
      <button
        type="button"
        onClick={onOpen}
        className="flex w-full items-center gap-3 rounded-card bg-surface-raised p-2.5 pr-10 text-left shadow-float transition ease-standard hover:bg-primary-soft"
      >
        <PlaceEmoji icon={icon} size="sm" />
        <span className="flex min-w-0 flex-1 flex-col gap-0.5">
          <span className="truncate text-sm font-bold text-fg">{place.name}</span>
          <span className="truncate text-xs text-fg-muted">
            {place.category}
            {place.price_per_person !== null && ` · ~${vnd.format(place.price_per_person)}đ`}
          </span>
          <span className="text-xs font-semibold text-fg">Xem chi tiết</span>
        </span>
        <IconChevronRight className="size-4 shrink-0 text-fg-muted" aria-hidden />
      </button>
      <IconButton
        variant="plain"
        size="sm"
        label="Bỏ chọn quán"
        icon={<IconClose className="size-4" />}
        onClick={onClose}
        className="absolute right-1.5 top-1.5"
      />
    </div>
  );
}

// =========================================================================== list of places

export function PlaceGrid({
  places,
  total,
  iconOf,
  selectedId,
  savedIds,
  onToggleSave,
  onSelect,
  title,
  sort,
  onSort,
  page,
  pageCount,
  firstIndex,
  onPage,
  onClearFilters,
}: {
  /** the places of the current page */
  places: MapPlace[];
  /** how many match the filters */
  total: number;
  iconOf: (p: MapPlace) => string;
  selectedId: string | null;
  savedIds: ReadonlySet<string>;
  onToggleSave: (p: MapPlace) => void;
  onSelect: (id: string) => void;
  title: string;
  sort: SortId;
  onSort: (s: SortId) => void;
  /** 1-based page, number of pages, index (0-based) of the first place of this page in the list */
  page: number;
  pageCount: number;
  firstIndex: number;
  onPage: (page: number) => void;
  /** shown in the empty state when a filter is on */
  onClearFilters?: () => void;
}) {
  return (
    <section className="flex scroll-mt-20 flex-col gap-3 lg:scroll-mt-4" aria-labelledby="place-grid-title" id="place-list">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="place-grid-title" className="text-lg font-extrabold text-fg">
          {title} <span className="text-sm font-semibold text-fg-muted">({total})</span>
        </h2>
        {total > 1 && (
          <label className="flex items-center gap-2 text-sm text-fg-muted">
            <IconSort className="size-4" aria-hidden />
            <span className="sr-only">Sắp xếp</span>
            <select value={sort} onChange={(e) => onSort(e.target.value as SortId)} className={cn(control, "h-9 pr-8")}>
              {SORTS.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
      {total === 0 ? (
        <div className="rounded-card bg-surface p-6 text-center text-sm text-fg-muted shadow-card">
          <p className="font-semibold text-fg">Không có quán nào khớp bộ lọc</p>
          <p className="mt-1">Thử bỏ bớt điều kiện, hoặc mô tả điều bạn muốn để AI tìm giúp.</p>
          {onClearFilters && (
            <button type="button" onClick={onClearFilters} className="mt-3 font-semibold text-fg underline">
              Xoá bộ lọc
            </button>
          )}
        </div>
      ) : (
        <>
          <ul className="grid grid-cols-1 gap-3 sm:grid-cols-2 2xl:grid-cols-3">
            {places.map((place) => (
              <li
                key={place.place_id}
                className={cn(
                  "relative rounded-card bg-surface p-3 shadow-card transition ease-standard hover:-translate-y-0.5",
                  selectedId === place.place_id && "ring-2 ring-primary",
                )}
              >
                <button
                  type="button"
                  onClick={() => onSelect(place.place_id)}
                  className="flex w-full items-start gap-3 pr-9 text-left"
                  aria-current={selectedId === place.place_id || undefined}
                >
                  <PlaceEmoji icon={iconOf(place)} />
                  <span className="flex min-w-0 flex-col gap-1">
                    <span className="truncate text-sm font-bold text-fg">{place.name}</span>
                    <span className="truncate text-xs text-fg-muted">
                      {place.category}
                      {place.price_per_person !== null && ` · ~${vnd.format(place.price_per_person)}đ/người`}
                    </span>
                    {place.address && <span className="truncate text-xs text-fg-muted">{place.address}</span>}
                  </span>
                </button>
                <SaveButton
                  saved={savedIds.has(place.place_id)}
                  onToggle={() => onToggleSave(place)}
                  className="absolute right-2 top-2"
                  size="sm"
                />
              </li>
            ))}
          </ul>
          <div className="flex flex-col items-center gap-2 pt-1">
            <Pagination page={page} pageCount={pageCount} onPage={onPage} label="Trang của danh sách quán" />
            <p className="text-xs text-fg-muted" aria-live="polite">
              Quán {firstIndex + 1}–{firstIndex + places.length} trong {total} quán
            </p>
          </div>
        </>
      )}
    </section>
  );
}

export function PlaceGridSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 2xl:grid-cols-3" aria-busy aria-label="Đang tải danh sách quán">
      {Array.from({ length: 6 }, (_, i) => (
        <div key={i} className="flex gap-3 rounded-card bg-surface p-3 shadow-card" aria-hidden>
          <span className="size-11 shrink-0 animate-pulse rounded-xl bg-primary-soft" />
          <span className="flex flex-1 flex-col gap-2 py-1">
            <span className="h-3.5 w-2/3 animate-pulse rounded-control bg-primary-soft" />
            <span className="h-3 w-1/2 animate-pulse rounded-control bg-primary-soft" />
            <span className="h-3 w-5/6 animate-pulse rounded-control bg-primary-soft" />
          </span>
        </div>
      ))}
    </div>
  );
}

/** Heart toggle on a white disc. */
export function SaveButton({
  saved,
  onToggle,
  className,
  size = "md",
}: {
  saved: boolean;
  onToggle: () => void;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <IconButton
      label={saved ? "Bỏ lưu quán" : "Lưu quán"}
      pressed={saved}
      size={size}
      onClick={onToggle}
      className={className}
      icon={<IconHeart className={cn(size === "sm" ? "size-4" : "size-5", saved ? "fill-accent text-accent" : "text-fg")} aria-hidden />}
    />
  );
}

// =========================================================================== details

export function PlaceDetail({
  place,
  icon,
  saved,
  onToggleSave,
  onWriteReview,
  onClose,
  directionsUrl,
  mapsUrl,
  insights,
  reviews,
}: {
  place: MapPlace;
  icon: string;
  saved: boolean;
  onToggleSave: () => void;
  onWriteReview: () => void;
  onClose: () => void;
  directionsUrl: string;
  mapsUrl: string;
  /** AI summary block (rendered by the container, from the match feature) */
  insights?: ReactNode;
  /** Website reviews block (rendered by the container, from the reviews feature) */
  reviews?: ReactNode;
}) {
  return (
    <article className="flex flex-col gap-4" data-testid="place-detail" aria-labelledby="place-detail-name">
      <header className="flex items-start gap-3">
        <PlaceEmoji icon={icon} size="lg" />
        <div className="min-w-0 flex-1">
          <h2 id="place-detail-name" className="text-xl font-extrabold leading-tight text-fg">
            {place.name}
          </h2>
          <p className="mt-1 text-sm text-fg-muted">{place.category}</p>
        </div>
        <IconButton variant="plain" label="Đóng" icon={<IconClose className="size-5" />} onClick={onClose} />
      </header>

      <dl className="flex flex-col gap-2.5 text-sm">
        <Info label="Đánh giá">
          <RatingLine place={place} size="md" />
        </Info>
        {place.price_per_person !== null && <Info label="Giá tham khảo">khoảng {vnd.format(place.price_per_person)}đ/người</Info>}
        {place.address && <Info label="Địa chỉ">{place.address}</Info>}
      </dl>

      <div className="grid grid-cols-[1fr_auto] gap-2">
        <a
          href={directionsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary font-bold text-primary-fg shadow-card transition ease-standard hover:brightness-95"
        >
          <IconDirections className="size-4.5" aria-hidden />
          Chỉ đường
        </a>
        <button
          type="button"
          onClick={onToggleSave}
          aria-pressed={saved}
          className="inline-flex h-11 items-center justify-center gap-2 rounded-control border border-border bg-surface px-4 font-bold text-fg transition ease-standard hover:bg-primary-soft"
        >
          <IconHeart className={cn("size-4.5", saved && "fill-accent text-accent")} aria-hidden />
          {saved ? "Đã lưu" : "Lưu"}
        </button>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
        <button type="button" onClick={onWriteReview} className="inline-flex items-center gap-1.5 font-semibold text-fg hover:underline">
          <IconWrite className="size-4" aria-hidden /> Viết đánh giá
        </button>
        <a href={mapsUrl} target="_blank" rel="noopener noreferrer" className="font-semibold text-fg-muted hover:text-fg hover:underline">
          Mở trên Google Maps ↗
        </a>
      </div>
      {insights}
      {reviews}
    </article>
  );
}

function Info({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="grid grid-cols-[6.5rem_1fr] gap-2">
      <dt className="font-semibold text-fg">{label}</dt>
      <dd className="text-fg-muted">{children}</dd>
    </div>
  );
}

/** Side panel content when nothing is selected (wide screens). */
export function DetailHint() {
  return (
    <div className="flex flex-col items-center gap-2 px-4 py-10 text-center">
      <span className="grid size-14 place-items-center rounded-full bg-primary-soft text-2xl" aria-hidden>
        📍
      </span>
      <p className="font-bold text-fg">Chọn một quán để xem chi tiết</p>
      <p className="text-sm text-fg-muted">Bấm vào ghim trên bản đồ hoặc một quán trong danh sách.</p>
    </div>
  );
}