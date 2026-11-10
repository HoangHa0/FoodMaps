"""M6 Food Journey service: the library of a logged-in user and read-only share links.

Saving is always "overwrite the whole journey": the client sends the title, the date and the full
list of stops, and the stops are deleted and inserted again in the same transaction. That is why
there is no operation on a single stop, and why drag-and-drop needs nothing from the server.

Every library function filters by the user, so another user's journey answers 404 as if it did
not exist. Share links belong to nobody; their rules (7 days, one hour window) are in `rules.py`.
"""

import uuid
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import delete, func, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.modules.journey import rules
from app.modules.journey.constants import MAX_JOURNEYS_PER_USER
from app.modules.journey.models import Journey, JourneyShare, JourneyStop
from app.modules.journey.schemas import (
    JourneyIn,
    JourneyOut,
    JourneySummaryOut,
    PlaceOut,
    ShareCreatedOut,
    SharedJourneyOut,
    SharedStopOut,
    ShareIn,
    StopIn,
    StopOut,
)
from app.shared.auth import AuthUser
from app.shared.places import PlaceRef, get_places


def _now() -> datetime:
    return datetime.now(UTC)


def _hash_secret() -> str:
    """Server-side secret that keys the hash of client addresses (the JWT secret is already one)."""
    return get_settings().jwt_secret


async def _require_places(db: AsyncSession, stops: Sequence[StopIn]) -> dict[str, PlaceRef]:
    found = await get_places(db, [s.place_id for s in stops])
    if any(s.place_id not in found for s in stops):
        raise AppError(422, "unknown_place", "Có quán không còn trong hệ thống")
    return found


def _new_stops(journey_id: uuid.UUID, stops: Sequence[StopIn]) -> list[JourneyStop]:
    return [
        JourneyStop(
            journey_id=journey_id,
            place_id=s.place_id,
            stop_order=position,
            planned_time=s.planned_time,
            note=s.note,
        )
        for position, s in enumerate(stops, start=1)
    ]


async def _own_journey(db: AsyncSession, user: AuthUser, journey_id: uuid.UUID) -> Journey:
    """The journey, locked for update. Someone else's journey is reported as missing."""
    journey = await db.scalar(
        select(Journey).where(Journey.id == journey_id, Journey.user_id == user.id).with_for_update()
    )
    if journey is None:
        raise not_found("Chuyến đi")
    return journey


# --- library ---------------------------------------------------------------------------------
async def list_journeys(db: AsyncSession, user: AuthUser) -> list[JourneySummaryOut]:
    rows = await db.execute(
        select(
            Journey.id,
            Journey.title,
            Journey.planned_date,
            Journey.updated_at,
            func.count(JourneyStop.id).label("stop_count"),
        )
        .outerjoin(JourneyStop, JourneyStop.journey_id == Journey.id)
        .where(Journey.user_id == user.id)
        .group_by(Journey.id)
        .order_by(Journey.updated_at.desc(), Journey.id)
    )
    return [JourneySummaryOut.model_validate(dict(r._mapping)) for r in rows]


async def get_journey(db: AsyncSession, user: AuthUser, journey_id: uuid.UUID) -> JourneyOut:
    row = (
        await db.execute(
            select(
                Journey.id,
                Journey.title,
                Journey.planned_date,
                Journey.created_at,
                Journey.updated_at,
            ).where(Journey.id == journey_id, Journey.user_id == user.id)
        )
    ).one_or_none()
    if row is None:
        raise not_found("Chuyến đi")

    stops = (
        await db.scalars(
            select(JourneyStop).where(JourneyStop.journey_id == row.id).order_by(JourneyStop.stop_order)
        )
    ).all()
    places = await get_places(db, [s.place_id for s in stops])
    return JourneyOut(
        id=row.id,
        title=row.title,
        planned_date=row.planned_date,
        created_at=row.created_at,
        updated_at=row.updated_at,
        stops=[
            StopOut(
                id=s.id,
                stop_order=s.stop_order,
                planned_time=s.planned_time,
                note=s.note,
                place=PlaceOut.model_validate(places[s.place_id]),
            )
            for s in stops
            if s.place_id in places
        ],
    )


async def create_journey(db: AsyncSession, user: AuthUser, data: JourneyIn) -> JourneyOut:
    # One creation at a time per user, so two simultaneous requests cannot both pass the limit.
    # The lock is released by the commit (or rollback) below.
    await db.execute(text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"journey:{user.id}"})
    saved = await db.scalar(select(func.count()).select_from(Journey).where(Journey.user_id == user.id))
    if rules.journey_limit_reached(saved or 0):
        raise AppError(
            409,
            "journey_limit",
            f"Bạn đã lưu tối đa {MAX_JOURNEYS_PER_USER} chuyến đi, hãy xoá bớt chuyến cũ",
        )
    await _require_places(db, data.stops)

    journey = Journey(user_id=user.id, title=data.title, planned_date=data.planned_date)
    db.add(journey)
    await db.flush()  # gives the journey its id
    db.add_all(_new_stops(journey.id, data.stops))
    await db.commit()
    return await get_journey(db, user, journey.id)


async def replace_journey(
    db: AsyncSession, user: AuthUser, journey_id: uuid.UUID, data: JourneyIn
) -> JourneyOut:
    """Overwrite the journey: new title and date, and the stops exactly as sent."""
    journey = await _own_journey(db, user, journey_id)
    await _require_places(db, data.stops)  # checked first, so a bad request changes nothing

    await db.execute(delete(JourneyStop).where(JourneyStop.journey_id == journey.id))
    db.add_all(_new_stops(journey.id, data.stops))
    # updated_at is set by hand: if only the stops changed, the journey row itself would not be
    # updated and the column would not move.
    await db.execute(
        update(Journey)
        .where(Journey.id == journey.id)
        .values(title=data.title, planned_date=data.planned_date, updated_at=func.now())
    )
    await db.commit()
    return await get_journey(db, user, journey.id)


async def delete_journey(db: AsyncSession, user: AuthUser, journey_id: uuid.UUID) -> None:
    deleted = await db.scalar(
        delete(Journey).where(Journey.id == journey_id, Journey.user_id == user.id).returning(Journey.id)
    )
    if deleted is None:
        raise not_found("Chuyến đi")
    await db.commit()  # the stops go with it (ON DELETE CASCADE)


# --- share links -----------------------------------------------------------------------------
async def create_share(
    db: AsyncSession, data: ShareIn, client_ip: str, *, now: datetime | None = None
) -> ShareCreatedOut:
    """Snapshot the journey as sent (saved or not) behind a new code. Nobody needs to be logged in."""
    now = now or _now()
    # Housekeeping: there is no background job, so every new link removes the expired ones.
    await db.execute(delete(JourneyShare).where(JourneyShare.expires_at <= now))

    creator = rules.hash_client_ip(client_ip, _hash_secret())
    recent = await db.scalar(
        select(func.count())
        .select_from(JourneyShare)
        .where(
            JourneyShare.creator_hash == creator,
            JourneyShare.created_at > rules.share_window_start(now),
        )
    )
    if rules.share_limit_reached(recent or 0):
        raise AppError(429, "too_many_shares", "Bạn tạo link quá nhiều, hãy thử lại sau ít phút")
    await _require_places(db, data.stops)

    stops = [rules.StopData(s.place_id, s.planned_time, s.note) for s in data.stops]
    share = JourneyShare(
        code=rules.new_share_code(),  # 64^11 possible codes: a repeat is not a practical concern
        snapshot=rules.make_snapshot(data.title, data.planned_date, stops),
        creator_hash=creator,
        created_at=now,
        expires_at=rules.share_expires_at(now),
    )
    db.add(share)
    await db.commit()
    return ShareCreatedOut(code=share.code, expires_at=share.expires_at)


async def read_share(db: AsyncSession, code: str, *, now: datetime | None = None) -> SharedJourneyOut:
    """Anyone with the code may read it. A wrong code and an expired one answer the same 404."""
    now = now or _now()
    share = await db.get(JourneyShare, code)
    if share is None or rules.is_expired(share.expires_at, now):
        raise AppError(404, "not_found", "Liên kết không tồn tại hoặc đã hết hạn")

    snapshot = rules.read_snapshot(share.snapshot)
    places = await get_places(db, [s.place_id for s in snapshot.stops])
    kept = [(s, places[s.place_id]) for s in snapshot.stops if s.place_id in places]
    return SharedJourneyOut(
        title=snapshot.title,
        planned_date=snapshot.planned_date,
        expires_at=share.expires_at,
        stops=[
            SharedStopOut(
                stop_order=position,
                planned_time=s.planned_time,
                note=s.note,
                place=PlaceOut.model_validate(place),
            )
            for position, (s, place) in enumerate(kept, start=1)
        ],
        missing_places=len(snapshot.stops) - len(kept),
    )