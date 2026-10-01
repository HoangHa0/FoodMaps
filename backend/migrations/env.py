import asyncio

from alembic import context
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.core.db import Base
from app.core.registry import import_all_models

import_all_models()  # load models.py of every module so autogenerate sees all tables
target_metadata = Base.metadata

# Tables created by extensions (PostGIS): keep autogenerate from trying to drop them.
# Tables owned by database extensions (PostGIS, topology, Tiger geocoder...) are not ours:
# keep autogenerate and `alembic check` from trying to drop them. The list is read from the
# database (pg_depend, deptype 'e' = "member of an extension"), so nothing is hard-coded.
EXTENSION_TABLES: set[str] = set()


def _load_extension_tables(connection) -> None:
    rows = connection.execute(
        text(
            "SELECT c.relname FROM pg_depend d JOIN pg_class c ON c.oid = d.objid "
            "WHERE d.classid = 'pg_class'::regclass AND d.deptype = 'e' AND c.relkind IN ('r', 'p')"
        )
    )
    EXTENSION_TABLES.update(row[0] for row in rows)


def include_object(obj, name, type_, reflected, compare_to):
    # Only skip tables that exist in the database but not in our models; a model table that
    # happens to share a name with an extension table must still be created by migrations.
    if type_ == "table" and reflected and compare_to is None:
        return name not in EXTENSION_TABLES
    return True


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
        # Query inside Alembic's own transaction: a query before it would autobegin one that
        # Alembic does not own, and the migrations would be rolled back when the connection closes.
        _load_extension_tables(connection)
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
