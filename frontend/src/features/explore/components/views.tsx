"use client";

/**
 * Explore screen views: props in, markup out. No data fetching here (see ExploreScreen).
 * Geometry note: the hero + map "stage" is an artboard with the mock-up's proportions
 * (833 x 638). Everything inside is positioned in % of it and text sizes use container-query
 * units (cqw), so the composition keeps its look at any desktop width.
 */
import Image from "next/image";
import type { CSSProperties, ReactNode } from "react";

import {
  BrushUnderline,
  Chip,
  HandNote,
  IconArrowRight,
  IconBack,
  IconButton,
  IconChevronRight,
  IconDirections,
  IconGroup,
  IconHeart,
  IconOpeningHours,
  IconPayment,
  IconPin,
  IconStar,
  Badge,
  Mascot,
  PopLines,
  Rating,
  cn,
} from "@/ui";

import type { ExplorePlace } from "../mock";
import type { MapPlace } from "@/features/map";

export type FilterId = "nearby" | "top";

export const FILTERS: { id: FilterId; label: string; icon: ReactNode }[] = [
  { id: "nearby", label: "Tất cả quán", icon: <IconPin className="size-4" aria-hidden /> },
  { id: "top", label: "Đánh giá cao", icon: <IconStar className="size-4" aria-hidden /> },
];

/** Absolute position in % of the parent: at(left, top, width?) */
const at = (left: number, top: number, width?: number): CSSProperties => ({
  position: "absolute",
  left: `${left}%`,
  top: `${top}%`,
  ...(width !== undefined ? { width: `${width}%` } : {}),
});
/** Font size that scales with the stage width, never below `min` px. */
const fluid = (cqw: number, min: number): CSSProperties => ({ fontSize: `max(${min}px, ${cqw}cqw)` });

// =========================================================================== hero + map stage

export function HeroHeadline({ lines, className, style }: { lines: string[]; className?: string; style?: CSSProperties }) {
  return (
    <h1 className={cn("relative font-brand font-bold leading-[0.9] text-fg", className)} style={style}>
      {lines.map((l, i) => (
        <span key={l} className="block" style={{ paddingLeft: `${i * 0.08}em` }}>
          {l}
        </span>
      ))}
    </h1>
  );
}

export function FilterChips({
  active,
  onChange,
  className,
  style,
}: {
  active: FilterId;
  onChange: (f: FilterId) => void;
  className?: string;
  style?: CSSProperties;
}) {
  return (
    <div role="toolbar" aria-label="Filters" className={cn("flex flex-wrap gap-3.5", className)} style={style}>
      {FILTERS.map((f) => (
        <Chip key={f.id} selected={active === f.id} icon={f.icon} onClick={() => onChange(f.id)}>
          {f.label}
        </Chip>
      ))}
    </div>
  );
}

export function HeroStage({
  headline,
  subtitle,
  note,
  filter,
  onFilter,
  map,
}: {
  headline: string[];
  subtitle: string;
  note: string[];
  filter: FilterId;
  onFilter: (f: FilterId) => void;
  /** The map block. */
  map: ReactNode;
}) {
  return (
    <section
      className="@container relative flex flex-col gap-4 px-4 pt-2 md:block md:aspect-[833/638] md:w-full md:px-0 md:pt-0"
      aria-label="Explore"
    >
      <div className="flex items-start justify-between gap-2 md:hidden">
        <HeroHeadline lines={headline} className="text-5xl" />
        <Mascot className="mt-2 w-24" />
      </div>
      <p className="text-sm text-fg-muted md:hidden">{subtitle}</p>
      <FilterChips
        active={filter}
        onChange={onFilter}
        className="-mx-4 flex-nowrap! overflow-x-auto px-4 pb-1 md:hidden [&>button]:shrink-0"
      />

      <div className="relative aspect-[834/430] w-full overflow-hidden rounded-card md:absolute md:inset-x-0 md:bottom-0 md:top-[12.54%] md:aspect-auto">
        {map}
      </div>

      <div
        className="hidden md:block"
        style={{ ...at(4.8, 5.4), ...fluid(6.05, 34), letterSpacing: "0.02em", transform: "rotate(-3.5deg)", transformOrigin: "left top" }}
      >
        <HeroHeadline lines={headline} />
      </div>
      <div className="hidden md:block" style={{ ...at(5.2, 24.6, 28.4), height: "2.6%" }}>
        <BrushUnderline className="size-full" />
      </div>
      <div className="hidden md:block" style={{ ...at(37.4, 9.6, 3.1), height: "8.4%" }}>
        <PopLines className="size-full" />
      </div>
      <p className="hidden leading-snug text-fg-muted md:block" style={{ ...at(36.8, 26.6, 23), ...fluid(1.56, 12) }}>
        {subtitle}
      </p>

      <div className="hidden md:block" style={{ ...at(59.4, 19.6, 3), height: "5%" }}>
        <PopLines className="size-full" flip />
      </div>
      <div className="hidden md:block" style={at(63.9, 7.7, 20.3)}>
        <Mascot className="w-full" title="FoodMaps mascot" />
      </div>
      <div className="hidden md:block" style={{ ...at(80.3, 4.1, 2.8), height: "4.5%" }}>
        <svg viewBox="0 0 24 30" className="size-full" aria-hidden>
          <path d="M8 3 L4 12 M20 16 L9 21" className="stroke-primary" strokeWidth="3.4" strokeLinecap="round" fill="none" />
        </svg>
      </div>
      <div className="hidden text-center md:block" style={{ ...at(81.6, 1.8, 15), ...fluid(2.3, 14) }}>
        <HandNote tilt={-24} className="leading-[1.05]">
          {note.map((line) => (
            <span key={line} className="block">
              {line}
            </span>
          ))}
        </HandNote>
      </div>
      <div className="hidden md:block" style={{ ...at(88, 2.8, 8.4), height: "16%" }}>
        <svg viewBox="0 0 70 100" className="size-full" aria-hidden>
          <path d="M55 4 C70 24 66 64 32 92 M32 92 L44 86 M32 92 L26 80" className="stroke-fg" strokeWidth="1.6" fill="none" strokeLinecap="round" />
        </svg>
      </div>

      <FilterChips
        active={filter}
        onChange={onFilter}
        className="hidden flex-nowrap md:flex"
        style={at(3.5, 33.7)}
      />
    </section>
  );
}

/** Floating card over the map for the selected pin. */
export function MapPreviewCard({ place, onOpen }: { place: ExplorePlace; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex w-full items-center gap-3 rounded-card bg-surface-raised p-2 pr-3 text-left shadow-float transition ease-standard hover:-translate-y-0.5"
      data-testid="map-preview"
    >
      <span className="relative aspect-[88/70] w-[30%] shrink-0 overflow-hidden rounded-xl">
        <Image src={place.thumb} alt="" fill sizes="96px" className="object-cover" />
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="truncate text-sm font-bold text-fg">{place.name}</span>
        <Rating value={place.rating} count={place.reviewCount} size="sm" />
        <span className="inline-flex items-center gap-1 text-xs text-fg-muted">
          <IconPin className="size-3.5 fill-primary text-rating" aria-hidden />
          {place.distance}
        </span>
      </span>
      <IconChevronRight className="size-4 shrink-0 text-fg-muted" aria-hidden />
    </button>
  );
}

export function StoredPlacePreview({ place, onOpen }: { place: MapPlace; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex w-full items-center gap-3 rounded-card bg-surface-raised p-3 text-left shadow-float transition ease-standard hover:-translate-y-0.5"
      data-testid="map-preview"
    >
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-xl" aria-hidden>
        {/cafe|cà phê|trà/i.test(place.category) ? "☕" : "🍽️"}
      </span>
      <span className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="truncate text-sm font-bold text-fg">{place.name}</span>
        <span className="truncate text-xs text-fg-muted">{place.category}</span>
        {place.avg_rating !== null && place.review_count > 0 ? (
          <Rating value={place.avg_rating} count={`${place.review_count} đánh giá`} size="sm" />
        ) : (
          <span className="text-xs text-fg-muted">Chưa có đánh giá</span>
        )}
      </span>
      <IconChevronRight className="size-4 shrink-0 text-fg-muted" aria-hidden />
    </button>
  );
}

export function StoredPlaceList({ places, onSelect }: { places: MapPlace[]; onSelect: (id: string) => void }) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {places.map((place) => (
        <li key={place.place_id}>
          <button
            type="button"
            onClick={() => onSelect(place.place_id)}
            className="flex w-full items-center gap-3 rounded-card bg-surface-raised p-3 text-left shadow-card hover:bg-primary-soft"
          >
            <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-xl" aria-hidden>
              {/cafe|cà phê|trà/i.test(place.category) ? "☕" : "🍽️"}
            </span>
            <span className="flex min-w-0 flex-1 flex-col gap-1">
              <span className="truncate text-sm font-bold">{place.name}</span>
              <span className="truncate text-xs text-fg-muted">{place.category}</span>
            </span>
            {place.avg_rating !== null && place.review_count > 0 ? (
              <Rating value={place.avg_rating} size="sm" />
            ) : (
              <span className="text-xs text-fg-muted">Chưa có đánh giá</span>
            )}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function StoredPlaceGrid({
  places,
  savedIds,
  onToggleSave,
  onSelect,
}: {
  places: MapPlace[];
  savedIds: ReadonlySet<string>;
  onToggleSave: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="rounded-card bg-surface px-4 pb-4 pt-3 shadow-card md:px-7" aria-label="Quán trong FoodMaps">
      <SectionTitle title="Quán trong FoodMaps" action={`${places.length} quán`} />
      {places.length === 0 ? (
        <p className="py-6 text-center text-sm text-fg-muted">Chưa có quán nào trong khu vực dữ liệu.</p>
      ) : (
        <ul className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {places.map((place) => (
            <li key={place.place_id} className="relative rounded-xl bg-surface-raised p-3 shadow-card">
              <button type="button" onClick={() => onSelect(place.place_id)} className="flex w-full items-center gap-3 pr-9 text-left">
                <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-xl" aria-hidden>
                  {/cafe|cà phê|trà/i.test(place.category) ? "☕" : "🍽️"}
                </span>
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="truncate text-sm font-semibold text-fg">{place.name}</span>
                  <span className="truncate text-xs text-fg-muted">{place.category}</span>
                  {place.avg_rating !== null ? (
                    <Rating value={place.avg_rating} count={`${place.review_count} đánh giá`} size="sm" />
                  ) : (
                    <span className="text-xs text-fg-muted">Chưa có đánh giá</span>
                  )}
                </span>
              </button>
              <SaveButton
                saved={savedIds.has(place.place_id)}
                onToggle={() => onToggleSave(place.place_id)}
                filled
                className="absolute right-2 top-2"
                size="sm"
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function StoredPlaceDetail({
  place,
  saved,
  onToggleSave,
  onBack,
  directionsUrl,
}: {
  place: MapPlace;
  saved: boolean;
  onToggleSave: () => void;
  onBack: () => void;
  directionsUrl: string;
}) {
  return (
    <article className="overflow-hidden rounded-sheet bg-surface p-5 shadow-sheet" data-testid="place-detail" aria-label={place.name}>
      <header className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-start gap-3">
          <span className="grid size-12 shrink-0 place-items-center rounded-xl bg-primary-soft text-2xl" aria-hidden>
            {/cafe|cà phê|trà/i.test(place.category) ? "☕" : "🍽️"}
          </span>
          <div className="min-w-0">
            <h2 className="text-xl font-extrabold leading-tight text-fg">{place.name}</h2>
            <p className="mt-1 text-sm text-fg-muted">{place.category}</p>
          </div>
        </div>
        <SaveButton saved={saved} onToggle={onToggleSave} />
      </header>

      <div className="mt-4 flex flex-col gap-3 text-sm text-fg-muted">
        {place.avg_rating !== null ? (
          <Rating value={place.avg_rating} count={`${place.review_count} đánh giá`} />
        ) : (
          <span>Chưa có đánh giá</span>
        )}
        {place.address && (
          <p>
            <span className="font-semibold text-fg">Địa chỉ: </span>
            {place.address}
          </p>
        )}
        {place.price_per_person !== null && (
          <p>
            <span className="font-semibold text-fg">Giá tham khảo: </span>
            {new Intl.NumberFormat("vi-VN").format(place.price_per_person)}đ/người
          </p>
        )}
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3">
        <button type="button" onClick={onBack} className="h-11 rounded-control bg-surface-raised font-semibold text-fg hover:bg-primary-soft">
          Quay lại bản đồ
        </button>
        <a
          href={directionsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex h-11 items-center justify-center gap-2 rounded-control bg-primary font-bold text-primary-fg shadow-card hover:brightness-95"
        >
          <IconDirections className="size-4.5 fill-fg" aria-hidden />
          Chỉ đường
        </a>
      </div>
    </article>
  );
}

/** "List View": the same places as rows. */
export function PlaceList({ places, onSelect }: { places: ExplorePlace[]; onSelect: (id: string) => void }) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {places.map((p) => (
        <li key={p.id}>
          <button
            type="button"
            onClick={() => onSelect(p.id)}
            className="flex w-full items-center gap-3 rounded-card bg-surface-raised p-2 text-left shadow-card hover:bg-primary-soft"
          >
            <span className="relative size-12 shrink-0 overflow-hidden rounded-lg">
              <Image src={p.thumb} alt="" fill sizes="48px" className="object-cover" />
            </span>
            <span className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-bold">{p.name}</span>
              <Rating value={p.rating} count={p.reviewCount} size="sm" />
            </span>
            <span className="ml-auto text-xs font-semibold">{p.distance}</span>
          </button>
        </li>
      ))}
    </ul>
  );
}

// =========================================================================== section header

export function SectionTitle({
  title,
  action,
  onAction,
  doodle = false,
}: {
  title: string;
  action?: string;
  onAction?: () => void;
  /** small hand-drawn strokes after the title */
  doodle?: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-2">
      <h2 className="flex items-center gap-1.5 text-lg font-extrabold text-fg">
        <Mascot variant="flying" className="w-6" />
        {title}
        {doodle && <PopLines className="ml-2 h-5 w-3 -rotate-12 self-start" />}
      </h2>
      {action && (
        <button type="button" onClick={onAction} className="inline-flex items-center gap-1 text-xs font-semibold text-fg-muted hover:text-fg">
          {action} <IconArrowRight className="size-3.5" aria-hidden />
        </button>
      )}
    </div>
  );
}

// =========================================================================== featured row

export function FeaturedThisWeek({
  places,
  savedIds,
  onToggleSave,
  onSelect,
}: {
  places: ExplorePlace[];
  savedIds: ReadonlySet<string>;
  onToggleSave: (id: string) => void;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="rounded-card bg-surface px-4 pb-2.5 pt-3 shadow-card md:px-7" aria-label="Featured this week">
      <SectionTitle title="Featured This Week" action="See all" doodle />
      <ul className="mt-1.5 grid grid-cols-2 gap-3 md:grid-cols-4 md:gap-5">
        {places.map((p) => (
          <li key={p.id}>
            <PlaceCard place={p} saved={savedIds.has(p.id)} onToggleSave={() => onToggleSave(p.id)} onSelect={() => onSelect(p.id)} />
          </li>
        ))}
      </ul>
    </section>
  );
}

function PlaceCard({
  place,
  saved,
  onToggleSave,
  onSelect,
}: {
  place: ExplorePlace;
  saved: boolean;
  onToggleSave: () => void;
  onSelect: () => void;
}) {
  return (
    <article className="relative overflow-hidden rounded-xl bg-surface-raised shadow-card" data-testid="featured-card">
      <button type="button" onClick={onSelect} className="block w-full text-left">
        <span className="relative block aspect-[180/70] w-full">
          <Image src={place.photo} alt={place.name} fill sizes="(min-width: 768px) 18vw, 45vw" className="object-cover" />
        </span>
        <span className="flex flex-col gap-0.5 px-2.5 pb-2 pt-1.5">
          <span className="truncate text-sm font-semibold text-fg">{place.name}</span>
          <span className="flex items-center gap-1.5 text-xs text-fg-muted">
            <Rating value={place.rating} count={place.reviewCount} size="sm" className="[&>span:first-of-type]:font-normal [&>span:first-of-type]:text-fg-muted" />
            <span aria-hidden>·</span>
            {place.cuisine}
          </span>
          <span className="text-xs font-bold text-fg">{place.distance}</span>
        </span>
      </button>
      <SaveButton saved={saved} onToggle={onToggleSave} filled className="absolute right-2 top-2" size="sm" />
    </article>
  );
}

/** Heart toggle. `filled`: dark heart on a white disc (cards); otherwise outline (dish tiles). */
export function SaveButton({
  saved,
  onToggle,
  filled = false,
  className,
  size = "md",
}: {
  saved: boolean;
  onToggle: () => void;
  filled?: boolean;
  className?: string;
  size?: "sm" | "md";
}) {
  return (
    <IconButton
      label={saved ? "Remove from saved" : "Save"}
      pressed={saved}
      size={size}
      onClick={onToggle}
      className={className}
      icon={
        <IconHeart
          className={cn(
            size === "sm" ? "size-4" : "size-5",
            saved ? "fill-accent text-accent" : filled ? "fill-pin-neutral text-pin-neutral" : "text-fg",
          )}
          aria-hidden
        />
      }
    />
  );
}

// =========================================================================== detail panel

export function PlaceDetailPanel({
  place,
  saved,
  onToggleSave,
  onBack,
  directionsUrl,
  savedDishIds,
  onToggleDish,
}: {
  place: ExplorePlace;
  saved: boolean;
  onToggleSave: () => void;
  onBack: () => void;
  directionsUrl: string;
  savedDishIds: ReadonlySet<string>;
  onToggleDish: (id: string) => void;
}) {
  return (
    <article className="overflow-hidden rounded-sheet bg-surface shadow-sheet" data-testid="place-detail" aria-label={place.name}>
      <div className="relative aspect-[405/204] w-full">
        <Image src={place.heroPhoto} alt={place.name} fill sizes="420px" className="object-cover" priority />
        <IconButton label="Back" icon={<IconBack className="size-5" />} onClick={onBack} className="absolute left-4 top-4" />
        <SaveButton saved={saved} onToggle={onToggleSave} className="absolute right-4 top-4" />
        <span className="absolute bottom-3 right-4 rounded-control bg-overlay px-3 py-1 text-xs font-semibold text-surface">
          1/{place.photoCount}
        </span>
      </div>

      <div className="flex flex-col gap-3.5 px-5 pb-4 pt-3.5">
        <header className="flex gap-4">
          <Mascot variant="round" className="mt-1 size-11" />
          <div className="flex min-w-0 flex-col gap-1">
            <h2 className="text-2xl font-extrabold leading-tight text-fg">{place.name}</h2>
            <p className="text-sm text-fg-muted">{place.subtitle}</p>
          </div>
        </header>
        <p className="-mt-2 flex items-center gap-2 pl-1 text-sm">
          <Rating value={place.rating} count={`${place.reviewCount} reviews`} />
          <span aria-hidden>•</span>
          <span className="font-semibold">{place.distance}</span>
        </p>

        <ul className="flex flex-wrap gap-2" aria-label="Tags">
          {place.tags.map((t) => (
            <li key={t}>
              <Badge>{t}</Badge>
            </li>
          ))}
        </ul>

        <p className="max-w-74 text-sm leading-relaxed text-fg-muted">{place.description}</p>

        <ul className="flex flex-col gap-1.5 text-sm text-fg-muted">
          <InfoRow icon={<IconOpeningHours className="size-4.5 text-fg" aria-hidden />}>
            <span className="font-bold text-fg">Open</span> {place.openHours}
          </InfoRow>
          <InfoRow icon={<IconPayment className="size-4.5 text-fg" aria-hidden />}>{place.payment}</InfoRow>
          <InfoRow icon={<IconGroup className="size-4.5 fill-fg text-fg" aria-hidden />}>{place.goodFor}</InfoRow>
        </ul>

        <a
          href={directionsUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-1 inline-flex h-12 items-center justify-center gap-2 rounded-control bg-primary font-bold text-primary-fg shadow-card transition ease-standard hover:brightness-95"
        >
          <IconDirections className="size-4.5 fill-fg" aria-hidden />
          Get Directions
        </a>

        {place.dishes.length > 0 && (
          <section className="mt-1 flex flex-col gap-2.5" aria-label="Popular dishes">
            <SectionTitle title="Popular Dishes" action="See all" />
            <ul className="grid grid-cols-3 gap-3">
              {place.dishes.map((d) => (
                <li key={d.id} className="relative overflow-hidden rounded-xl bg-surface-raised shadow-card">
                  <span className="relative block aspect-[112/78] w-full">
                    <Image src={d.photo} alt={d.name} fill sizes="130px" className="object-cover" />
                  </span>
                  <span className="flex flex-col gap-0.5 px-2 pb-2 pt-1.5">
                    <span className="truncate text-xs font-semibold text-fg">{d.name}</span>
                    <span className="text-xs text-fg-muted">{d.price}</span>
                  </span>
                  <IconButton
                    variant="plain"
                    size="sm"
                    label={savedDishIds.has(d.id) ? `Unsave ${d.name}` : `Save ${d.name}`}
                    pressed={savedDishIds.has(d.id)}
                    onClick={() => onToggleDish(d.id)}
                    className="absolute right-1 top-1 text-surface-raised hover:bg-transparent"
                    icon={<IconHeart className={cn("size-5 drop-shadow", savedDishIds.has(d.id) && "fill-accent text-accent")} aria-hidden />}
                  />
                </li>
              ))}
            </ul>
          </section>
        )}
      </div>
    </article>
  );
}

function InfoRow({ icon, children }: { icon: ReactNode; children: ReactNode }) {
  return (
    <li className="flex items-center gap-3">
      {icon}
      <span>{children}</span>
    </li>
  );
}
