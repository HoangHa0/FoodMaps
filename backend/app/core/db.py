from collections.abc import AsyncIterator

from sqlalchemy import MetaData, make_url
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


# Seconds to wait for a NEW database connection. asyncpg's default (60 s) outlasts the Next.js proxy, so
# a stuck connect looked like a page that never loads; failing fast lets the client retry instead.
CONNECT_TIMEOUT_S = 10
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


def connect_args_for(database_url: str, use_pgbouncer: bool) -> dict:
    """asyncpg options. The local Docker database has no TLS: skipping the TLS probe removes a step
    that Docker Desktop on Windows sometimes resets under load ("WinError 10054"). Remote databases
    (Supabase) keep asyncpg's default TLS negotiation."""
    args: dict = {"timeout": CONNECT_TIMEOUT_S}
    if use_pgbouncer:
        args["statement_cache_size"] = 0
    if make_url(database_url).host in LOCAL_HOSTS:
        args["ssl"] = False
    return args


def _make_engine():
    s = get_settings()
    return create_async_engine(
        s.database_url,
        pool_pre_ping=True,
        connect_args=connect_args_for(s.database_url, s.db_use_pgbouncer),
    )


engine = _make_engine()
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: one session per request. Services commit explicitly."""
    async with SessionLocal() as session:
        yield session
