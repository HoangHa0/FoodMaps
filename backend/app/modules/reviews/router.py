"""M4 endpoints, mounted at /api/reviews.

Guests can read (list, analysis); writing needs a login. Only the author can PUT/DELETE.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.reviews import service
from app.modules.reviews.schemas import (
    ReportIn,
    ReportOut,
    ReviewAnalysisOut,
    ReviewIn,
    ReviewListOut,
    ReviewOut,
    ReviewUpdateIn,
)
from app.shared.auth import CurrentUser, OptionalUser

router = APIRouter(prefix="/reviews", tags=["M4 reviews"])

Db = Annotated[AsyncSession, Depends(get_db)]
PlaceId = Annotated[str, Query(min_length=1, max_length=255)]


@router.get("", response_model=ReviewListOut, responses={404: {}})
async def list_reviews(
    place_id: PlaceId,
    user: OptionalUser,
    db: Db,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """Visible reviews written on the website, newest first (guests allowed).
    `is_mine` marks the caller's own.

    Internal reviews imported from the team's form are not listed; they only feed Match and Analysis.
    """
    return await service.list_reviews(db, place_id, user, limit, offset)


@router.get("/mine", response_model=ReviewOut, responses={401: {}, 404: {}})
async def my_review(place_id: PlaceId, user: CurrentUser, db: Db):
    """The caller's own review of a place (any status). 404 = they have not reviewed it yet."""
    return await service.my_review(db, user, place_id)


@router.get("/analysis/{place_id}", response_model=ReviewAnalysisOut, responses={404: {}})
async def analysis(place_id: str, db: Db):
    """Review Analysis: 4 aspect scores, most mentioned dishes, pros/cons, tags (guests allowed)."""
    return await service.place_analysis(db, place_id)


@router.post("", response_model=ReviewOut, status_code=201, responses={401: {}, 404: {}, 409: {}, 429: {}})
async def create_review(data: ReviewIn, user: CurrentUser, db: Db):
    """Write a review. 409 if the caller already reviewed this place (edit it instead); 429 if too fast.

    A review that trips the text filter is saved with status `flagged`: only its author sees it.
    """
    return await service.create_review(db, user, data)


@router.put("/{review_id}", response_model=ReviewOut, responses={401: {}, 403: {}, 404: {}})
async def update_review(review_id: uuid.UUID, data: ReviewUpdateIn, user: CurrentUser, db: Db):
    """Replace the editable fields of the caller's own review. Not rate limited."""
    return await service.update_review(db, user, review_id, data)


@router.delete("/{review_id}", status_code=204, responses={401: {}, 403: {}, 404: {}})
async def delete_review(review_id: uuid.UUID, user: CurrentUser, db: Db) -> Response:
    """Delete the caller's own review."""
    await service.delete_review(db, user, review_id)
    return Response(status_code=204)


@router.post(
    "/{review_id}/report",
    response_model=ReportOut,
    status_code=201,
    responses={401: {}, 404: {}, 409: {}, 422: {}},
)
async def report_review(review_id: uuid.UUID, data: ReportIn, user: CurrentUser, db: Db):
    """'Báo cáo' button. One report per person per review; 3 different reporters flag it."""
    return await service.report_review(db, user, review_id, data)
