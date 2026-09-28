"""google_places business logic.

Other modules must not import this file; expose what they need through app/shared/.
"""

# Planned contract used by M3, M5 and M6 to display a place card:
#   async def get_place_summary(place_id: str) -> PlaceSummary
#       PlaceSummary: name, photo_url, rating, price_level, google_maps_uri, attribution_required
# Exposed to the frontend as GET /api/places/{place_id}/summary. Results are never stored in the DB.
