"""Fixtures for the tests that need the real foodmaps_test database.

Embeddings are built by hand (no sentence-transformers needed): the query is the unit vector e0 and
a place with cosine `c` to it is `c * e0 + sqrt(1 - c^2) * e1`, so every similarity is exact.
"""

import math
import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.modules.match.embedding import EMBED_DIM, EMBED_MODEL

PLACE_PREFIX = "match_test_"
ORIGIN = (21.0300, 105.8500)
METERS_PER_DEGREE_LAT = 111_320


def _test_db_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    return (
        make_url(get_settings().database_url)
        .set(database="foodmaps_test")
        .render_as_string(hide_password=False)
    )


def unit_vector(cosine_to_query: float) -> list[float]:
    vec = [0.0] * EMBED_DIM
    vec[0] = cosine_to_query
    vec[1] = math.sqrt(max(0.0, 1 - cosine_to_query**2))
    return vec


def query_vector() -> list[float]:
    vec = [0.0] * EMBED_DIM
    vec[0] = 1.0
    return vec


@pytest.fixture
async def engine(db_client):
    eng = create_async_engine(_test_db_url())
    yield eng
    await eng.dispose()


@pytest.fixture
async def seed_place(engine):
    """Factory: insert one place (+ embedding + optional crowd reviews). Cleans up its own rows first."""
    async with engine.begin() as conn:
        # cascades to place_embeddings and reviews
        await conn.execute(text("DELETE FROM places WHERE place_id LIKE :p"), {"p": PLACE_PREFIX + "%"})
    counter = {"n": 0}

    async def make(
        name: str,
        *,
        cosine: float = 0.5,
        meters_north: float = 0,
        price: int | None = None,
        crowd: list[str] | None = None,
        embedding: bool = True,
    ) -> str:
        counter["n"] += 1
        pid = PLACE_PREFIX + name
        lat = ORIGIN[0] + meters_north / METERS_PER_DEGREE_LAT
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO places (place_id, place_code, manual_name, category, lat, lng, "
                    "price_per_person) VALUES (:pid, :code, :name, 'cafe', :lat, :lng, :price)"
                ),
                {
                    "pid": pid,
                    "code": f"M9{counter['n']:02d}",
                    "name": name,
                    "lat": lat,
                    "lng": ORIGIN[1],
                    "price": price,
                },
            )
            if embedding:
                vec = "[" + ",".join(f"{x:.8f}" for x in unit_vector(cosine)) + "]"
                await conn.execute(
                    text(
                        "INSERT INTO place_embeddings (place_id, source_text, embedding, model_name) "
                        "VALUES (:pid, 'x', CAST(:vec AS vector), :model)"
                    ),
                    {"pid": pid, "vec": vec, "model": EMBED_MODEL},
                )
            for i, level in enumerate(crowd or []):
                await conn.execute(
                    text(
                        "INSERT INTO reviews (place_id, source, import_key, score_food, score_space, "
                        "score_price, score_service, crowd_level) "
                        "VALUES (:pid, 'sheet', :key, 4, 4, 4, 4, :crowd)"
                    ),
                    {"pid": pid, "key": f"{pid}#{i}", "crowd": level},
                )
        return pid

    return make
