from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.errors import todo
from app.modules.match import service
from app.modules.match.schemas import MatchResponse, RejectIn, WhyOut
from app.shared.contracts import MatchCriteria

router = APIRouter(prefix="/match", tags=["M3 match"])

Db = Annotated[AsyncSession, Depends(get_db)]


# Guests can call these: no CurrentUser dependency.


@router.post("", response_model=MatchResponse)
async def match(criteria: MatchCriteria, db: Db) -> MatchResponse:
    """One best place + up to 3 backups. With USE_STUB_MATCH=true it returns sample data."""
    return await service.match(db, criteria)


@router.post("/reject", response_model=MatchResponse)
async def reject(data: RejectIn, db: Db) -> MatchResponse:
    """'Không hợp': rerank the remaining backups by the reason. (Task 7, not implemented yet.)"""
    raise todo()


@router.get("/{place_id}/why", response_model=WhyOut)
async def why(place_id: str, mood: Annotated[str, Query(min_length=1, max_length=300)]) -> WhyOut:
    """'Why this place?' written by Gemini. (Task 5, not implemented yet.)"""
    raise todo()