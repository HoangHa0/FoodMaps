"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useRef, useState } from "react";

import {
  CATEGORY_PARAM,
  categoryHref,
  categoryIcon,
  countCategories,
  type MapPlace,
  normalizeCategory,
  PLACE_PARAM,
  usePlaces,
  VietMap,
} from "@/features/map";
import { useRequireAuth } from "@/features/auth";
import { PlaceInsights } from "@/features/match";
import { ReviewForm } from "@/features/reviews";
import { useSavedPlaces } from "@/features/saved";
import { useMediaQuery } from "@/lib/useMediaQuery";
import { BottomSheet, Sheet } from "@/ui";

import { inPriceRange, PAGE_SIZE, queryScore, type SortId, sortPlaces, suggestPlaces } from "../lib/listing";
import {
  CategoryChips,
  DetailHint,
  ExploreHero,
  PlaceDetail,
  PlaceGrid,
  PlaceGridSkeleton,
  PlacePreview,
  SearchFilters,
} from "./views";

const AREA = "Hà Nội";
const TOP_RATED = 4.5;

const iconOf = (p: MapPlace) => categoryIcon(p.category);

function directionsUrl(p: MapPlace): string {
  return `https://www.google.com/maps/dir/?${new URLSearchParams({ api: "1", destination: `${p.lat},${p.lng}` })}`;
}
function mapsUrl(p: MapPlace): string {
  return `https://www.google.com/maps/search/?${new URLSearchParams({ api: "1", query: [p.name, p.address].filter(Boolean).join(", "), query_place_id: p.place_id })}`;
}

/**
 * Container of the home screen: places from the API; filters (category in the URL so the sidebar and
 * the chips agree; text, price and "Đánh giá cao" local) that narrow both the pins and the list; the
 * list sorted and shown one page at a time; the selected place (also from ?quan=, e.g. an AI result
 * or "Đã lưu"); saved hearts (M2 API) and the review form.
 */
export function ExploreScreen() {
  const router = useRouter();
  const params = useSearchParams();
  const activeCategory = params.get(CATEGORY_PARAM);
  const placeParam = params.get(PLACE_PARAM);
  const places = usePlaces();
  const { savedIds, toggle: toggleSave } = useSavedPlaces();
  const isWide = useMediaQuery("(min-width: 1280px)");
  const mapRef = useRef<HTMLDivElement>(null);
  const guard = useRequireAuth(); // guests log in first, then the review form opens

  const [query, setQuery] = useState("");
  const [price, setPrice] = useState(0);
  const [topRated, setTopRated] = useState(false);
  const [sort, setSort] = useState<SortId>("default");
  const [selectedId, setSelectedId] = useState<string | null>(placeParam);
  const [detailOpen, setDetailOpen] = useState(placeParam !== null);
  const [reviewOpen, setReviewOpen] = useState(false);

  // ?quan= changed while on this page (an AI result): show that place, clear the local filters
  const [seenParam, setSeenParam] = useState(placeParam);
  if (seenParam !== placeParam) {
    setSeenParam(placeParam);
    if (placeParam) {
      setSelectedId(placeParam);
      setDetailOpen(false); // the AI sheet already shows the details
      setQuery("");
      setPrice(0);
      setTopRated(false);
    }
  }

  const all = useMemo(() => places.data ?? [], [places.data]);
  const categories = useMemo(() => countCategories(all), [all]);
  const hasRatings = all.some((p) => p.avg_rating !== null && p.review_count > 0);
  const folded = query.trim().toLowerCase();
  // the filters other than the text (category, rating, price)
  const passesOtherFilters = useCallback(
    (p: MapPlace) =>
      (!activeCategory || normalizeCategory(p.category) === activeCategory) &&
      (!topRated || (p.avg_rating !== null && p.avg_rating >= TOP_RATED)) &&
      inPriceRange(p, price),
    [activeCategory, topRated, price],
  );
  const visible = useMemo(
    () => all.filter((p) => passesOtherFilters(p) && queryScore(p, folded) > 0),
    [all, passesOtherFilters, folded],
  );
  // suggestions come from ALL places: one hidden by another filter is still found, and marked
  const suggestions = useMemo(
    () =>
      suggestPlaces(all, folded).map((p) => ({ place: p, icon: iconOf(p), outside: !passesOtherFilters(p) })),
    [all, folded, passesOtherFilters],
  );
  // with a text filter and no explicit sort: name matches first, then address / category matches
  const sorted = useMemo(
    () =>
      folded && sort === "default"
        ? [...visible].sort((a, b) => queryScore(b, folded) - queryScore(a, folded))
        : sortPlaces(visible, sort),
    [visible, sort, folded],
  );

  // numbered pages; back to page 1 whenever the filters or the sort change
  const filterKey = `${activeCategory}|${topRated}|${price}|${folded}|${sort}`;
  const [paging, setPaging] = useState({ key: filterKey, page: 1 });
  const pageCount = Math.max(1, Math.ceil(sorted.length / PAGE_SIZE));
  const page = Math.min(paging.key === filterKey ? paging.page : 1, pageCount);
  const firstIndex = (page - 1) * PAGE_SIZE;
  const pagePlaces = sorted.slice(firstIndex, firstIndex + PAGE_SIZE);
  const goToPage = (p: number) => {
    setPaging({ key: filterKey, page: p });
    // the new page starts at the top of the list, not where the pager was
    document.getElementById("place-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const selected = visible.find((p) => p.place_id === selectedId) ?? null;
  const filtersOn = !!activeCategory || topRated || price > 0 || !!folded;

  const select = useCallback(
    (id: string, from: "map" | "list") => {
      setSelectedId(id);
      // from the list: details at once; from a pin: the small preview first (narrow screens)
      setDetailOpen(from === "list");
      // from the list: bring the map back into view, so the pin is there when the details are lowered
      if (from === "list") mapRef.current?.scrollIntoView({ behavior: "smooth", block: isWide ? "nearest" : "start" });
    },
    [isWide],
  );
  const clearSelection = useCallback(() => {
    setSelectedId(null);
    setDetailOpen(false);
  }, []);
  const setCategory = (name: string | null) => router.replace(categoryHref(name), { scroll: false });

  /** A suggestion was picked: show that place. If another filter hides it, clear those filters first. */
  const pickSuggestion = (id: string) => {
    const place = all.find((p) => p.place_id === id);
    if (!place) return;
    if (!passesOtherFilters(place)) {
      setPrice(0);
      setTopRated(false);
      if (activeCategory && normalizeCategory(place.category) !== activeCategory) setCategory(null);
    }
    select(id, "list");
  };
  const clearFilters = () => {
    setQuery("");
    setPrice(0);
    setTopRated(false);
    setCategory(null);
  };

  const detail = selected && (
    <PlaceDetail
      place={selected}
      icon={iconOf(selected)}
      saved={savedIds.has(selected.place_id)}
      onToggleSave={() => toggleSave(selected.place_id, selected.name)}
      onWriteReview={() => guard(() => setReviewOpen(true))}
      onClose={clearSelection}
      directionsUrl={directionsUrl(selected)}
      mapsUrl={mapsUrl(selected)}
      insights={<PlaceInsights key={selected.place_id} placeId={selected.place_id} />}
    />
  );

  return (
    <div className="grid gap-6 px-4 pb-6 pt-3 md:px-6 xl:grid-cols-[minmax(0,1fr)_22rem] xl:items-start 2xl:grid-cols-[minmax(0,1fr)_25rem]">
      <div className="flex min-w-0 flex-col gap-4">
        <ExploreHero placeCount={places.data?.length ?? null} area={AREA} />

        <div className="flex flex-col gap-3">
          <SearchFilters
            query={query}
            onQuery={setQuery}
            suggestions={suggestions}
            matchCount={visible.length}
            onPick={pickSuggestion}
            price={price}
            onPrice={setPrice}
          />
          <CategoryChips
            categories={categories}
            total={all.length}
            activeCategory={activeCategory}
            onCategory={setCategory}
            topRated={topRated}
            onTopRated={() => setTopRated((v) => !v)}
            showTopRated={hasRatings}
          />
        </div>

        <div ref={mapRef} className="relative h-[48vh] min-h-72 scroll-mt-20 overflow-hidden rounded-card shadow-card md:h-[58vh] lg:scroll-mt-4 xl:h-[min(64vh,640px)]">
          <VietMap
            places={visible}
            selectedId={selectedId}
            onSelect={(id) => select(id, "map")}
            onBackgroundClick={clearSelection}
            savedIds={savedIds}
            preview={
              selected && !isWide && !detailOpen ? (
                <PlacePreview place={selected} icon={iconOf(selected)} onOpen={() => setDetailOpen(true)} onClose={clearSelection} />
              ) : undefined
            }
          />
          {places.isSuccess && filtersOn && (
            <p className="pointer-events-none absolute bottom-9 left-3 z-10 rounded-control bg-surface-raised/95 px-3 py-1.5 text-xs font-semibold shadow-card">
              {visible.length} / {all.length} quán khớp bộ lọc
            </p>
          )}
        </div>

        {places.isPending && <PlaceGridSkeleton />}
        {places.isError && (
          <div className="rounded-card bg-surface p-4 text-sm shadow-card" role="alert">
            <p className="font-semibold text-danger">Không tải được danh sách quán.</p>
            <p className="mt-1 text-fg-muted">Kiểm tra kết nối mạng rồi thử lại.</p>
            <button type="button" onClick={() => places.refetch()} className="mt-2 font-semibold underline">
              Thử lại
            </button>
          </div>
        )}
        {places.isSuccess && (
          <PlaceGrid
            title={activeCategory ?? (filtersOn ? "Kết quả lọc" : "Tất cả quán")}
            places={pagePlaces}
            total={sorted.length}
            iconOf={iconOf}
            selectedId={selectedId}
            savedIds={savedIds}
            onToggleSave={(p) => toggleSave(p.place_id, p.name)}
            onSelect={(id) => select(id, "list")}
            sort={sort}
            onSort={setSort}
            page={page}
            pageCount={pageCount}
            firstIndex={firstIndex}
            onPage={goToPage}
            onClearFilters={filtersOn ? clearFilters : undefined}
          />
        )}
      </div>

      {/* wide screens: details beside the map, always in view */}
      {isWide && (
        <aside
          className="sticky top-4 max-h-[calc(100dvh-2rem)] overflow-y-auto rounded-sheet bg-surface p-5 shadow-sheet"
          aria-label="Thông tin quán"
        >
          {detail ?? <DetailHint />}
        </aside>
      )}

      {/* narrow screens: details in a sheet that can be dragged down to see the map */}
      {!isWide && selected && detailOpen && !reviewOpen && (
        <BottomSheet label={`Thông tin quán ${selected.name}`} resetKey={selected.place_id} peekHeight={104} className="sm:max-w-xl">
          {detail}
        </BottomSheet>
      )}

      {selected && (
        <Sheet open={reviewOpen} onClose={() => setReviewOpen(false)} title={`Đánh giá ${selected.name}`} modal>
          <ReviewForm placeId={selected.place_id} onSaved={() => setReviewOpen(false)} bare />
        </Sheet>
      )}
    </div>
  );
}
