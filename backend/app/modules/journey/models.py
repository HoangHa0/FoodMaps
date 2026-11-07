"""Food Journey tables.

A journey is saved in the library of a logged-in user (`journeys` + `journey_stops`), or copied
into a short-lived share link (`journey_shares`). A stop stores only the `place_id`: the name and
coordinates are always read back from `places`, so there is no copy of place data here.
"""

import uuid
from datetime import date, datetime, time
from typing import Any

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.modules.journey.constants import CODE_COLUMN_LENGTH, NOTE_MAX_LENGTH, TITLE_MAX_LENGTH


class Journey(Base):
    __tablename__ = "journeys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str | None] = mapped_column(String(TITLE_MAX_LENGTH))
    planned_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class JourneyStop(Base):
    __tablename__ = "journey_stops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    journey_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("places.place_id", ondelete="CASCADE"), nullable=False, index=True
    )
    stop_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)  # 1..n, no gaps
    planned_time: Mapped[time | None] = mapped_column(Time)
    note: Mapped[str | None] = mapped_column(String(NOTE_MAX_LENGTH))

    __table_args__ = (
        # The same place may appear twice in one journey; only the position is unique.
        UniqueConstraint("journey_id", "stop_order", name="uq_journey_stops_journey_order"),
        CheckConstraint("stop_order >= 1", name="stop_order_positive"),
    )


class JourneyShare(Base):
    """A read-only snapshot behind a share link. It belongs to nobody and expires on its own.

    `snapshot` = {"title", "planned_date", "stops": [{"place_id", "planned_time", "note"}]}.
    `creator_hash` is a keyed hash of the creator's IP address, kept only to limit how many
    links one address can create per hour; it is deleted together with the row.
    """

    __tablename__ = "journey_shares"

    code: Mapped[str] = mapped_column(String(CODE_COLUMN_LENGTH), primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    creator_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # "how many links did this address create in the last hour?" is the only lookup by creator
    __table_args__ = (Index("ix_journey_shares_creator_hash_created_at", "creator_hash", "created_at"),)
