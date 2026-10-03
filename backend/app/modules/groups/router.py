"""M5 endpoints, mounted at /api/groups.

Room members authenticate with the `X-Participant-Token` header; no account is needed.
Every write returns the new room state, so the client updates without waiting for a poll.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.modules.groups import service
from app.modules.groups.schemas import (
    CreateRoomIn,
    JoinedOut,
    JoinRoomIn,
    RoomStateOut,
    StartIn,
    VoteIn,
)
from app.shared.auth import OptionalUser
from app.shared.contracts import CandidateProvider, get_candidate_provider

router = APIRouter(prefix="/groups", tags=["M5 group session"])

Db = Annotated[AsyncSession, Depends(get_db)]
ParticipantToken = Annotated[str, Header(alias="X-Participant-Token")]
Provider = Annotated[CandidateProvider, Depends(get_candidate_provider)]


@router.post("", response_model=JoinedOut, status_code=201)
async def create_room(data: CreateRoomIn, user: OptionalUser, db: Db):
    """Create a room right away (criteria come later). The creator becomes the host."""
    room, host, token = await service.create_room(db, data, user)
    return JoinedOut(code=room.code, participant_id=host.id, participant_token=token, is_host=True)


@router.post("/{code}/join", response_model=JoinedOut, status_code=201, responses={404: {}, 409: {}, 410: {}})
async def join_room(code: str, data: JoinRoomIn, user: OptionalUser, db: Db):
    """Join the lobby. 409 if the room already started, is full or the name is taken; 410 if expired."""
    room, me, token = await service.join_room(db, code, data, user)
    return JoinedOut(code=room.code, participant_id=me.id, participant_token=token, is_host=False)


@router.get("/{code}", response_model=RoomStateOut, responses={401: {}, 404: {}})
async def get_state(code: str, token: ParticipantToken, db: Db, since_version: int | None = None):
    """Polling endpoint. If since_version == room.version, returns changed=False with an empty body."""
    room, me = await service.authenticate_participant(db, code, token)
    return await service.get_state(db, room, me, since_version)


@router.post("/{code}/start", response_model=RoomStateOut, responses={403: {}, 409: {}})
async def start(code: str, data: StartIn, token: ParticipantToken, provider: Provider, db: Db):
    """Host only: fetch candidates from the CandidateProvider, store them, move to voting."""
    room, me = await service.authenticate_participant(db, code, token, for_update=True)
    await service.start_room(db, room, me, data.criteria, provider)
    return await service.get_state(db, room, me)


@router.post("/{code}/votes", response_model=RoomStateOut, responses={404: {}, 409: {}})
async def vote(code: str, data: VoteIn, token: ParticipantToken, db: Db):
    """Upsert a vote, then apply rules.decide; the room may be decided in the same transaction."""
    room, me = await service.authenticate_participant(db, code, token, for_update=True)
    await service.cast_vote(db, room, me, data)
    return await service.get_state(db, room, me)


@router.post("/{code}/finalize", response_model=RoomStateOut, responses={403: {}, 409: {}})
async def finalize(code: str, token: ParticipantToken, db: Db):
    """Host ends voting early: the most-liked place wins (decided_by="host")."""
    room, me = await service.authenticate_participant(db, code, token, for_update=True)
    await service.finalize(db, room, me)
    return await service.get_state(db, room, me)
