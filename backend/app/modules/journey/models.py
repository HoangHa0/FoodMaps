"""journey models (M6). Inherit from app.core.db.Base so Alembic picks them up.

Three tables, matching the migration `m6_add_journeys` (cb745200e3db):
- `journeys`: a user's planned outing (title and date are optional).
- `journey_stops`: the ordered places of one journey (`stop_order` starts at 1, unique per journey).
- `journey_shares`: a read-only snapshot of a journey behind a short share code, with an expiry date.
  It keeps no foreign key: a share must keep working (until it expires) after the journey is edited.

Deleting a user deletes their journeys; deleting a journey or a place deletes the matching stops.
"""

import uuid
from datetime import date, datetime, time

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


class Journey(Base):
    __tablename__ = "journeys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(100))
    planned_date: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class JourneyStop(Base):
    __tablename__ = "journey_stops"
    __table_args__ = (
        CheckConstraint("stop_order >= 1", name="stop_order_positive"),
        UniqueConstraint("journey_id", "stop_order", name="uq_journey_stops_journey_order"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    journey_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("journeys.id", ondelete="CASCADE"), nullable=False
    )
    place_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("places.place_id", ondelete="CASCADE"), nullable=False, index=True
    )
    stop_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    planned_time: Mapped[time | None] = mapped_column(Time)
    note: Mapped[str | None] = mapped_column(String(300))


class JourneyShare(Base):
    __tablename__ = "journey_shares"
    __table_args__ = (Index("ix_journey_shares_creator_hash_created_at", "creator_hash", "created_at"),)

    code: Mapped[str] = mapped_column(String(32), primary_key=True)
    snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False)
    creator_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
