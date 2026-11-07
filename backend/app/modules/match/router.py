from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.match import service
from app.modules.match.schemas import InsightsOut, MapPlace, MatchResponse, RejectIn, WhyOut
from app.shared.contracts import MatchCriteria

router = APIRouter(prefix="/match", tags=["M3 match"])

Db = Annotated[AsyncSession, Depends(get_db)]


# Guests can call these: no CurrentUser dependency.


@router.get("/places", response_model=list[MapPlace])
async def map_places(db: Db) -> list[MapPlace]:
    """List stored FoodMaps places and real coordinates for the public home map."""
    return await service.list_map_places(db)


@router.post("", response_model=MatchResponse)
async def match(criteria: MatchCriteria, db: Db) -> MatchResponse:
    """One best place + up to 3 backups. With USE_STUB_MATCH=true it returns sample data."""
    return await service.match(db, criteria)


@router.post("/reject", response_model=MatchResponse)
async def reject(data: RejectIn, db: Db) -> MatchResponse:
    """'Not Match': reorder the backups the client still holds by the reason given.

    The first place of the response is the new best; the rest are the new backups. The server keeps
    no state: send the place_ids of the backups that are left in `remaining`.
    """
    return await service.reject(db, data)


@router.get("/{place_id}/why", response_model=WhyOut)
async def why(place_id: str, mood: Annotated[str, Query(min_length=1, max_length=300)], db: Db) -> WhyOut:
    """'Why this place?': 3-4 short bullets from the reviews that fit what the user typed.

    The bullets are written offline by `scripts/generate_insights.py`; here they are only chosen by
    embedding similarity to `mood`, so no LLM is called. Empty `points` = the place has no insights yet.
    """
    return await service.why(db, place_id, mood)


@router.get("/{place_id}/insights", response_model=InsightsOut)
async def insights(place_id: str, db: Db) -> InsightsOut:
    """AI Summary, pros/cons, answers to the preset questions and most mentioned dishes of one place.

    Written offline by `scripts/generate_insights.py` and only read here. 404 `insights_not_found`
    = the place exists but has no insights yet (hide the block); 404 `not_found` = unknown place.
    """
    return await service.insights(db, place_id)
