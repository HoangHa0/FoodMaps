"""saved_places business logic.

Other modules must not import this file; expose what they need through app/shared/.

Rules (see the plan, section 2.2):
- Every query is filtered by the current user. Someone else's id behaves like an unknown id: 404.
- The default list "Yêu thích" is created on first use and cannot be deleted.
- Saving a place that is already saved moves it / updates the note instead of failing.
- `get_db` never commits, so every write path ends with `commit()`.
"""

import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, not_found
from app.modules.saved_places.models import SavedList, SavedPlace
from app.modules.saved_places.schemas import (
    SavedListIn,
    SavedListOut,
    SavedListUpdateIn,
    SavedPlaceIn,
    SavedPlaceOut,
    SavedPlaceUpdateIn,
)
from app.shared.places import place_exists

DEFAULT_LIST_NAME = "Yêu thích"
DEFAULT_LIST_ICON = "❤️"


def _duplicate_name() -> AppError:
    return AppError(409, "list_name_taken", "Bạn đã có danh sách tên này")


def _list_out(row: SavedList, place_count: int) -> SavedListOut:
    return SavedListOut(
        id=row.id,
        name=row.name,
        icon=row.icon,
        position=row.position,
        is_default=row.is_default,
        place_count=place_count,
    )


def _saved_out(row: SavedPlace, list_icon: str) -> SavedPlaceOut:
    return SavedPlaceOut(
        id=row.id,
        place_id=row.place_id,
        list_id=row.list_id,
        list_icon=list_icon,
        note=row.note,
        created_at=row.created_at,
    )


async def _default_list(db: AsyncSession, user_id: uuid.UUID) -> SavedList | None:
    return await db.scalar(
        select(SavedList).where(SavedList.user_id == user_id, SavedList.is_default.is_(True))
    )


async def ensure_default_list(db: AsyncSession, user_id: uuid.UUID) -> SavedList:
    """The user's default list, created on first use (two requests racing end up with one)."""
    existing = await _default_list(db, user_id)
    if existing is not None:
        return existing
    created = SavedList(
        user_id=user_id, name=DEFAULT_LIST_NAME, icon=DEFAULT_LIST_ICON, position=0, is_default=True
    )
    db.add(created)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # either another request created it, or the user renamed another list to "Yêu thích"
        existing = await _default_list(db, user_id)
        if existing is None:
            raise _duplicate_name() from None
        return existing
    await db.refresh(created)
    return created


async def _get_list(db: AsyncSession, user_id: uuid.UUID, list_id: uuid.UUID) -> SavedList:
    row = await db.scalar(select(SavedList).where(SavedList.id == list_id, SavedList.user_id == user_id))
    if row is None:
        raise not_found("Danh sách")
    return row


async def _count(db: AsyncSession, list_id: uuid.UUID) -> int:
    return await db.scalar(select(func.count()).where(SavedPlace.list_id == list_id)) or 0


# ---------- lists ----------


async def list_lists(db: AsyncSession, user_id: uuid.UUID) -> list[SavedListOut]:
    await ensure_default_list(db, user_id)
    counts = (
        select(SavedPlace.list_id, func.count().label("n"))
        .where(SavedPlace.user_id == user_id)
        .group_by(SavedPlace.list_id)
        .subquery()
    )
    rows = await db.execute(
        select(SavedList, func.coalesce(counts.c.n, 0))
        .outerjoin(counts, counts.c.list_id == SavedList.id)
        .where(SavedList.user_id == user_id)
        .order_by(SavedList.position, SavedList.created_at)
    )
    return [_list_out(row, n) for row, n in rows]


async def create_list(db: AsyncSession, user_id: uuid.UUID, data: SavedListIn) -> SavedListOut:
    await ensure_default_list(db, user_id)
    next_position = (
        await db.scalar(select(func.max(SavedList.position)).where(SavedList.user_id == user_id))
    ) or 0
    row = SavedList(user_id=user_id, name=data.name.strip(), icon=data.icon, position=next_position + 1)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise _duplicate_name() from None
    await db.refresh(row)
    return _list_out(row, 0)


async def update_list(
    db: AsyncSession, user_id: uuid.UUID, list_id: uuid.UUID, data: SavedListUpdateIn
) -> SavedListOut:
    row = await _get_list(db, user_id, list_id)
    changes = data.model_dump(exclude_unset=True, exclude_none=True)
    if "name" in changes:
        row.name = changes["name"].strip()
    if "icon" in changes:
        row.icon = changes["icon"]
    if "position" in changes:
        row.position = changes["position"]
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise _duplicate_name() from None
    return _list_out(row, await _count(db, row.id))


async def delete_list(db: AsyncSession, user_id: uuid.UUID, list_id: uuid.UUID) -> None:
    """Deletes the list and the saved-place rows inside it (never a row of `places`)."""
    row = await _get_list(db, user_id, list_id)
    if row.is_default:
        raise AppError(400, "cannot_delete_default_list", "Không thể xoá danh sách mặc định")
    await db.delete(row)
    await db.commit()


# ---------- saved places ----------


async def list_saved(db: AsyncSession, user_id: uuid.UUID) -> list[SavedPlaceOut]:
    rows = await db.execute(
        select(SavedPlace, SavedList.icon)
        .join(SavedList, SavedList.id == SavedPlace.list_id)
        .where(SavedPlace.user_id == user_id)
        .order_by(SavedPlace.created_at.desc())
    )
    return [_saved_out(row, icon) for row, icon in rows]


async def save_place(db: AsyncSession, user_id: uuid.UUID, data: SavedPlaceIn) -> tuple[SavedPlaceOut, bool]:
    """Save a place. Returns (saved place, created); saving again moves it and returns created=False."""
    if not await place_exists(db, data.place_id):
        raise not_found("Quán")
    target = (
        await _get_list(db, user_id, data.list_id)
        if data.list_id is not None
        else await ensure_default_list(db, user_id)
    )
    existing = await db.scalar(
        select(SavedPlace).where(SavedPlace.user_id == user_id, SavedPlace.place_id == data.place_id)
    )
    if existing is not None:
        existing.list_id = target.id
        if "note" in data.model_fields_set:
            existing.note = data.note
        await db.commit()
        return _saved_out(existing, target.icon), False

    row = SavedPlace(user_id=user_id, list_id=target.id, place_id=data.place_id, note=data.note)
    db.add(row)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()  # two requests raced: the other one saved it first
        again = await db.scalar(
            select(SavedPlace).where(SavedPlace.user_id == user_id, SavedPlace.place_id == data.place_id)
        )
        if again is None:
            raise not_found("Quán") from None
        return _saved_out(again, target.icon), False
    await db.refresh(row)
    return _saved_out(row, target.icon), True


async def update_saved(
    db: AsyncSession, user_id: uuid.UUID, saved_id: uuid.UUID, data: SavedPlaceUpdateIn
) -> SavedPlaceOut:
    row = await db.scalar(select(SavedPlace).where(SavedPlace.id == saved_id, SavedPlace.user_id == user_id))
    if row is None:
        raise not_found("Quán đã lưu")
    if data.list_id is not None:
        row.list_id = (await _get_list(db, user_id, data.list_id)).id
    if "note" in data.model_fields_set:
        row.note = data.note
    await db.commit()
    icon = await db.scalar(select(SavedList.icon).where(SavedList.id == row.list_id))
    return _saved_out(row, icon or DEFAULT_LIST_ICON)


async def delete_saved(db: AsyncSession, user_id: uuid.UUID, saved_id: uuid.UUID) -> None:
    row = await db.scalar(select(SavedPlace).where(SavedPlace.id == saved_id, SavedPlace.user_id == user_id))
    if row is None:
        raise not_found("Quán đã lưu")
    await db.delete(row)
    await db.commit()
