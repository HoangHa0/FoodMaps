"""M5 endpoints, mounted at /api/groups.

Room members authenticate with the `X-Participant-Token` header; no account is needed.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Header

from app.core.errors import todo
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

ParticipantToken = Annotated[str, Header(alias="X-Participant-Token")]
Provider = Annotated[CandidateProvider, Depends(get_candidate_provider)]


@router.post("", response_model=JoinedOut, status_code=201)
async def create_room(data: CreateRoomIn, user: OptionalUser):
    """Create a room right away (criteria come later). The creator becomes the host."""
    raise todo()


@router.post("/{code}/join", response_model=JoinedOut, responses={404: {}, 409: {}, 410: {}})
async def join_room(code: str, data: JoinRoomIn, user: OptionalUser):
    """Join the lobby. 409 if the room already started, is full or the name is taken; 410 if expired."""
    raise todo()


@router.get("/{code}", response_model=RoomStateOut)
async def get_state(code: str, token: ParticipantToken, since_version: int | None = None):
    """Polling endpoint. If since_version == room.version, returns changed=False with an empty body."""
    raise todo()


@router.post("/{code}/start", response_model=RoomStateOut, responses={403: {}, 409: {}})
async def start(code: str, data: StartIn, token: ParticipantToken, provider: Provider):
    """Host only: fetch candidates from the CandidateProvider, store them, move to voting."""
    raise todo()


@router.post("/{code}/votes", response_model=RoomStateOut, responses={409: {}})
async def vote(code: str, data: VoteIn, token: ParticipantToken):
    """Upsert a vote, then apply rules.decide; the room may be decided in the same transaction."""
    raise todo()


@router.post("/{code}/finalize", response_model=RoomStateOut, responses={403: {}})
async def finalize(code: str, token: ParticipantToken):
    """Host ends voting early: the most-liked place wins (decided_by="host")."""
    raise todo()
