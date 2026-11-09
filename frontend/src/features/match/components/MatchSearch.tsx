"use client";

import { usePathname, useRouter } from "next/navigation";
import { createContext, type ReactNode, useCallback, useContext, useMemo, useState } from "react";

import { useRequireAuth } from "@/features/auth";
import { placeHref } from "@/features/map";
import type { Origin } from "@/features/places";
import { ReviewForm } from "@/features/reviews";
import { useSavedPlaces } from "@/features/saved";
import { Portal, Sheet } from "@/ui";

import type { MatchCriteria } from "../api";
import { useMatchSearch, useWhy } from "../hooks/useMatchSearch";
import { directionsUrl } from "../lib/options";
import { MatchOverlay, MatchResultSheet, SearchTrigger } from "./views";

const OpenContext = createContext<(() => void) | null>(null);

/**
 * AI Match (M3 UI), mounted once around the app so it lives across pages:
 *   any trigger (top bar on desktop, round button of the phone tab bar) -> full-screen overlay
 *   (mood + options) -> draggable sheet with ONE place over the map, "Vì sao hợp với bạn?",
 *   directions, save, "Không hợp" (4 reasons -> rerank of the backups) and a review form (M4).
 * The result opens the home map on that place (/?quan=<place_id>).
 */
export function MatchSearchProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { session, search, reject, rejectCurrent, close } = useMatchSearch();
  const [overlayOpen, setOverlayOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const best = session?.best ?? null;
  const why = useWhy(best?.place_id, session?.criteria.mood);
  const { savedIds, toggle: toggleSave } = useSavedPlaces();
  const guard = useRequireAuth(); // guests log in first, then the review form opens

  const openOverlay = useCallback(() => setOverlayOpen(true), []);
  const closeOverlay = useCallback(() => setOverlayOpen(false), []);

  function showOnMap(placeId: string | undefined) {
    if (placeId) router.replace(placeHref(placeId), { scroll: false });
    else if (pathname !== "/") router.push("/");
  }

  function submit(criteria: MatchCriteria, origin: Origin | null) {
    search.mutate({ criteria, origin }, {
      onSuccess: (s) => {
        setOverlayOpen(false);
        showOnMap(s.best?.place_id); // the result floats over the map, on that place
      },
    });
  }

  function onReject(reason: Parameters<typeof rejectCurrent>[0]) {
    rejectCurrent(reason);
  }

  return (
    <OpenContext.Provider value={openOverlay}>
      {children}

      {/* portal: these fixed layers must not be positioned inside a sticky / blurred ancestor */}
      <Portal>
        {overlayOpen && (
          <MatchOverlay
            initial={session?.criteria}
            initialOrigin={session?.origin}
            onSubmit={submit}
            onClose={closeOverlay}
            loading={search.isPending}
            error={search.error?.message}
          />
        )}

        {session && !overlayOpen && !reviewOpen && (
          <MatchResultSheet
            result={best}
            backupsLeft={session.backups.length}
            emptyAfter={session.emptyAfter}
            originLabel={session.origin && session.origin.source !== "gps" ? session.origin.label : undefined}
            why={why.data}
            whyLoading={why.isLoading}
            directionsUrl={best ? directionsUrl(best.place_id, best.name) : ""}
            onClose={close}
            onSearchAgain={openOverlay}
            onReject={onReject}
            rejecting={reject.isPending}
            rejectError={reject.error?.message}
            onWriteReview={() => guard(() => setReviewOpen(true))}
            onShowOnMap={() => best && showOnMap(best.place_id)}
            saved={!!best && savedIds.has(best.place_id)}
            onToggleSave={() => best && toggleSave(best.place_id, best.name ?? undefined)}
          />
        )}

        {best && (
          <Sheet open={reviewOpen} onClose={() => setReviewOpen(false)} title={`Đánh giá ${best.name ?? "quán"}`} modal>
            {/* ReviewForm handles guests itself (login sheet), then edits or creates the user's review */}
            <ReviewForm placeId={best.place_id} onSaved={() => setReviewOpen(false)} bare />
          </Sheet>
        )}
      </Portal>
    </OpenContext.Provider>
  );
}

/** Opens the AI search overlay (for buttons outside the match feature, e.g. the phone tab bar). */
export function useOpenMatchSearch(): () => void {
  const open = useContext(OpenContext);
  return useMemo(() => open ?? (() => {}), [open]);
}

/** The search bar of the desktop top bar. */
export function MatchSearchBar() {
  const open = useOpenMatchSearch();
  return <SearchTrigger onOpen={open} />;
}
