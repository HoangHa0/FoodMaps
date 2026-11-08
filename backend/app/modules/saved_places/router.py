"""M2 saved places, mounted at /api/saved-places. Every endpoint needs login.

Fixed paths (`/lists`) are declared before `/{saved_id}` so they are not read as an id.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.saved_places import service
from app.modules.saved_places.schemas import (
    SavedListIn,
    SavedListOut,
    SavedListUpdateIn,
    SavedPlaceIn,
    SavedPlaceOut,
    SavedPlaceUpdateIn,
)
from app.shared.auth import CurrentUser

router = APIRouter(prefix="/saved-places", tags=["M2 saved places"])

Db = Annotated[AsyncSession, Depends(get_db)]


# ---------- lists ----------


@router.get("/lists", response_model=list[SavedListOut], responses={401: {}})
async def my_lists(user: CurrentUser, db: Db):
    """The user's lists with place counts. The default list is created on the first call."""
    return await service.list_lists(db, user.id)


@router.post("/lists", response_model=SavedListOut, status_code=201, responses={401: {}, 409: {}})
async def create_list(data: SavedListIn, user: CurrentUser, db: Db):
    return await service.create_list(db, user.id, data)


@router.patch("/lists/{list_id}", response_model=SavedListOut, responses={401: {}, 404: {}, 409: {}})
async def update_list(list_id: uuid.UUID, data: SavedListUpdateIn, user: CurrentUser, db: Db):
    return await service.update_list(db, user.id, list_id, data)


@router.delete("/lists/{list_id}", status_code=204, responses={400: {}, 401: {}, 404: {}})
async def delete_list(list_id: uuid.UUID, user: CurrentUser, db: Db) -> Response:
    """Deletes the list and the saved places in it. The default list cannot be deleted (400)."""
    await service.delete_list(db, user.id, list_id)
    return Response(status_code=204)


# ---------- saved places ----------


@router.get("", response_model=list[SavedPlaceOut], responses={401: {}})
async def my_saved_places(user: CurrentUser, db: Db):
    return await service.list_saved(db, user.id)


@router.post("", response_model=SavedPlaceOut, status_code=201, responses={200: {}, 401: {}, 404: {}})
async def save_place(data: SavedPlaceIn, user: CurrentUser, db: Db, response: Response):
    """Save a place (201). Saving an already saved place moves it / updates the note (200)."""
    saved, created = await service.save_place(db, user.id, data)
    if not created:
        response.status_code = 200
    return saved


@router.patch("/{saved_id}", response_model=SavedPlaceOut, responses={401: {}, 404: {}})
async def update_saved_place(saved_id: uuid.UUID, data: SavedPlaceUpdateIn, user: CurrentUser, db: Db):
    return await service.update_saved(db, user.id, saved_id, data)


@router.delete("/{saved_id}", status_code=204, responses={401: {}, 404: {}})
async def delete_saved_place(saved_id: uuid.UUID, user: CurrentUser, db: Db) -> Response:
    await service.delete_saved(db, user.id, saved_id)
    return Response(status_code=204)
