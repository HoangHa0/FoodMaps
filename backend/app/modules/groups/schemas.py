"""M5 API contract. The frontend generates its TypeScript types from these (via OpenAPI)."""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints

from app.shared.contracts import MatchCriteria

RoomStatus = Literal["lobby", "voting", "decided", "expired"]
# Whitespace is stripped BEFORE the length check, so "   " is rejected (422) instead of becoming a blank name
DisplayName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30), Field(examples=["Hà"])
]


class CreateRoomIn(BaseModel):
    display_name: DisplayName  # the host's display name


class JoinRoomIn(BaseModel):
    display_name: DisplayName


class JoinedOut(BaseModel):
    """Returned exactly once. The client stores the token (per room code) and sends it back in
    the `X-Participant-Token` header on every following request."""

    code: str
    participant_id: uuid.UUID
    participant_token: str
    is_host: bool


class StartIn(BaseModel):
    criteria: MatchCriteria


class VoteIn(BaseModel):
    candidate_id: uuid.UUID
    liked: bool


class ParticipantOut(BaseModel):
    id: uuid.UUID
    display_name: str
    is_host: bool
    votes_cast: int  # cards this person has voted on -> host sees who is still voting


class CandidateOut(BaseModel):
    id: uuid.UUID
    place_id: str  # name/photo fetched live via M7 (with attribution)
    rank: int
    match_score: float
    tags: list[str]
    likes: int
    my_vote: bool | None  # None = the caller has not voted on this card yet


class RoomStateOut(BaseModel):
    code: str
    status: RoomStatus
    version: int
    changed: bool = True  # False -> nothing changed; list fields may be empty
    me: uuid.UUID
    participants: list[ParticipantOut] = []
    candidates: list[CandidateOut] = []
    majority_threshold: int | None = None  # likes needed to decide automatically
    winner_place_id: str | None = None
    decided_by: str | None = None  # majority | all_voted | host | expired
    # No directions URL here: the frontend builds the Google Maps deep link from place_id plus the
    # live place name (Google place names must not be stored).
    expires_at: datetime
    server_time: datetime  # lets clients show a countdown that ignores their own clock skew
    poll_interval_ms: int
