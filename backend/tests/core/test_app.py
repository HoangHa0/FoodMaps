"""Skeleton tests: must always pass. A failure after a merge means module auto-discovery broke."""

from app.core.db import Base
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


async def test_unimplemented_endpoints_return_501_not_500(client):
    """Unimplemented endpoints return 501 in the standard error format instead of crashing."""
    r = await client.post("/api/groups", json={"display_name": "Hà"})
    assert r.status_code in (201, 501)
    if r.status_code == 501:
        assert r.json()["error"]["code"] == "not_implemented"
