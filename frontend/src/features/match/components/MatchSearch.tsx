"use client";

import { usePathname, useRouter } from "next/navigation";
import { useCallback, useState } from "react";

import type { Origin } from "@/features/places";
import { ReviewForm } from "@/features/reviews";
import { Sheet } from "@/ui";

import type { MatchCriteria } from "../api";
import { useMatchSearch, useWhy } from "../hooks/useMatchSearch";
import { directionsUrl } from "../lib/options";
import { MatchOverlay, MatchResultSheet, SearchTrigger } from "./views";

/**
 * Container of AI Match (M3 UI), mounted once in the top bar so it lives across pages:
 *   collapsed bar -> full-screen overlay (mood + options) -> bottom sheet with ONE place over the
 *   map, "Why this place?", directions, "Không hợp" (4 reasons -> rerank of the backups) and a
 *   review form (M4). A search started on another page returns to the map (home) first.
 */
export function MatchSearch() {
  const router = useRouter();
  const pathname = usePathname();
  const { session, search, reject, rejectCurrent, close } = useMatchSearch();
  const [overlayOpen, setOverlayOpen] = useState(false);
  const [reviewOpen, setReviewOpen] = useState(false);
  const best = session?.best ?? null;
  const why = useWhy(best?.place_id, session?.criteria.mood);

  const openOverlay = useCallback(() => setOverlayOpen(true), []);
  const closeOverlay = useCallback(() => setOverlayOpen(false), []);

  function submit(criteria: MatchCriteria, origin: Origin | null) {
    search.mutate({ criteria, origin }, {
      onSuccess: () => {
        setOverlayOpen(false);
        if (pathname !== "/") router.push("/"); // the result floats over the map
      },
    });
  }

  return (
    <>
      <SearchTrigger onOpen={openOverlay} />

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
          why={why.data}
          whyLoading={why.isLoading}
          directionsUrl={best ? directionsUrl(best.place_id, best.name) : ""}
          // distances are measured from the chosen point: name it unless it is the user's own position
          originLabel={session.origin && session.origin.source !== "gps" ? session.origin.label : undefined}
          onClose={close}
          onSearchAgain={openOverlay}
          onReject={rejectCurrent}
          rejecting={reject.isPending}
          rejectError={reject.error?.message}
          onWriteReview={() => setReviewOpen(true)}
        />
      )}

      {best && (
        <Sheet open={reviewOpen} onClose={() => setReviewOpen(false)} modal>
          {/* ReviewForm handles guests itself (login sheet), then edits or creates the user's review */}
          <ReviewForm placeId={best.place_id} placeName={best.name ?? undefined} onSaved={() => setReviewOpen(false)} />
        </Sheet>
      )}
    </>
  );
}
