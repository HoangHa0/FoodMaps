"use client";

import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";

import { useMe, useRequireAuth } from "@/features/auth";
import { categoryIcon, PlaceSearchBox, suggestPlaces, usePlaces, VietMap } from "@/features/map";
import { ApiError } from "@/lib/api/errors";
import { Button, IconShare, Sheet, useToast } from "@/ui";

import { useDeleteJourney, useJourneyLibrary, useOpenJourney, useSaveJourney, useShareJourney } from "../hooks/useJourneys";
import { type Draft, draftActions, toJourneyIn, useJourneyDraft } from "../lib/draft";
import { MAX_JOURNEYS_PER_USER, MAX_STOPS_PER_JOURNEY } from "../lib/limits";
import { buildStopViews, type StopInput } from "../lib/stops";
import {
  DirectionsLinks,
  EmptyStops,
  JourneyHeader,
  JourneySummary,
  LibraryList,
  MetaFields,
  Panel,
  ReplaceBanner,
  type SaveState,
  ShareResult,
  StopTimeline,
} from "./views";

/** The stops with their places, legs, time checks and totals, recomputed when either changes. */
export function useStopViews(stops: readonly StopInput[]) {
  const places = usePlaces();
  return useMemo(() => buildStopViews(stops, places.data ?? []), [stops, places.data]);
}

const hasContent = (d: Draft) => d.stops.length > 0 || d.title.trim() !== "";

/**
 * /journey: plan a food journey (stops, times, notes), see distance and cost, open walking
 * directions in Google Maps, save it to the account (login), share a read-only link (no login),
 * and reopen saved journeys. The draft lives in this browser until it is saved (see lib/draft).
 */
export function JourneyScreen() {
  const router = useRouter();
  const draft = useJourneyDraft();
  const places = usePlaces();
  const { data: me } = useMe();
  const guard = useRequireAuth();
  const toast = useToast();

  const library = useJourneyLibrary();
  const save = useSaveJourney();
  const open = useOpenJourney();
  const del = useDeleteJourney();
  const share = useShareJourney();

  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [confirm, setConfirm] = useState<{ message: string; label: string; run: () => void } | null>(null);
  const [shared, setShared] = useState<{ url: string; expiresAt: string } | null>(null);
  const [copied, setCopied] = useState(false);

  const { views, mapPlaces, totalDistance, cost, links } = useStopViews(draft.stops);

  const inDraft = useMemo(() => new Set(draft.stops.map((s) => s.place_id)), [draft.stops]);
  const suggestions = useMemo(
    () =>
      suggestPlaces(
        (places.data ?? []).filter((p) => !inDraft.has(p.place_id)),
        query,
      ).map((p) => ({ place: p, icon: categoryIcon(p.category) })),
    [places.data, inDraft, query],
  );
  const full = draft.stops.length >= MAX_STOPS_PER_JOURNEY;

  const saveState: SaveState = draft.journeyId
    ? draft.dirty
      ? "changed"
      : "saved"
    : hasContent(draft)
      ? "unsaved"
      : "empty";

  /** Replacing the draft: ask first when it has changes that are not saved anywhere. */
  function replaceDraft(message: string, label: string, run: () => void) {
    if (draft.dirty && hasContent(draft)) setConfirm({ message, label, run });
    else run();
  }

  function addStop(placeId: string) {
    const r = draftActions.addStop(placeId);
    if (r === "full") toast(`Mỗi lịch trình có tối đa ${MAX_STOPS_PER_JOURNEY} điểm dừng.`, { tone: "error" });
    setSelected(placeId);
  }

  function onSave() {
    guard(() => {
      const savedRev = draft.rev; // edits made while saving must stay "changed"
      save.mutate(
        { journeyId: draft.journeyId, body: toJourneyIn(draft) },
        {
          onSuccess: (j) => {
            draftActions.markSaved(j.id, savedRev);
            toast(draft.journeyId ? "Đã lưu thay đổi" : "Đã lưu lịch trình vào tài khoản");
          },
          onError: (e) => {
            if (e instanceof ApiError && e.status === 404 && draft.journeyId) {
              draftActions.detach(); // deleted elsewhere: keep the content as a new journey
              toast("Lịch trình gốc không còn nữa. Bấm Lưu lần nữa để lưu thành lịch trình mới.", { tone: "info" });
            } else {
              toast(e.message, { tone: "error" });
            }
          },
        },
      );
    });
  }

  function onShare() {
    share.mutate(toJourneyIn(draft), {
      onSuccess: (s) => {
        setCopied(false);
        setShared({ url: `${window.location.origin}/journey/shared/${s.code}`, expiresAt: s.expires_at });
      },
      onError: (e) => toast(e.message, { tone: "error" }),
    });
  }

  function onOpen(id: string) {
    replaceDraft("Lịch trình đang soạn có thay đổi chưa lưu. Mở lịch trình khác sẽ bỏ các thay đổi đó.", "Vẫn mở", () =>
      open.mutate(id, {
        onSuccess: (j) => {
          draftActions.loadSaved(j);
          setSelected(null);
          window.scrollTo({ top: 0, behavior: "smooth" });
        },
        onError: (e) => toast(e.message, { tone: "error" }),
      }),
    );
  }

  function onDelete(id: string) {
    del.mutate(id, {
      onSuccess: () => {
        if (draft.journeyId === id) draftActions.detach();
        toast("Đã xoá lịch trình", { tone: "info" });
      },
      onError: (e) => toast(e.message, { tone: "error" }),
    });
  }

  const libraryRows = (library.data ?? []).map((j) => ({ ...j, open: j.id === draft.journeyId }));

  return (
    <main className="grid gap-6 px-4 py-4 md:px-6 xl:grid-cols-[minmax(0,1fr)_26rem] xl:items-start">
      <div className="flex min-w-0 flex-col gap-5">
        <JourneyHeader
          saveState={saveState}
          onNew={hasContent(draft) ? () => replaceDraft("Lịch trình đang soạn có thay đổi chưa lưu. Tạo lịch trình mới sẽ bỏ các thay đổi đó.", "Tạo mới", draftActions.reset) : undefined}
        />

        {confirm && (
          <ReplaceBanner
            message={confirm.message}
            confirmLabel={confirm.label}
            onConfirm={() => {
              confirm.run();
              setConfirm(null);
            }}
            onCancel={() => setConfirm(null)}
          />
        )}

        <Panel>
          <MetaFields title={draft.title} onTitle={draftActions.setTitle} date={draft.planned_date} onDate={draftActions.setDate} />

          <div className="flex flex-col gap-1.5">
            <span className="text-sm font-semibold">
              Điểm dừng{" "}
              <span className="font-normal text-fg-muted">
                ({draft.stops.length}/{MAX_STOPS_PER_JOURNEY})
              </span>
            </span>
            {full ? (
              <p className="text-sm text-fg-muted">Lịch trình đã đủ {MAX_STOPS_PER_JOURNEY} điểm. Bỏ bớt một điểm để thêm quán khác.</p>
            ) : (
              <PlaceSearchBox
                query={query}
                onQuery={setQuery}
                suggestions={suggestions}
                onPick={addStop}
                clearOnPick
                label="Thêm quán vào lịch trình"
                placeholder="Thêm quán: gõ tên hoặc địa chỉ…"
                emptyHint="Quán đã có trong lịch trình sẽ không hiện lại."
                data-testid="journey-add-stop"
              />
            )}
          </div>

          {draft.stops.length === 0 ? (
            <EmptyStops />
          ) : (
            <StopTimeline
              stops={views}
              selectedPlaceId={selected}
              onSelect={setSelected}
              onTime={(key, v) => draftActions.updateStop(key, { planned_time: v })}
              onNote={(key, v) => draftActions.updateStop(key, { note: v })}
              onMove={draftActions.moveStop}
              onRemove={draftActions.removeStop}
            />
          )}

          {draft.stops.length > 0 && (
            <>
              <JourneySummary stopCount={draft.stops.length} totalCost={cost.total} unknownCost={cost.unknown} totalDistance={totalDistance} />
              <div className="flex flex-wrap gap-2">
                <Button
                  size="lg"
                  onClick={onSave}
                  loading={save.isPending}
                  disabled={saveState === "saved"}
                  data-testid="journey-save"
                >
                  {saveState === "saved" ? "Đã lưu" : draft.journeyId ? "Lưu thay đổi" : "Lưu lịch trình"}
                </Button>
                <Button size="lg" variant="secondary" onClick={onShare} loading={share.isPending} data-testid="journey-share">
                  <IconShare className="size-4" aria-hidden /> Chia sẻ
                </Button>
              </div>
              <DirectionsLinks links={links} />
              {draft.stops.length === 1 && <p className="text-xs text-fg-muted">Thêm điểm thứ hai để có chỉ đường.</p>}
            </>
          )}
        </Panel>

        <LibraryList
          rows={libraryRows}
          max={MAX_JOURNEYS_PER_USER}
          loading={!!me && library.isPending}
          error={library.error?.message}
          onRetry={() => void library.refetch()}
          onOpen={onOpen}
          onDelete={onDelete}
          deletingId={del.isPending ? (del.variables ?? null) : null}
          guest={!me}
          onLogin={() => router.push("/login?next=%2Fjourney")}
        />
      </div>

      <aside className="xl:sticky xl:top-4" aria-label="Bản đồ lịch trình">
        <div className="relative h-72 overflow-hidden rounded-card shadow-card sm:h-96 xl:h-[min(calc(100dvh-2rem),720px)]">
          <VietMap places={mapPlaces} selectedId={selected} onSelect={(id) => {
            setSelected(id);
            document.getElementById(`stop-${id}`)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
          }} onBackgroundClick={() => setSelected(null)} />
          {mapPlaces.length === 0 && (
            <p className="pointer-events-none absolute inset-x-4 top-4 z-10 rounded-card bg-surface-raised/95 p-3 text-center text-sm text-fg-muted shadow-card">
              Các điểm dừng sẽ hiện trên bản đồ.
            </p>
          )}
        </div>
      </aside>

      <Sheet open={!!shared} onClose={() => setShared(null)} title="Chia sẻ lịch trình" modal>
        {shared && (
          <ShareResult
            url={shared.url}
            expiresAt={shared.expiresAt}
            copied={copied}
            onCopy={() => {
              void navigator.clipboard?.writeText(shared.url).then(
                () => setCopied(true),
                () => toast("Không sao chép được, hãy chọn và sao chép link bằng tay.", { tone: "error" }),
              );
            }}
            onNativeShare={
              typeof navigator !== "undefined" && "share" in navigator
                ? () => void navigator.share({ title: draft.title || "Lịch trình FoodMaps", url: shared.url }).catch(() => {})
                : undefined
            }
          />
        )}
      </Sheet>
    </main>
  );
}
