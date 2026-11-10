"""Skeleton tests: must always pass. A failure after a merge means module auto-discovery broke."""

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.core.db import Base
from app.core.errors import register_error_handlers, todo
from app.core.registry import discover_routers, import_all_models


async def test_health(client):
    r = await client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_every_module_router_is_discovered():
    prefixes = {r.prefix for r in discover_routers()}
    assert {"/auth", "/groups", "/saved-places", "/match", "/reviews", "/journeys", "/places"} <= prefixes


def test_models_registered_for_alembic():
    import_all_models()
    assert {"users", "group_rooms", "group_participants", "group_candidates", "group_votes"} <= set(
        Base.metadata.tables
    )


async def test_openapi_builds(client):
    """The frontend generates its types from /openapi.json, so a broken schema breaks the frontend."""
    r = await client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/groups/{code}/votes" in r.json()["paths"]


async def test_todo_helper_returns_501_in_standard_format():
    """`raise todo()` answers 501 in the standard error format instead of crashing with a 500.

    Uses its own tiny app, not a real module endpoint: modules get implemented over time, and
    a test that calls a real endpoint would start needing a database as soon as that happens.
    """
    app = FastAPI()
    register_error_handlers(app)

    @app.get("/unfinished")
    async def unfinished():
        raise todo()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/unfinished")
    assert r.status_code == 501
    assert r.json()["error"] == {"code": "not_implemented", "message": "Chức năng đang được phát triển"}


def test_local_database_skips_tls_and_every_database_has_a_connect_timeout():
    from app.core.db import CONNECT_TIMEOUT_S, connect_args_for

    local = connect_args_for("postgresql+asyncpg://u:p@localhost:5433/foodmaps", use_pgbouncer=False)
    assert local == {"timeout": CONNECT_TIMEOUT_S, "ssl": False}
    remote = connect_args_for(
        "postgresql+asyncpg://u:p@aws-0.pooler.supabase.com:5432/postgres", use_pgbouncer=True
    )
    assert remote == {"timeout": CONNECT_TIMEOUT_S, "statement_cache_size": 0}
