"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";

import { useRequireAuth } from "@/features/auth";
import { mapApi, VietMap } from "@/features/map";

import { EXPLORE_COPY } from "../mock";
import {
  type FilterId,
  HeroStage,
  StoredPlaceDetail,
  StoredPlaceList,
  StoredPlacePreview,
  StoredPlaceGrid,
} from "./views";

function directionsUrl(lat: number, lng: number): string {
  const query = new URLSearchParams({ api: "1", destination: `${lat},${lng}` });
  return `https://www.google.com/maps/dir/?${query}`;
}

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

  const select = (id: string) => {
    setSelectedId(id);
    setListView(false);
  };

  const map = (
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