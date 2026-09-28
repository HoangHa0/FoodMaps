"""Contract between AI Match (M3, provider) and its consumers: Group Session (M5) and
Food Journey (M6).

Consumers depend only on `CandidateProvider`. While the real M3 pipeline is not ready,
`USE_STUB_MATCH=true` returns sample data, so no module is blocked by another.
"""

from typing import Protocol

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class MatchCriteria(BaseModel):
    """Search criteria shared by AI Match, Group Session and Food Journey."""

    mood: str = Field(min_length=1, max_length=300, examples=["quán yên tĩnh để học bài"])
    origin: GeoPoint | None = None
    radius_m: int = Field(default=2000, ge=200, le=10000)
    price_min: int | None = Field(default=None, ge=0, description="VND per person")
    price_max: int | None = Field(default=None, ge=0, description="VND per person")
    categories: list[str] = Field(default_factory=list, description="e.g. ['cafe', 'main_meal']")


class PlaceCandidate(BaseModel):
    """One candidate place.

    Contains only data we are allowed to store (the Google `place_id`) plus data we generate
    ourselves (score, tags). Name, photos and rating from Google must be fetched live through
    the `google_places` module (M7) when displayed.
    """

    place_id: str
    match_score: float = Field(ge=0, le=1)
    tags: list[str] = Field(default_factory=list, description="short system-generated tags")
    distance_m: int | None = None


class CandidateProvider(Protocol):
    async def find_candidates(self, criteria: MatchCriteria, k: int) -> list[PlaceCandidate]:
        """Return at most k places, sorted by match_score descending."""
        ...


class StubCandidateProvider:
    """Deterministic sample data for developing and testing M5 and M6."""

    _FAKE = [
        ("stub_place_cafe_yen_tinh", ["yên tĩnh", "học bài"]),
        ("stub_place_bun_cha", ["ăn chính", "dưới 100k"]),
        ("stub_place_tra_chanh", ["đông vui", "rẻ"]),
        ("stub_place_lau_nuong", ["đi nhóm", "ăn tối"]),
        ("stub_place_banh_ngot", ["tráng miệng", "date"]),
        ("stub_place_pho_dem", ["ăn khuya"]),
        ("stub_place_ca_phe_trung", ["cà phê", "đặc sản"]),
    ]

    async def find_candidates(self, criteria: MatchCriteria, k: int) -> list[PlaceCandidate]:
        return [
            PlaceCandidate(
                place_id=pid,
                match_score=round(0.95 - i * 0.07, 2),
                tags=tags,
                distance_m=300 + i * 250,
            )
            for i, (pid, tags) in enumerate(self._FAKE[:k])
        ]


def get_candidate_provider() -> CandidateProvider:
    """FastAPI dependency.

    M3 only has to make `app.modules.match.service.MatchCandidateProvider` satisfy the
    Protocol above; no other file needs to change when switching from the stub.
    """
    from app.core.config import get_settings

    if get_settings().use_stub_match:
        return StubCandidateProvider()
    from app.modules.match.service import MatchCandidateProvider  # noqa: PLC0415

    return MatchCandidateProvider()
