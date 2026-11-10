/**
 * Public API of the match feature (AI Match UI; backend M3).
 *   MatchSearchProvider - wraps the app: overlay + result sheet, shared by every trigger
 *   MatchSearchBar      - the search bar of the desktop top bar
 *   useOpenMatchSearch  - open the overlay from anywhere (phone tab bar button)
 */
export { MatchSearchBar, MatchSearchProvider, useOpenMatchSearch } from "./components/MatchSearch";
/** PlaceInsights - AI summary block of one place (pros/cons, questions, dishes); any place screen can show it */
export { PlaceInsights } from "./components/PlaceInsights";
