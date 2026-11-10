"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { useMe } from "@/features/auth";
import { Button } from "@/ui";

import { usePlaces } from "../hooks/usePlaces";
import { useRemoveSaved, useSavedLists, useSavedPlaces } from "../hooks/useSaved";
import { placeHref } from "../lib/categories";
import type { MapPlace } from "../api";
import { ListManagerSheet } from "./ListManagerSheet";

/** "Đã lưu" screen for /me: every list with the places saved in it. */
export function SavedListsScreen() {
  const { data: me } = useMe();
  const lists = useSavedLists();
  const saved = useSavedPlaces();
  const places = usePlaces();
  const remove = useRemoveSaved();
  const [managing, setManaging] = useState(false);

  const placeById = useMemo(
    () => new Map((places.data ?? []).map((place: MapPlace) => [place.place_id, place] as const)),
    [places.data],
  );

  if (!me) {
    return <p className="rounded-card bg-surface p-5 text-sm text-fg-muted">Đăng nhập để xem các quán đã lưu.</p>;
  }
  if (lists.isPending || saved.isPending) {
    return (
      <p className="text-sm text-fg-muted" role="status">
        Đang tải danh sách đã lưu…
      </p>
    );
  }
  if (lists.isError || saved.isError) {
    return (
      <p className="rounded-card bg-surface p-4 text-sm text-danger" role="alert">
        Không tải được danh sách đã lưu. Hãy thử tải lại trang.
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold">Đã lưu</h2>
        <Button size="sm" variant="secondary" onClick={() => setManaging(true)}>
          Quản lý danh sách
        </Button>
      </div>

      {lists.data.map((list) => {
        const rows = saved.data.filter((row) => row.list_id === list.id);
        return (
          <section key={list.id} className="flex flex-col gap-2" aria-label={list.name}>
            <h3 className="flex items-center gap-2 font-semibold">
              <span aria-hidden>{list.icon}</span>
              {list.name}
              <span className="text-sm font-normal text-fg-muted">· {rows.length}</span>
            </h3>
            {rows.length === 0 ? (
              <p className="rounded-card bg-surface p-3 text-sm text-fg-muted">Chưa có quán nào trong danh sách này.</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {rows.map((row) => {
                  const place = placeById.get(row.place_id);
                  return (
                    <li key={row.id} className="flex items-center gap-3 rounded-card bg-surface-raised p-3 shadow-card">
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-semibold">{place?.name ?? "Quán không còn trong dữ liệu"}</p>
                        {place && <p className="truncate text-sm text-fg-muted">{place.category}</p>}
                        {row.note && <p className="truncate text-sm text-fg-muted">“{row.note}”</p>}
                      </div>
                      {place && (
                        <Link
                          href={placeHref(place.place_id)}
                          className="text-sm font-semibold text-primary hover:underline"
                        >
                          Xem trên bản đồ
                        </Link>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => remove.mutate(row.id)}>
                        Bỏ lưu
                      </Button>
                    </li>
                  );
                })}
              </ul>
            )}
          </section>
        );
      })}

      <ListManagerSheet open={managing} onClose={() => setManaging(false)} />
    </div>
  );
}