"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { VietMap } from "@/features/map";
import { ApiError } from "@/lib/api/errors";
import { Button, Spinner } from "@/ui";

import { useSharedJourney } from "../hooks/useJourneys";
import { draftActions, useJourneyDraft } from "../lib/draft";
import { hhmm } from "../lib/route";
import { useStopViews } from "./JourneyScreen";
import { DirectionsLinks, formatPlannedDate, formatShortDate, JourneySummary, Panel, ReplaceBanner, StopTimeline } from "./views";

/** /journey/shared/[code]: what anyone holding a share link sees (read-only, no account needed). */
export function SharedJourneyScreen({ code }: { code: string }) {
  const router = useRouter();
  const shared = useSharedJourney(code);
  const draft = useJourneyDraft();
  const [selected, setSelected] = useState<string | null>(null);
  const [confirm, setConfirm] = useState(false);

  const stops = useMemo(
    () =>
      (shared.data?.stops ?? []).map((s) => ({
        key: `${s.stop_order}-${s.place.place_id}`,
        place_id: s.place.place_id,
        planned_time: hhmm(s.planned_time),
        note: s.note ?? "",
      })),
    [shared.data],
  );
  const { views, mapPlaces, totalDistance, cost, links } = useStopViews(stops);

  function copy() {
    if (!shared.data) return;
    draftActions.copyShared(shared.data);
    router.push("/journey");
  }

  if (shared.isPending)
    return (
      <main className="flex flex-1 items-center justify-center p-10">
        <Spinner />
      </main>
    );

  if (shared.isError) {
    const gone = shared.error instanceof ApiError && shared.error.status === 404;
    return (
      <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center gap-3 px-4 py-12 text-center">
        <p className="text-4xl" aria-hidden>
          🔗
        </p>
        <h1 className="text-xl font-bold">{gone ? "Link không tồn tại hoặc đã hết hạn" : "Không mở được lịch trình"}</h1>
        <p className="text-sm text-fg-muted">
          {gone ? "Link chia sẻ chỉ dùng được 7 ngày. Hãy nhờ người gửi tạo link mới." : shared.error.message}
        </p>
        <div className="mt-2 flex gap-2">
          {!gone && <Button onClick={() => void shared.refetch()}>Thử lại</Button>}
          <Link href="/journey" className="inline-flex h-10 items-center rounded-control border border-border bg-surface px-5 font-bold">
            Lập lịch trình của bạn
          </Link>
        </div>
      </main>
    );
  }

  const j = shared.data;
  return (
    <main className="grid gap-6 px-4 py-4 md:px-6 xl:grid-cols-[minmax(0,1fr)_26rem] xl:items-start">
      <div className="flex min-w-0 flex-col gap-5">
        <header>
          <p className="text-sm font-semibold text-fg-muted">Lịch trình được chia sẻ</p>
          <h1 className="font-display text-3xl font-bold">{j.title ?? "Chuyến đi ẩm thực"}</h1>
          <p className="mt-1 text-sm text-fg-muted">
            {j.planned_date && `${formatPlannedDate(j.planned_date)} · `}
            {j.stops.length} điểm dừng · Link dùng được tới {formatShortDate(j.expires_at)}
          </p>
        </header>

        {confirm && (
          <ReplaceBanner
            message="Bạn đang soạn một lịch trình chưa lưu. Lưu bản này thành lịch trình của bạn sẽ thay thế bản đang soạn."
            confirmLabel="Vẫn thay thế"
            onConfirm={copy}
            onCancel={() => setConfirm(false)}
          />
        )}

        <Panel>
          {j.missing_places > 0 && (
            <p className="rounded-card bg-primary-soft p-3 text-sm" role="status">
              {j.missing_places} quán trong lịch trình gốc không còn trong dữ liệu FoodMaps nên đã được bỏ qua.
            </p>
          )}
          <StopTimeline stops={views} readOnly selectedPlaceId={selected} onSelect={setSelected} />
          <JourneySummary stopCount={j.stops.length} totalCost={cost.total} unknownCost={cost.unknown} totalDistance={totalDistance} />
          <div className="flex flex-wrap gap-2">
            <DirectionsLinks links={links} />
            <Button
              size="lg"
              variant="secondary"
              onClick={() => (draft.dirty && (draft.stops.length > 0 || draft.title.trim()) ? setConfirm(true) : copy())}
              data-testid="journey-copy-shared"
            >
              Lưu thành lịch trình của tôi
            </Button>
          </div>
        </Panel>
      </div>

      <aside className="xl:sticky xl:top-4" aria-label="Bản đồ lịch trình">
        <div className="relative h-72 overflow-hidden rounded-card shadow-card sm:h-96 xl:h-[min(calc(100dvh-2rem),720px)]">
          <VietMap places={mapPlaces} selectedId={selected} onSelect={setSelected} onBackgroundClick={() => setSelected(null)} />
        </div>
      </aside>
    </main>
  );
}
