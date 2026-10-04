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
  IconClock,
  IconDirections,
  IconGroup,
  IconHeart,
  IconList,
  IconLocate,
  IconMinus,
  IconOpeningHours,
  IconPayment,
  IconPin,
  IconPlus,
  IconStar,
  IconTrending,
  Badge,
  MapPin,
  Mascot,
  PopLines,
  Rating,
  cn,
} from "@/ui";

import type { ExplorePlace } from "../mock";

export type FilterId = "nearby" | "trending" | "top" | "open";

export const FILTERS: { id: FilterId; label: string; icon: ReactNode }[] = [
  { id: "nearby", label: "Nearby", icon: <IconPin className="size-4" aria-hidden /> },
  { id: "trending", label: "Trending", icon: <IconTrending className="size-4" aria-hidden /> },
  { id: "top", label: "Top Rated", icon: <IconStar className="size-4" aria-hidden /> },
  { id: "open", label: "Open Now", icon: <IconClock className="size-4" aria-hidden /> },
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
  /** The map block (illustration placeholder now, M2's Google map later). */
  map: ReactNode;
}) {
  return (
    <>
      {/* phones / tablets: plain stacked layout */}
      <section className="flex flex-col gap-4 px-4 pt-2 md:hidden">
        <div className="flex items-start justify-between gap-2">
          <HeroHeadline lines={headline} className="text-5xl" />
          <Mascot className="mt-2 w-24" />
        </div>
        <p className="text-sm text-fg-muted">{subtitle}</p>
        <FilterChips active={filter} onChange={onFilter} className="-mx-4 flex-nowrap! overflow-x-auto px-4 pb-1 [&>button]:shrink-0" />
        {/* crop away most of the illustration's top bleed, which only makes sense behind the desktop hero */}
        <div className="relative aspect-[834/430] w-full overflow-hidden rounded-card">
          <div className="absolute inset-x-0 bottom-0 h-[130%]">{map}</div>
        </div>
      </section>

      {/* desktop: the mock-up composition */}
      <section className="@container relative hidden aspect-[833/638] w-full md:block" aria-label="Explore">
        <div style={{ ...at(4.8, 5.4), ...fluid(6.05, 34), letterSpacing: "0.02em", transform: "rotate(-3.5deg)", transformOrigin: "left top" }}>
          <HeroHeadline lines={headline} />
        </div>
        <div style={{ ...at(5.2, 24.6, 28.4), height: "2.6%" }}>
          <BrushUnderline className="size-full" />
        </div>
        <div style={{ ...at(37.4, 9.6, 3.1), height: "8.4%" }}>
          <PopLines className="size-full" />
        </div>
        <p className="leading-snug text-fg-muted" style={{ ...at(36.8, 26.6, 23), ...fluid(1.56, 12) }}>
          {subtitle}
        </p>

        {/* the map sits UNDER the mascot and note: its top-right edge bleeds into the hero */}
        <div className="absolute inset-x-0 bottom-0" style={{ top: "12.54%" }}>
          {map}
        </div>

        <div style={{ ...at(59.4, 19.6, 3), height: "5%" }}>
          <PopLines className="size-full" flip />
        </div>
        <div style={at(63.9, 7.7, 20.3)}>
          <Mascot className="w-full" title="FoodMaps mascot" />
        </div>
        <div style={{ ...at(80.3, 4.1, 2.8), height: "4.5%" }}>
          <svg viewBox="0 0 24 30" className="size-full" aria-hidden>
            <path d="M8 3 L4 12 M20 16 L9 21" className="stroke-primary" strokeWidth="3.4" strokeLinecap="round" fill="none" />
          </svg>
        </div>
        <div className="text-center" style={{ ...at(81.6, 1.8, 15), ...fluid(2.3, 14) }}>
          <HandNote tilt={-24} className="leading-[1.05]">
            {note.map((l) => (
              <span key={l} className="block">
                {l}
              </span>
            ))}
          </HandNote>
        </div>
        <div style={{ ...at(88, 2.8, 8.4), height: "16%" }}>
          {/* curved arrow that wraps the note */}
          <svg viewBox="0 0 70 100" className="size-full" aria-hidden>
            <path d="M55 4 C70 24 66 64 32 92 M32 92 L44 86 M32 92 L26 80" className="stroke-fg" strokeWidth="1.6" fill="none" strokeLinecap="round" />
          </svg>
        </div>

        <FilterChips
          active={filter}
          onChange={onFilter}
          className="flex-nowrap"
          // chips keep their real size; only their position follows the stage
          style={at(3.5, 33.7)}
        />
      </section>
    </>
  );
}

// =========================================================================== illustrated map

export interface MapLabel {
  text: string;
  x: number;
  y: number;
  tilt: number;
  arrow: boolean;
}

/**
 * PLACEHOLDER MAP: a static illustration with clickable pins. M2 replaces the illustration and
 * the % positioning with <MapView> (Google Maps JS + AdvancedMarkerElement rendering <MapPin>);
 * the floating controls, preview card and "List View" button stay as they are.
 */
export function IllustratedMap({
  places,
  labels,
  selectedId,
  onSelect,
  preview,
  listView,
  onToggleList,
  list,
}: {
  places: ExplorePlace[];
  labels: MapLabel[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  preview?: ReactNode;
  listView: boolean;
  onToggleList: () => void;
  list: ReactNode;
}) {
  return (
    <div className="@container absolute inset-0" data-testid="explore-map">
      <Image
        src="/mock/map-illustration.webp"
        alt="Illustrated map of the area"
        fill
        priority
        sizes="(min-width: 768px) 60vw, 100vw"
        className="pointer-events-none select-none object-fill"
      />
      {!listView && (
        <>
          {labels.map((l) => (
            <div key={l.text} className="pointer-events-none flex flex-col items-center" style={{ ...at(l.x, l.y), ...fluid(2.65, 14) }}>
              <HandNote tilt={l.tilt}>{l.text}</HandNote>
              {l.arrow && (
                <svg viewBox="0 0 44 10" className="w-10" style={{ transform: `rotate(${l.tilt}deg)` }} aria-hidden>
                  <path d="M3 5 H41 M3 5 L8 2 M3 5 L8 8 M41 5 L36 2 M41 5 L36 8" className="stroke-fg" strokeWidth="1.4" fill="none" strokeLinecap="round" />
                </svg>
              )}
            </div>
          ))}
          {places.map((p) => (
            <div
              key={p.id}
              className={cn("absolute -translate-x-1/2 -translate-y-full", p.id === selectedId && "z-10")}
              style={{ left: `${p.mapPoint.x}%`, top: `${p.mapPoint.y}%` }}
            >
              <MapPin
                tone={p.pinTone}
                kind={p.pinKind}
                label={p.name}
                selected={p.id === selectedId}
                onClick={() => onSelect(p.id)}
              />
            </div>
          ))}
          {/* phones: no floating card (the detail panel sits right below the map) */}
          {preview && (
            <div className="hidden md:block" style={at(55.5, 35.2, 34.8)}>
              {preview}
            </div>
          )}
        </>
      )}
      {listView && <div className="absolute inset-x-0 bottom-0 top-[42%] overflow-y-auto rounded-b-card p-4 md:top-[34%]">{list}</div>}

      <div
        className="absolute hidden w-10 flex-col overflow-hidden rounded-control bg-surface-raised shadow-float md:flex md:w-[5%] md:min-w-10"
        style={{ right: "0.8%", top: "26.1%" }}
      >
        {/* TODO(M2): wire zoom / my-location to the Google map instance */}
        <IconButton variant="plain" label="Zoom in" icon={<IconPlus className="size-5" />} className="w-full rounded-none" />
        <span className="mx-2 h-px bg-border" aria-hidden />
        <IconButton variant="plain" label="Zoom out" icon={<IconMinus className="size-5" />} className="w-full rounded-none" />
        <span className="mx-2 h-px bg-border" aria-hidden />
        <IconButton variant="plain" label="My location" icon={<IconLocate className="size-5" />} className="w-full rounded-none" />
      </div>

      <button
        type="button"
        onClick={onToggleList}
        aria-pressed={listView}
        className="absolute inline-flex h-9 items-center gap-2 rounded-control bg-surface-raised px-4 text-sm font-semibold shadow-float transition ease-standard hover:bg-primary-soft"
        style={{ right: "1.6%", bottom: "2%" }}
      >
        <IconList className="size-4" aria-hidden />
        {listView ? "Map View" : "List View"}
      </button>
    </div>
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
