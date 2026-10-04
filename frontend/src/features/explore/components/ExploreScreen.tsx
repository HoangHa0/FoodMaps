"use client";

import { useMemo, useState } from "react";

import { useRequireAuth } from "@/features/auth";

import { DEFAULT_PLACE_ID, EXPLORE_COPY, MAP_LABELS, PLACES } from "../mock";
import {
  FeaturedThisWeek,
  type FilterId,
  HeroStage,
  IllustratedMap,
  MapPreviewCard,
  PlaceDetailPanel,
  PlaceList,
} from "./views";

/** Google Maps search link by name (works without an API key; opens the app on phones). */
const directionsUrl = (name: string) =>
  `https://www.google.com/maps/search/?${new URLSearchParams({ api: "1", query: name }).toString()}`;

/**
 * Container of the home / Explore screen. Holds UI state only (selected place, filter, list
 * view, saved hearts). Data comes from ../mock for now:
 *   TODO(M2/M3/M7): replace PLACES with real queries (map places, match results, place summaries)
 *   TODO(M2): replace the local `saved` set with the saved-places API (the login guard stays)
 */
export function ExploreScreen() {
  const guard = useRequireAuth(); // Save = login-only action (M1): guests get the login sheet first
  const [filter, setFilter] = useState<FilterId>("nearby");
  const [selectedId, setSelectedId] = useState<string>(DEFAULT_PLACE_ID);
  const [listView, setListView] = useState(false);
  const [saved, setSaved] = useState<ReadonlySet<string>>(new Set());
  const [savedDishes, setSavedDishes] = useState<ReadonlySet<string>>(new Set());

  const visible = useMemo(
    () =>
      PLACES.filter((p) =>
        filter === "trending" ? p.trending : filter === "open" ? p.openNow : filter === "top" ? p.rating >= 4.6 : true,
      ),
    [filter],
  );
  const featured = PLACES.filter((p) => p.featured);
  const selected = PLACES.find((p) => p.id === selectedId) ?? PLACES[0];

  const toggle = (set: ReadonlySet<string>, id: string) => {
    const next = new Set(set);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  };
  const toggleSave = (id: string) => guard(() => setSaved((s) => toggle(s, id)));
  const toggleDish = (id: string) => guard(() => setSavedDishes((s) => toggle(s, id)));
  const select = (id: string) => {
    setSelectedId(id);
    setListView(false);
  };

  const map = (
    <IllustratedMap
      places={visible}
      labels={MAP_LABELS}
      selectedId={selectedId}
      onSelect={select}
      listView={listView}
      onToggleList={() => setListView((v) => !v)}
      list={<PlaceList places={visible} onSelect={select} />}
      preview={
        visible.some((p) => p.id === selected.id) ? (
          <MapPreviewCard place={selected} onOpen={() => document.getElementById("place-detail")?.scrollIntoView({ behavior: "smooth" })} />
        ) : undefined
      }
    />
  );

  return (
    // Two columns only when the hero still has room next to the 28rem panel (≈1360px+);
    // narrower desktops show the panel under the featured row.
    <div className="grid gap-5 pb-6 min-[1360px]:grid-cols-[minmax(0,1fr)_28rem] min-[1360px]:gap-0 min-[1360px]:pb-0">
      <div className="flex min-w-0 flex-col gap-3.5 md:px-2.5 min-[1360px]:pr-0">
        <HeroStage
          headline={EXPLORE_COPY.headline}
          subtitle={EXPLORE_COPY.subtitle}
          note={EXPLORE_COPY.note}
          filter={filter}
          onFilter={setFilter}
          map={map}
        />
        <div className="px-4 md:px-0">
          <FeaturedThisWeek places={featured} savedIds={saved} onToggleSave={toggleSave} onSelect={select} />
        </div>
      </div>
      <aside id="place-detail" className="w-full max-w-xl justify-self-center px-4 md:px-0 min-[1360px]:max-w-none min-[1360px]:pl-5 min-[1360px]:pr-6 min-[1360px]:pt-5.5" aria-label="Selected place">
        <PlaceDetailPanel
          place={selected}
          saved={saved.has(selected.id)}
          onToggleSave={() => toggleSave(selected.id)}
          onBack={() => setSelectedId(DEFAULT_PLACE_ID)}
          directionsUrl={directionsUrl(selected.name)}
          savedDishIds={savedDishes}
          onToggleDish={toggleDish}
        />
      </aside>
    </div>
  );
}
