"""Reviews models.

Inherit from app.core.db.Base so Alembic picks them up.

A single `reviews` table is used for both sources:
- source = "sheet": reviews submitted through the team's internal Google Form
  (no account yet, so `user_id` is `NULL`).
- source = "user": reviews posted by users on the website
  (`user_id` is required).

`UNIQUE(user_id, place_id)`: PostgreSQL treats `NULL` values as distinct,
so multiple "sheet" reviews with `user_id = NULL` are not restricted by
this constraint. Only reviews submitted by actual users are limited to
one review per user per restaurant.
"""

import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("places.place_id", ondelete="CASCADE"), nullable=False, index=True
    )

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE")
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False, server_default="user")

    import_key: Mapped[str | None] = mapped_column(String(80))

    score_food: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_space: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_price: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    score_service: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    categories: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    suitable_for: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    atmosphere: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    facilities: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    food_types: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    pros: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    cons: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    recommended_dishes: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    crowd_level: Mapped[str | None] = mapped_column(String(100))
    price_per_person: Mapped[int | None] = mapped_column(Integer)

    comment: Mapped[str | None] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(10), nullable=False, server_default="visible")

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "place_id", name="uq_reviews_user_place"),
        UniqueConstraint("import_key", name="uq_reviews_import_key"),
        CheckConstraint("source IN ('user', 'sheet')", name="source_valid"),
        CheckConstraint("status IN ('visible', 'flagged', 'hidden')", name="status_valid"),
        CheckConstraint("source <> 'user' OR user_id IS NOT NULL", name="user_review_has_user"),
        CheckConstraint("score_food BETWEEN 1 AND 5", name="score_food_range"),
        CheckConstraint("score_space BETWEEN 1 AND 5", name="score_space_range"),
        CheckConstraint("score_price BETWEEN 1 AND 5", name="score_price_range"),
        CheckConstraint("score_service BETWEEN 1 AND 5", name="score_service_range"),
    )
