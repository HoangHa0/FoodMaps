"use client";

import Link from "next/link";
import { useMemo } from "react";

import { useMe } from "@/features/auth";
import { categoryIcon, type MapPlace, placeHref, usePlaces } from "@/features/map";
import { IconHeart, IconPin, Spinner } from "@/ui";

import { useSavedPlaces } from "../hooks/useSavedPlaces";

/** "Đã lưu": the user's saved places (M2 API), each one opens on the map. Guests are asked to log in. */
export function SavedScreen() {
  const { data: me, isPending: mePending } = useMe();
  const { saved, toggle, isLoading, error } = useSavedPlaces();
  const places = usePlaces();
  const byId = useMemo(() => new Map((places.data ?? []).map((p) => [p.place_id, p])), [places.data]);

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-5 px-4 py-4 md:px-6">
      <header>
        <h1 className="font-display text-3xl font-bold">Quán đã lưu</h1>
        <p className="mt-1 text-sm text-fg-muted">Những quán bạn bấm ♥ để dành lần sau ghé.</p>
      </header>

      {mePending || (me && (isLoading || places.isPending)) ? (
        <Spinner />
      ) : !me ? (
        <section className="rounded-sheet bg-surface p-6 text-center shadow-card">
          <p className="font-bold">Đăng nhập để xem và lưu quán</p>
          <p className="mt-1 text-sm text-fg-muted">Quán đã lưu được giữ trong tài khoản, mở trên máy nào cũng thấy.</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            <Link href="/login?next=%2Fme" className="inline-flex h-10 items-center rounded-control bg-primary px-5 font-bold text-primary-fg shadow-card">
              Đăng nhập
            </Link>
            <Link href="/register?next=%2Fme" className="inline-flex h-10 items-center rounded-control border border-border bg-surface px-5 font-bold">
              Tạo tài khoản
            </Link>
          </div>
        </section>
      ) : saved.length === 0 ? (
        <section className="rounded-sheet bg-surface p-6 text-center shadow-card">
          <p className="font-bold">Bạn chưa lưu quán nào</p>
          <p className="mt-1 text-sm text-fg-muted">Bấm ♥ trên một quán ở trang Khám phá để lưu lại.</p>
          <Link href="/" className="mt-4 inline-flex h-10 items-center rounded-control bg-primary px-5 font-bold text-primary-fg shadow-card">
            Khám phá quán
          </Link>
        </section>
      ) : (
        <ul className="flex flex-col gap-3">
          {saved.map((s) => (
            <SavedRow key={s.id} place={byId.get(s.place_id)} placeId={s.place_id} onRemove={() => toggle(s.place_id)} />
          ))}
        </ul>
      )}
      {error && <p className="text-sm text-danger" role="alert">{error}</p>}
    </main>
  );
}

function SavedRow({ place, placeId, onRemove }: { place: MapPlace | undefined; placeId: string; onRemove: () => void }) {
  return (
    <li className="flex items-center gap-3 rounded-card bg-surface p-3 shadow-card">
      <span className="grid size-11 shrink-0 place-items-center rounded-xl bg-primary-soft text-xl" aria-hidden>
        {categoryIcon(place?.category ?? "")}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-bold">{place?.name ?? "Quán không còn trong dữ liệu"}</p>
        {place && <p className="truncate text-xs text-fg-muted">{[place.category, place.address].filter(Boolean).join(" · ")}</p>}
      </div>
      {place && (
        <Link
          href={placeHref(placeId)}
          className="inline-flex h-9 shrink-0 items-center gap-1.5 rounded-control bg-primary-soft px-3 text-sm font-semibold hover:brightness-95"
        >
          <IconPin className="size-4" aria-hidden />
          <span className="hidden sm:inline">Xem trên bản đồ</span>
          <span className="sm:hidden">Bản đồ</span>
        </Link>
      )}
      <button
        type="button"
        onClick={onRemove}
        aria-label={`Bỏ lưu ${place?.name ?? "quán"}`}
        title="Bỏ lưu"
        className="inline-flex size-9 shrink-0 items-center justify-center rounded-full hover:bg-primary-soft"
      >
        <IconHeart className="size-4.5 fill-accent text-accent" aria-hidden />
      </button>
    </li>
  );
}
