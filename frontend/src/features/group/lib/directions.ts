/**
 * Google Maps directions deep link (no API key needed; opens the Maps app on phones).
 * `destination` is required by the URL format: pass the team's own name of the place (CandidateOut
 * `name`); Google still routes by `destination_place_id` when it is a real place ID.
 * Docs: https://developers.google.com/maps/documentation/urls/get-started#directions-action
 */
export function directionsUrl(placeId: string, name = "Quán đã chốt"): string {
  const q = new URLSearchParams({ api: "1", destination: name, destination_place_id: placeId });
  return `https://www.google.com/maps/dir/?${q.toString()}`;
}
