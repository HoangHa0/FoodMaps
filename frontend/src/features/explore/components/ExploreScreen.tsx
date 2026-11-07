"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { useRequireAuth } from "@/features/auth";
<<<<<<< Updated upstream
import { mapApi, VietMap } from "@/features/map";

import { EXPLORE_COPY } from "../mock";
=======
import { MapMarker, MapView } from "@/features/map"; // 👈 Import MapView và MapMarker từ module map của bạn

import { DEFAULT_PLACE_ID, EXPLORE_COPY, PLACES } from "../mock";
>>>>>>> Stashed changes
import {
  type FilterId,
  HeroStage,
<<<<<<< Updated upstream
  StoredPlaceDetail,
  StoredPlaceList,
  StoredPlacePreview,
  StoredPlaceGrid,
=======
  MapPreviewCard,
  PlaceDetailPanel,
  PlaceList,
>>>>>>> Stashed changes
} from "./views";

function directionsUrl(lat: number, lng: number): string {
  const query = new URLSearchParams({ api: "1", destination: `${lat},${lng}` });
  return `https://www.google.com/maps/dir/?${query}`;
}

<<<<<<< Updated upstream
=======
/**
 * Container of the home / Explore screen.
 */
>>>>>>> Stashed changes
export function ExploreScreen() {
  const guard = useRequireAuth();
  const [filter, setFilter] = useState<FilterId>("nearby");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [listView, setListView] = useState(false);
  const [saved, setSaved] = useState<ReadonlySet<string>>(new Set());
  const placesQuery = useQuery({
    queryKey: ["map", "places"],
    queryFn: mapApi.places,
    staleTime: 60_000,
  });

  const visible = useMemo(
    () => {
      const places = placesQuery.data ?? [];
      return filter === "top"
        ? places.filter((place) => place.avg_rating !== null && place.avg_rating >= 4.6)
        : places;
    },
    [filter, placesQuery.data],
  );
  const selected = visible.find((place) => place.place_id === selectedId) ?? visible[0];

  const toggleSave = (id: string) =>
    guard(() =>
      setSaved((current) => {
        const next = new Set(current);
        if (next.has(id)) next.delete(id);
        else next.add(id);
        return next;
      }),
    );

<<<<<<< Updated upstream
=======
  // 👈 Chuyển đổi dữ liệu danh sách quán thành dạng MapMarker cho MapView
  const mapMarkers: MapMarker[] = useMemo(
    () =>
      visible.map((place) => ({
        id: place.id,
        lngLat: [place.lng, place.lat],
        icon: place.categoryIcon || "📍",
        label: place.name,
        variant: saved.has(place.id) ? "saved" : "match",
      })),
    [visible, saved],
  );

  const toggle = (set: ReadonlySet<string>, id: string) => {
    const next = new Set(set);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    return next;
  };
  const toggleSave = (id: string) => guard(() => setSaved((s) => toggle(s, id)));
  const toggleDish = (id: string) => guard(() => setSavedDishes((s) => toggle(s, id)));
>>>>>>> Stashed changes
  const select = (id: string) => {
    setSelectedId(id);
    setListView(false);
  };

  // 👈 Dùng MapView thật (VietMap GL JS) thay thế cho IllustratedMap
  const map = (
<<<<<<< Updated upstream
    <VietMap
      places={visible}
      selectedId={selected?.place_id ?? null}
      onSelect={select}
      listView={listView}
      onToggleList={() => setListView((value) => !value)}
      list={<StoredPlaceList places={visible} onSelect={select} />}
      preview={
        selected ? (
          <StoredPlacePreview
            place={selected}
            onOpen={() => document.getElementById("place-detail")?.scrollIntoView({ behavior: "smooth" })}
          />
        ) : undefined
      }
    />
=======
    <div className="relative w-full h-[500px] overflow-hidden rounded-2xl border border-gray-200">
      <MapView
        markers={mapMarkers}
        onMarkerClick={(marker) => select(marker.id)}
      />

      {/* Preview Card hiển thị ở góc dưới khi chọn quán */}
      {visible.some((p) => p.id === selected.id) && (
        <div className="absolute bottom-4 left-4 right-4 z-10 max-w-sm">
          <MapPreviewCard
            place={selected}
            onOpen={() => document.getElementById("place-detail")?.scrollIntoView({ behavior: "smooth" })}
          />
        </div>
      )}
    </div>
>>>>>>> Stashed changes
  );

  return (
    <div className="grid gap-5 pb-6 min-[1360px]:grid-cols-[minmax(0,1fr)_28rem] min-[1360px]:gap-0 min-[1360px]:pb-0">
      <div className="flex min-w-0 flex-col gap-3.5 md:px-2.5 min-[1360px]:pr-0">
        <HeroStage
          headline={EXPLORE_COPY.headline}
          subtitle="Khám phá các quán có trong dữ liệu FoodMaps."
          note={EXPLORE_COPY.note}
          filter={filter}
          onFilter={setFilter}
          map={map}
        />
        {placesQuery.isPending && (
          <p className="px-4 text-sm text-fg-muted" role="status">
            Đang tải danh sách quán…
          </p>
        )}
        {placesQuery.isError && (
          <p className="mx-4 rounded-card bg-surface p-4 text-sm text-danger shadow-card md:mx-0" role="alert">
            Không tải được danh sách quán từ FoodMaps. Hãy thử tải lại trang.
          </p>
        )}
        {!placesQuery.isPending && !placesQuery.isError && (
          <div className="px-4 md:px-0">
            <StoredPlaceGrid
              places={visible}
              savedIds={saved}
              onToggleSave={toggleSave}
              onSelect={select}
            />
          </div>
        )}
      </div>

      <aside
        id="place-detail"
        className="w-full max-w-xl justify-self-center px-4 md:px-0 min-[1360px]:max-w-none min-[1360px]:pl-5 min-[1360px]:pr-6 min-[1360px]:pt-5.5"
        aria-label="Thông tin quán"
      >
        {selected ? (
          <StoredPlaceDetail
            place={selected}
            saved={saved.has(selected.place_id)}
            onToggleSave={() => toggleSave(selected.place_id)}
            onBack={() => setListView(false)}
            directionsUrl={directionsUrl(selected.lat, selected.lng)}
          />
        ) : (
          !placesQuery.isPending &&
          !placesQuery.isError && (
            <p className="rounded-sheet bg-surface p-5 text-sm text-fg-muted shadow-sheet">
              {filter === "top" ? "Chưa có quán nào có đánh giá từ 4.6 trở lên." : "Chưa có quán nào trong dữ liệu FoodMaps."}
            </p>
          )
        )}
      </aside>
    </div>
  );
}