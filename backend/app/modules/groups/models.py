"""Group Session tables. All of this is data we generate ourselves, so it is kept permanently.

Places are referenced by Google `place_id` only (allowed to store); never store Google names,
photos or ratings here.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base

ROOM_STATUSES = ("lobby", "voting", "decided", "expired")


def _uuid_pk():
    return mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))


class GroupRoom(Base):
    __tablename__ = "group_rooms"

    id: Mapped[uuid.UUID] = _uuid_pk()
    code: Mapped[str] = mapped_column(String(6), unique=True, nullable=False)
    # String + CHECK instead of a Postgres ENUM: adding a status later needs no ALTER TYPE migration.
    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="lobby")
    criteria: Mapped[dict | None] = mapped_column(JSONB)  # MatchCriteria.model_dump(), set on start
    # Incremented on every room change (join, vote, decision) -> cheap polling via since_version.
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    member_count_at_start: Mapped[int | None] = mapped_column(SmallInteger)
    winner_place_id: Mapped[str | None] = mapped_column(String(300))
    decided_by: Mapped[str | None] = mapped_column(String(12))  # majority | all_voted | host | expired
    created_by_user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (CheckConstraint(f"status IN {ROOM_STATUSES}", name="status_valid"),)


class GroupParticipant(Base):
    __tablename__ = "group_participants"

    id: Mapped[uuid.UUID] = _uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group_rooms.id", ondelete="CASCADE"), nullable=False
    )
    display_name: Mapped[str] = mapped_column(String(30), nullable=False)
    # Only the SHA-256 of the token is stored; the raw token is returned to the client once, on join.
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    is_host: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("uq_group_participants_room_name", "room_id", func.lower(display_name), unique=True),
    )


class GroupCandidate(Base):
    __tablename__ = "group_candidates"

    id: Mapped[uuid.UUID] = _uuid_pk()
    room_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group_rooms.id", ondelete="CASCADE"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(String(300), nullable=False)
    rank: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 0 = best match; used as tie-breaker
    match_score: Mapped[float] = mapped_column(Float, nullable=False)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="[]")

    __table_args__ = (UniqueConstraint("room_id", "place_id"),)


class GroupVote(Base):
    __tablename__ = "group_votes"

    participant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group_participants.id", ondelete="CASCADE"), primary_key=True
    )
    candidate_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("group_candidates.id", ondelete="CASCADE"), primary_key=True
    )
    room_id: Mapped[uuid.UUID] = mapped_column(  # denormalised on purpose: count votes per room in one query
        ForeignKey("group_rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )
    liked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    voted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
