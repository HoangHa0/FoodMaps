import asyncio

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.db import Base
from app.core.registry import import_all_models

import_all_models()  # load models.py of every module so autogenerate sees all tables
target_metadata = Base.metadata

# Tables created by extensions (PostGIS): keep autogenerate from trying to drop them.
IGNORED_TABLES = {"spatial_ref_sys"}


def include_object(obj, name, type_, reflected, compare_to):
    return not (type_ == "table" and name in IGNORED_TABLES)


def _configure(connection=None, url=None):
    context.configure(
        connection=connection,
        url=url,
        target_metadata=target_metadata,
        include_object=include_object,
        compare_type=True,
    )


def run_offline():
    _configure(url=get_settings().database_url)
    with context.begin_transaction():
        context.run_migrations()


def _run_sync(connection):
    _configure(connection=connection)
    with context.begin_transaction():
        context.run_migrations()


async def run_online():
    s = get_settings()
    args = {"statement_cache_size": 0} if s.db_use_pgbouncer else {}
    engine = create_async_engine(s.database_url, connect_args=args)
    async with engine.connect() as conn:
        await conn.run_sync(_run_sync)
    await engine.dispose()


if context.is_offline_mode():
    run_offline()
else:
    asyncio.run(run_online())
