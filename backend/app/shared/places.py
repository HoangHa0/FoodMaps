"""Read-only contract for the `places` table (owned by M3 / AI Match).

Saved places (M2), Food Journey (M6) and the map endpoints need a place's name and coordinates.
They must not import M3's service, so they read places only through the functions below. If M3
renames a column in `app.modules.match.models.Place`, only `_to_ref` in this file has to change.

Nothing here writes or commits. The name is the team's own (`places.manual_name`, DECISIONS D10);
no Google name, photo or rating passes through this file.
"""

import math
from collections.abc import Iterable

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.match.models import Place

EARTH_RADIUS_M = 6_371_000
METRES_PER_DEGREE = 111_320


class PlaceRef(BaseModel):
    """What other modules may know about a place."""

    model_config = ConfigDict(frozen=True)

    place_id: str
    place_code: str
    name: str  # the team's own name (places.manual_name)
    category: str
    address: str | None = None
    google_maps_url: str | None = None
    lat: float
    lng: float
    price_per_person: int | None = Field(default=None, description="VND")
    tiktok_urls: list[str] = Field(default_factory=list)


class NearbyPlace(PlaceRef):
    distance_m: int


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Straight-line distance in metres between two points."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = (
        math.sin((p2 - p1) / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lng2 - lng1) / 2) ** 2
    )
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def bounding_box(lat: float, lng: float, radius_m: float) -> tuple[float, float, float, float]:
    """(lat_lo, lat_hi, lng_lo, lng_hi) of the square that contains the circle of `radius_m`."""
    dlat = radius_m / METRES_PER_DEGREE
    dlng = radius_m / (METRES_PER_DEGREE * max(math.cos(math.radians(lat)), 1e-6))
    return lat - dlat, lat + dlat, lng - dlng, lng + dlng


def _to_ref(p: Place) -> PlaceRef:
    return PlaceRef(
        place_id=p.place_id,
        place_code=p.place_code,
        name=p.manual_name,
        category=p.category,
        address=p.address,
        google_maps_url=p.google_maps_url,
        lat=p.lat,
        lng=p.lng,
        price_per_person=p.price_per_person,
        tiktok_urls=list(p.tiktok_urls or []),
    )


async def get_place(db: AsyncSession, place_id: str) -> PlaceRef | None:
    row = await db.get(Place, place_id)
    return _to_ref(row) if row is not None else None


async def place_exists(db: AsyncSession, place_id: str) -> bool:
    found = await db.scalar(select(Place.place_id).where(Place.place_id == place_id))
    return found is not None


async def get_places(db: AsyncSession, place_ids: Iterable[str]) -> dict[str, PlaceRef]:
    """Places by id. Unknown ids are simply absent, so callers check with `.get(place_id)`."""
    ids = list(set(place_ids))
    if not ids:
        return {}
    rows = await db.scalars(select(Place).where(Place.place_id.in_(ids)))
    return {p.place_id: _to_ref(p) for p in rows}


async def get_all_places(db: AsyncSession) -> list[PlaceRef]:
    """Every place, in `place_code` order (about 40 now, a few hundred at most)."""
    rows = await db.scalars(select(Place).order_by(Place.place_code))
    return [_to_ref(p) for p in rows]


async def get_places_near(
    db: AsyncSession,
    lat: float,
    lng: float,
    radius_m: float,
    *,
    limit: int | None = None,
) -> list[NearbyPlace]:
    """Places within `radius_m` of a point, nearest first (ties broken by place_id).

    SQL keeps only the bounding box; the exact distance is computed here, as AI Match does.
    """
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(lat, lng, radius_m)
    stmt = select(Place).where(
        Place.lat.between(lat_lo, lat_hi),
        Place.lng.between(lng_lo, lng_hi),
    )
    found: list[NearbyPlace] = []
    for p in await db.scalars(stmt):
        d = haversine_m(lat, lng, p.lat, p.lng)
        if d <= radius_m:
            found.append(NearbyPlace(**_to_ref(p).model_dump(), distance_m=round(d)))
    found.sort(key=lambda n: (n.distance_m, n.place_id))
    return found[:limit] if limit is not None else found
