"""google_places API contract (Pydantic request/response models)."""

from pydantic import BaseModel, Field


class MapPlaceOut(BaseModel):
    """One pin on the home map: only what is needed to draw and select it."""

    place_id: str
    name: str = Field(description="the team's own name (places.manual_name)")
    category: str
    lat: float
    lng: float


class PlaceSummaryOut(BaseModel):
    """Basic facts about one place, for the place panel and for cards in other features.

    Ratings and review summaries are not here: they come from M4 (`/api/reviews/analysis/{place_id}`)
    and M3 (`/api/match/{place_id}/insights`).
    """

    place_id: str
    name: str = Field(description="the team's own name (places.manual_name)")
    category: str
    address: str | None = None
    google_maps_url: str | None = Field(default=None, description="link for the 'open in Google Maps' button")
    lat: float
    lng: float
    price_per_person: int | None = Field(default=None, description="VND per person")
    tiktok_urls: list[str] = Field(default_factory=list)
