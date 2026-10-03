/**
 * Google Maps directions deep link (no API key needed; opens the Maps app on phones).
 * `destination` is required by the URL format; once M7 provides the live place name, pass it as
 * `name` (Google place names must not be stored, so it is never read from our database).
 * Docs: https://developers.google.com/maps/documentation/urls/get-started#directions-action
 */
export function directionsUrl(placeId: string, name = "Quán đã chốt"): string {
  const q = new URLSearchParams({ api: "1", destination: name, destination_place_id: placeId });
  return `https://www.google.com/maps/dir/?${q.toString()}`;
}
