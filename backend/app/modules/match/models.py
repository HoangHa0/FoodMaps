"""match models. Inherit from app.core.db.Base so Alembic picks them up."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.modules.match.embedding import EMBED_DIM


class Place(Base):
    __tablename__ = "places"

    place_id: Mapped[str] = mapped_column(String(255), primary_key=True)  # Google place_id
    place_code: Mapped[str] = mapped_column(String(10), nullable=False, unique=True)  # Q001...
    manual_name: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[str | None] = mapped_column(Text)
    google_maps_url: Mapped[str | None] = mapped_column(Text)
    lat: Mapped[float] = mapped_column(Float, nullable=False)
    lng: Mapped[float] = mapped_column(Float, nullable=False)
    price_per_person: Mapped[int | None] = mapped_column(Integer)  # VND
    tiktok_urls: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlaceEmbedding(Base):
    """One vector per place, computed OFFLINE by scripts/compute_embeddings.py (DECISIONS D7).

    `source_text` is the merged text that was embedded (our own reviews + TikTok captions).
    `model_name` records which model produced the vector: a query must be encoded with the same one.
    """

    __tablename__ = "place_embeddings"

    place_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("places.place_id", ondelete="CASCADE"), primary_key=True
    )
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlaceInsight(Base):
    """What the LLM job (`scripts/generate_insights.py`) wrote about one place. One row per place.

    Everything here is generated OFFLINE, so no LLM call happens while a user is using the app.
    Two separate calls feed this row, with different inputs:

    - MAIN call, every visible review (website AND internal sheet): pros, cons, faq, highlights.
      Tracked by `review_count` + `input_hash`.
    - SUMMARY call, visible WEBSITE reviews only (`source = 'user'`): `summary`. The internal sheet
      data is not public, so it is never given to the summary call. Tracked by `web_review_count`
      + `summary_hash`; `summary` is NULL while the place has no website review.

    `top_dishes` is counted by plain code (same rule as Review Analysis), not by the LLM.
    A place without any review has no row at all.
    """

    __tablename__ = "place_insights"

    place_id: Mapped[str] = mapped_column(
        String(255), ForeignKey("places.place_id", ondelete="CASCADE"), primary_key=True
    )
    summary: Mapped[str | None] = mapped_column(Text)  # AI Summary, from website reviews only
    pros: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    cons: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    # {preset_key: answer or null}; the questions themselves live in code (insights.PRESET_QUESTIONS).
    # null = the reviews do not say, so nothing is shown instead of a guess.
    faq: Mapped[dict[str, str | None]] = mapped_column(JSONB, nullable=False, server_default="{}")
    # [{"name": "Phở bò", "mentions": 4}, ...], most mentioned first
    top_dishes: Mapped[list[dict]] = mapped_column(JSONB, nullable=False, server_default="[]")

    # --- bookkeeping, so the script can resume and skip work that is already done
    review_count: Mapped[int] = mapped_column(Integer, nullable=False)  # reviews given to the main call
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)  # fingerprint of those reviews
    web_review_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    summary_hash: Mapped[str | None] = mapped_column(String(64))  # fingerprint of the website reviews
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)  # model of the highlights
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class PlaceHighlight(Base):
    """One short factual bullet about a place ("Có nhiều ổ điện") with its embedding.

    The search text is compared with these vectors at request time (no LLM) to explain WHY a place
    matches. `support` = how many reviews mention it, used to rank bullets. Rows are replaced
    together with their `place_insights` row; deleting the insight deletes them.
    """

    __tablename__ = "place_highlights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    place_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey("place_insights.place_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(String(200), nullable=False)
    support: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM), nullable=False)

    __table_args__ = (UniqueConstraint("place_id", "content", name="uq_place_highlights_place_content"),)
