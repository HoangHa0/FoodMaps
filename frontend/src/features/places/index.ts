/**
 * Feature: places (M7). Public components:
 *   OriginPicker      - "where do you want to eat?": my location, a quick district or any typed address
 *                       (backend `geo` module) + radius. Used by AI Match and by the Group Session criteria.
 * Planned public components:
 *   PlaceSummaryCard  - name/photo/rating fetched live from GET /api/places/{id}/summary
 *   GoogleAttribution - official "Powered by Google" attribution
 * Reused by the match and group features to display any Google place.
 */
export { OriginPicker, type OriginPickerProps } from "./components/OriginPicker";
export type { Origin } from "./lib/origin";
