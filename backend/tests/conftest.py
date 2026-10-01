import asyncio
import os
import subprocess
import sys

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.db import get_db
from app.main import create_app


def _default_test_url() -> str:
    """Same server, user and port as DATABASE_URL (from .env), but the foodmaps_test database."""
    url = make_url(get_settings().database_url).set(database="foodmaps_test")
    return url.render_as_string(hide_password=False)  # str(url) would mask the password as ***


TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or _default_test_url()


@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=create_app()), base_url="http://test") as c:
        yield c


async def _ensure_test_database() -> None:
    """Create foodmaps_test if missing (Docker's init.sql creates it locally; CI does not)."""
    url = make_url(TEST_DATABASE_URL)
    admin = create_async_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    async with admin.connect() as conn:
        exists = await conn.scalar(text("SELECT 1 FROM pg_database WHERE datname = :n"), {"n": url.database})
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{url.database}"'))
    await admin.dispose()


@pytest.fixture(scope="session")
def _migrated_test_db():
    """Bring foodmaps_test to the latest schema once per test run (same migrations as dev)."""
    asyncio.run(_ensure_test_database())
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        check=True,
        env={**os.environ, "DATABASE_URL": TEST_DATABASE_URL},
    )


@pytest.fixture
async def db_client(_migrated_test_db):
    """HTTP client whose requests use foodmaps_test; tables are emptied before each test."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("TRUNCATE users CASCADE"))
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def _test_db():
        async with sessions() as session:
            yield session

    app = create_app()
    app.dependency_overrides[get_db] = _test_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    await engine.dispose()
