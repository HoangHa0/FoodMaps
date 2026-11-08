"""M7 endpoints without a database: the places contract is replaced by an in-memory fake.

These run with plain `pytest` (no Docker). The db-marked tests in test_places_api.py cover the real SQL.
"""

from types import SimpleNamespace

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.db import get_db
from app.main import create_app
from app.modules.google_places import service

CAFE = SimpleNamespace(
    place_id="p_cafe",
    place_code="M901",
    name="Cà phê Test",
    category="cafe",
    address="1 Phố Test, Hà Nội",
    google_maps_url="https://maps.google.com/?cid=1",
    lat=21.03,
    lng=105.85,
    price_per_person=45000,
    tiktok_urls=["https://www.tiktok.com/@test/video/1"],
)
NOODLE = SimpleNamespace(
    place_id="p_noodle",
    place_code="M902",
    name="Phở Test",
    category="main_meal",
    address=None,
    google_maps_url=None,
    lat=21.04,
    lng=105.86,
    price_per_person=None,
    tiktok_urls=[],
)


@pytest.fixture
async def client(monkeypatch):
    async def fake_all(db):
        return [CAFE, NOODLE]

    async def fake_get(db, place_id):
        return {p.place_id: p for p in (CAFE, NOODLE)}.get(place_id)

    async def fake_db():
        yield None  # the faked contract never touches the session

    monkeypatch.setattr(service, "get_all_places", fake_all)
    monkeypatch.setattr(service, "get_place", fake_get)
    app = create_app()
    app.dependency_overrides[get_db] = fake_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


async def test_map_returns_only_pin_fields_for_guests(client):
    res = await client.get("/api/places/map")  # no auth header: guests are allowed
    assert res.status_code == 200
    body = res.json()
    assert [p["place_id"] for p in body] == ["p_cafe", "p_noodle"]
    assert set(body[0]) == {"place_id", "name", "category", "lat", "lng"}
    assert body[0]["name"] == "Cà phê Test"


async def test_summary_returns_all_fields(client):
    res = await client.get("/api/places/p_cafe/summary")
    assert res.status_code == 200
    body = res.json()
    assert body["address"] == "1 Phố Test, Hà Nội"
    assert body["price_per_person"] == 45000
    assert body["tiktok_urls"] == ["https://www.tiktok.com/@test/video/1"]


async def test_summary_optional_fields_are_null(client):
    body = (await client.get("/api/places/p_noodle/summary")).json()
    assert body["address"] is None
    assert body["google_maps_url"] is None
    assert body["price_per_person"] is None
    assert body["tiktok_urls"] == []


async def test_summary_unknown_place_is_404(client):
    res = await client.get("/api/places/does_not_exist/summary")
    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"