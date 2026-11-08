"""google_places business logic (M7): the home map pins and the basic facts of one place.

Other modules must not import this file; expose what they need through app/shared/.

Both functions read the `places` table through the shared read-only contract (`app.shared.places`),
so this module never imports M3's service or models. The name is the team's own
(`places.manual_name`); no Google name, photo or rating is read or stored here.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import not_found
from app.modules.google_places.schemas import MapPlaceOut, PlaceSummaryOut
from app.shared.places import get_all_places, get_place


async def list_map_places(db: AsyncSession) -> list[MapPlaceOut]:
    """Every place reduced to the pin fields, in `place_code` order."""
    return [
        MapPlaceOut(place_id=p.place_id, name=p.name, category=p.category, lat=p.lat, lng=p.lng)
        for p in await get_all_places(db)
    ]


async def get_place_summary(db: AsyncSession, place_id: str) -> PlaceSummaryOut:
    """Basic facts about one place; 404 `not_found` when the id is unknown."""
    p = await get_place(db, place_id)
    if p is None:
        raise not_found("Quán")
    return PlaceSummaryOut(
        place_id=p.place_id,
        name=p.name,
        category=p.category,
        address=p.address,
        google_maps_url=p.google_maps_url,
        lat=p.lat,
        lng=p.lng,
        price_per_person=p.price_per_person,
        tiktok_urls=list(p.tiktok_urls or []),
    )
