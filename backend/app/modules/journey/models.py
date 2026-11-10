"""Journey models (M6).

A journey is a user's planned outing:
- journeys: a user's planned outing (title and date are optional).
- journey_stops: ordered places belonging to a journey.
- journey_shares: a read-only snapshot behind a short-lived share link.

A stop stores only the place_id. Place names and coordinates are read from
the places table, so place data is not duplicated here.

Deleting a user deletes their journeys; deleting a journey or a place
deletes the matching stops.
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
from app.modules.journey.constants import (
    CODE_COLUMN_LENGTH,
    NOTE_MAX_LENGTH,
    TITLE_MAX_LENGTH,
)


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
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class JourneyStop(Base):
    __tablename__ = "journey_stops"
    __table_args__ = (
        CheckConstraint("stop_order >= 1", name="stop_order_positive"),
        UniqueConstraint(
            "journey_id",
            "stop_order",
            name="uq_journey_stops_journey_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    journey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("journeys.id", ondelete="CASCADE"),
        nullable=False,
    )
    place_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("places.place_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stop_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    planned_time: Mapped[time | None] = mapped_column(Time)
    note: Mapped[str | None] = mapped_column(String(NOTE_MAX_LENGTH))


class JourneyShare(Base):
    """A read-only snapshot behind a share link.

    The share belongs to nobody and expires independently of the journey.

    snapshot = {
        "title", "planned_date",
        "stops": [{"place_id", "planned_time", "note"}]
    }

    creator_hash is a keyed hash used to limit link creation per address.
    """

    __tablename__ = "journey_shares"
    __table_args__ = (
        Index(
            "ix_journey_shares_creator_hash_created_at",
            "creator_hash",
            "created_at",
        ),
    )

    code: Mapped[str] = mapped_column(String(CODE_COLUMN_LENGTH), primary_key=True)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    creator_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
