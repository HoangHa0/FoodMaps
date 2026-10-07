"""Fixtures for the reviews API tests (they need the real foodmaps_test database).

`db_client` (tests/conftest.py) empties `users` before every test, which also removes the reviews
and reports of those users. Places are not removed, and neither are 'sheet' reviews (no user), so
the `places` fixture clears the reviews of its own test places itself.
"""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

PLACE_IDS = [f"review_test_place_{i}" for i in range(1, 5)]


def _test_db_url() -> str:
    if url := os.environ.get("TEST_DATABASE_URL"):
        return url
    return (
        make_url(get_settings().database_url)
        .set(database="foodmaps_test")
        .render_as_string(hide_password=False)
    )


@pytest.fixture
async def engine(db_client):
    """A direct connection to the test database (to insert sheet reviews or change a status)."""
    eng = create_async_engine(_test_db_url())
    yield eng
    await eng.dispose()


@pytest.fixture
async def places(engine):
    """Four test places; returns their place_ids."""
    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM reviews WHERE place_id = ANY(:ids)"), {"ids": PLACE_IDS})
        for i, pid in enumerate(PLACE_IDS, start=1):
            await conn.execute(
                text(
                    "INSERT INTO places (place_id, place_code, manual_name, category, lat, lng) "
                    "VALUES (:pid, :code, :name, 'cafe', 21.03, 105.85) ON CONFLICT DO NOTHING"
                ),
                {"pid": pid, "code": f"T90{i}", "name": f"Quán test {i}"},
            )
    return PLACE_IDS
