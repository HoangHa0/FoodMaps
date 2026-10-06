"""match models. Inherit from app.core.db.Base so Alembic picks them up."""

from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY
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
