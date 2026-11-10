"""M6 Food Journey, mounted at /api/journeys.

Library endpoints need login and only ever see the caller's own journeys. The two share endpoints
(`/shares`) are public. Fixed paths (`/shares`) are declared BEFORE `/{journey_id}`, otherwise the
word "shares" would be read as a journey id.
"""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.journey import service
from app.modules.journey.schemas import (
    JourneyIn,
    JourneyOut,
    JourneySummaryOut,
    ShareCreatedOut,
    ShareIn,
    SharedJourneyOut,
)
from app.shared.auth import CurrentUser

router = APIRouter(prefix="/journeys", tags=["M6 journey"])

Db = Annotated[AsyncSession, Depends(get_db)]

_MAX_IP_LENGTH = 64  # longer than any IPv6 text form; stops a huge header from reaching the database


def client_ip(request: Request) -> str:
    """Best guess of the real client address, used only to rate-limit link creation.

    The browser calls Next.js and Next.js calls this API, so `request.client.host` is always the
    Next.js server. The real address is the first entry of `X-Forwarded-For`, which Next.js must pass
    on. Anyone can send that header themselves, so this reduces abuse but cannot stop it.
    """
    forwarded = request.headers.get("x-forwarded-for", "")
    first = forwarded.split(",")[0].strip()
    if first:
        return first[:_MAX_IP_LENGTH]
    return request.client.host if request.client else "unknown"


# ---------- share links (public) ----------


@router.post("/shares", response_model=ShareCreatedOut, status_code=201, responses={422: {}, 429: {}})
async def create_share(data: ShareIn, request: Request, db: Db):
    """Snapshot the journey as sent (saved or not) behind a code that works for 7 days."""
    return await service.create_share(db, data, client_ip(request))


@router.get("/shares/{code}", response_model=SharedJourneyOut, responses={404: {}})
async def read_share(code: str, db: Db):
    """Read-only view. A wrong code and an expired one both answer 404."""
    return await service.read_share(db, code)


# ---------- library (login required) ----------


@router.get("", response_model=list[JourneySummaryOut], responses={401: {}})
async def my_journeys(user: CurrentUser, db: Db):
    return await service.list_journeys(db, user)


@router.post("", response_model=JourneyOut, status_code=201, responses={401: {}, 409: {}, 422: {}})
async def create_journey(data: JourneyIn, user: CurrentUser, db: Db):
    return await service.create_journey(db, user, data)


@router.get("/{journey_id}", response_model=JourneyOut, responses={401: {}, 404: {}})
async def get_journey(journey_id: uuid.UUID, user: CurrentUser, db: Db):
    return await service.get_journey(db, user, journey_id)


@router.put("/{journey_id}", response_model=JourneyOut, responses={401: {}, 404: {}, 422: {}})
async def replace_journey(journey_id: uuid.UUID, data: JourneyIn, user: CurrentUser, db: Db):
    """Overwrite the whole journey: title, date and the stops exactly as sent."""
    return await service.replace_journey(db, user, journey_id, data)


@router.delete("/{journey_id}", status_code=204, responses={401: {}, 404: {}})
async def delete_journey(journey_id: uuid.UUID, user: CurrentUser, db: Db) -> None:
    await service.delete_journey(db, user, journey_id)
