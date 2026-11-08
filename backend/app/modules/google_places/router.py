"""M7 endpoints, mounted at /api/places. Both are public: guests can browse the map."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.google_places import service
from app.modules.google_places.schemas import MapPlaceOut, PlaceSummaryOut

router = APIRouter(prefix="/places", tags=["M7 google places"])

Db = Annotated[AsyncSession, Depends(get_db)]
PlaceId = Annotated[str, Path(min_length=1, max_length=255)]


@router.get("/map", response_model=list[MapPlaceOut])
async def map_places(db: Db):
    """Every place reduced to what the home map needs to draw a pin."""
    return await service.list_map_places(db)


@router.get("/{place_id}/summary", response_model=PlaceSummaryOut, responses={404: {}})
async def place_summary(place_id: PlaceId, db: Db):
    """Basic facts about one place (404 `not_found` when the id is unknown)."""
    return await service.get_place_summary(db, place_id)
