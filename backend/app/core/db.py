from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings

# Deterministic constraint names, so Alembic autogenerate produces the same names on every machine.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Single declarative base for every model in every module.

    One metadata object means one migration history for the whole project.
    """

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


def _make_engine():
    s = get_settings()
    connect_args = {"statement_cache_size": 0} if s.db_use_pgbouncer else {}
    return create_async_engine(s.database_url, pool_pre_ping=True, connect_args=connect_args)


engine = _make_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request. Services commit explicitly."""
    async with SessionLocal() as session:
        yield session
