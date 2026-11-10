/**
 * Public API of the Food Journey feature (M6 UI).
 *   JourneyScreen        - /journey: plan, save (login), share (no login), library
 *   SharedJourneyScreen  - /journey/shared/[code]: read-only view of a share link
 *   addPlaceToJourney    - "Thêm vào chuyến đi" from any place screen
 *   useJourneyDraft      - the journey being edited (kept in this browser)
 */
export { JourneyScreen } from "./components/JourneyScreen";
export { SharedJourneyScreen } from "./components/SharedJourneyScreen";
export { useJourneyDraft } from "./lib/draft";
export { MAX_STOPS_PER_JOURNEY } from "./lib/limits";

import { draftActions } from "./lib/draft";
/** "added" | "duplicate" (already a stop) | "full" (20 stops) */
export const addPlaceToJourney = (placeId: string) => draftActions.addStop(placeId);
