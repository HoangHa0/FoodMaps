"""M6 router: wiring only (the rules are covered by the service tests).

Checked here: `shares` is not read as a journey id, login is required exactly where it should be,
the address used for the link limit comes from X-Forwarded-For, and the status codes.
"""

from types import SimpleNamespace

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.modules.journey.router import client_ip
from tests.conftest import TEST_DATABASE_URL

PW = "matkhau123"
PLACE = "journey_router_place"


def _request(headers: dict[str, str], host: str | None = "10.0.0.1"):
    return SimpleNamespace(headers=headers, client=SimpleNamespace(host=host) if host else None)


# ---------- pure: no database ----------


def test_client_ip_takes_the_first_forwarded_address():
    assert client_ip(_request({"x-forwarded-for": "1.2.3.4, 10.0.0.9"})) == "1.2.3.4"


def test_client_ip_trims_spaces():
    assert client_ip(_request({"x-forwarded-for": "  1.2.3.4  "})) == "1.2.3.4"


def test_client_ip_falls_back_to_the_socket_address():
    assert client_ip(_request({})) == "10.0.0.1"
    assert client_ip(_request({"x-forwarded-for": " , "})) == "10.0.0.1"


def test_client_ip_never_fails_without_any_address():
    assert client_ip(_request({}, host=None)) == "unknown"


def test_client_ip_is_capped_in_length():
    assert len(client_ip(_request({"x-forwarded-for": "a" * 500}))) == 64


# ---------- with PostgreSQL ----------

db = pytest.mark.db


async def _as(c, username: str) -> None:
    c.cookies.clear()
    r = await c.post("/api/auth/login", json={"username": username, "password": PW})
    if r.status_code != 200:
        r = await c.post("/api/auth/register", json={"username": username, "password": PW})
        assert r.status_code == 201, r.text


@pytest.fixture
async def place(db_client):
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = :p"), {"p": PLACE})
        await conn.execute(
            text(
                "insert into places (place_id, place_code, manual_name, category, lat, lng) "
                "values (:p, 'J901', 'Quán Test', 'cafe', 21.03, 105.85)"
            ),
            {"p": PLACE},
        )
    yield
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = :p"), {"p": PLACE})
    await engine.dispose()


def _body() -> dict:
    return {"title": "Thử", "stops": [{"place_id": PLACE, "note": "ghi chú"}]}


@db
async def test_library_needs_login_but_shares_do_not(db_client, place):
    db_client.cookies.clear()
    assert (await db_client.get("/api/journeys")).status_code == 401
    assert (await db_client.post("/api/journeys", json=_body())).status_code == 401

    created = await db_client.post(
        "/api/journeys/shares", json=_body(), headers={"x-forwarded-for": "9.9.9.1"}
    )
    assert created.status_code == 201, created.text
    code = created.json()["code"]
    shared = await db_client.get(f"/api/journeys/shares/{code}")
    assert shared.status_code == 200
    assert shared.json()["stops"][0]["place"]["place_id"] == PLACE
    assert "user" not in shared.text.lower()


@db
async def test_shares_is_not_read_as_a_journey_id(db_client, place):
    await _as(db_client, "journey_router_a")
    # if the order of routes were wrong this would be a 422 (not a uuid) from /{journey_id}
    assert (await db_client.get("/api/journeys/shares/khong-co-ma-nay")).status_code == 404


@db
async def test_library_round_trip_and_status_codes(db_client, place):
    await _as(db_client, "journey_router_b")
    r = await db_client.post("/api/journeys", json=_body())
    assert r.status_code == 201, r.text
    jid = r.json()["id"]

    assert [j["id"] for j in (await db_client.get("/api/journeys")).json()] == [jid]
    assert (await db_client.get(f"/api/journeys/{jid}")).json()["stops"][0]["stop_order"] == 1

    put = await db_client.put(f"/api/journeys/{jid}", json={"title": "Mới", "stops": []})
    assert put.status_code == 200 and put.json()["stops"] == []

    assert (await db_client.delete(f"/api/journeys/{jid}")).status_code == 204
    assert (await db_client.get(f"/api/journeys/{jid}")).status_code == 404


@db
async def test_other_users_journey_is_404(db_client, place):
    await _as(db_client, "journey_router_c")
    jid = (await db_client.post("/api/journeys", json=_body())).json()["id"]
    await _as(db_client, "journey_router_d")
    assert (await db_client.get(f"/api/journeys/{jid}")).status_code == 404
    assert (await db_client.put(f"/api/journeys/{jid}", json=_body())).status_code == 404
    assert (await db_client.delete(f"/api/journeys/{jid}")).status_code == 404


@db
async def test_share_limit_is_counted_per_forwarded_address(db_client, place):
    db_client.cookies.clear()
    busy = {"x-forwarded-for": "9.9.9.50"}
    statuses = []
    for _ in range(60):  # far above the hourly limit, whatever its value
        statuses.append(
            (await db_client.post("/api/journeys/shares", json=_body(), headers=busy)).status_code
        )
        if statuses[-1] == 429:
            break
    assert statuses[-1] == 429

    # another visitor behind the same Next.js server is not affected
    other = await db_client.post(
        "/api/journeys/shares", json=_body(), headers={"x-forwarded-for": "9.9.9.51"}
    )
    assert other.status_code == 201


@db
async def test_share_needs_at_least_one_stop(db_client, place):
    r = await db_client.post(
        "/api/journeys/shares", json={"stops": []}, headers={"x-forwarded-for": "9.9.9.60"}
    )
    assert r.status_code == 422
