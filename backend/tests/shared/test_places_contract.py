"""Read-only contract app/shared/places.py: pure math first, then the queries (db-marked)."""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.shared.places import (
    METRES_PER_DEGREE,
    bounding_box,
    get_all_places,
    get_place,
    get_places,
    get_places_near,
    haversine_m,
    place_exists,
)
from tests.conftest import TEST_DATABASE_URL

# ---------- pure functions: no database needed ----------


def test_haversine_same_point_is_zero():
    assert haversine_m(21.0285, 105.8542, 21.0285, 105.8542) == 0


def test_haversine_one_degree_of_latitude():
    assert haversine_m(21.0, 105.0, 22.0, 105.0) == pytest.approx(METRES_PER_DEGREE, abs=1)


def test_haversine_is_symmetric():
    a = haversine_m(21.03, 105.85, 21.05, 105.80)
    b = haversine_m(21.05, 105.80, 21.03, 105.85)
    assert a == pytest.approx(b)


def test_bounding_box_contains_the_circle():
    lat, lng, radius = 21.0, 105.0, 1000
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(lat, lng, radius)
    assert lat_lo < lat < lat_hi
    assert lng_lo < lng < lng_hi
    # a point exactly `radius` metres north is on the edge of the box
    assert lat_hi == pytest.approx(lat + radius / METRES_PER_DEGREE)


def test_bounding_box_is_wider_in_longitude_away_from_the_equator():
    lat_lo, lat_hi, lng_lo, lng_hi = bounding_box(21.0, 105.0, 1000)
    assert (lng_hi - lng_lo) > (lat_hi - lat_lo)


# ---------- queries: need a real database ----------

ORIGIN = (21.0, 105.0)
NORTH_500M = 500 / METRES_PER_DEGREE
NORTH_5KM = 5000 / METRES_PER_DEGREE
IDS = ["contract_a", "contract_b", "contract_c"]


@pytest.fixture
async def session(db_client):
    engine = create_async_engine(TEST_DATABASE_URL)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = any(:ids)"), {"ids": IDS})
        rows = [
            ("contract_a", "K901", "Quán A", "cafe", ORIGIN[0], ORIGIN[1]),
            ("contract_b", "K902", "Quán B", "main_meal", ORIGIN[0] + NORTH_500M, ORIGIN[1]),
            ("contract_c", "K903", "Quán C", "cafe", ORIGIN[0] + NORTH_5KM, ORIGIN[1]),
        ]
        for pid, code, name, cat, lat, lng in rows:
            await conn.execute(
                text(
                    "insert into places (place_id, place_code, manual_name, category, lat, lng) "
                    "values (:pid, :code, :name, :cat, :lat, :lng)"
                ),
                {"pid": pid, "code": code, "name": name, "cat": cat, "lat": lat, "lng": lng},
            )
    async with maker() as s:
        yield s
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = any(:ids)"), {"ids": IDS})
    await engine.dispose()


@pytest.mark.db
async def test_get_place_returns_team_name(session):
    place = await get_place(session, "contract_a")
    assert place is not None
    assert place.name == "Quán A"  # manual_name, never a Google name
    assert place.tiktok_urls == []


@pytest.mark.db
async def test_get_place_unknown_is_none(session):
    assert await get_place(session, "no_such_place") is None


@pytest.mark.db
async def test_place_exists(session):
    assert await place_exists(session, "contract_a") is True
    assert await place_exists(session, "no_such_place") is False


@pytest.mark.db
async def test_get_places_skips_unknown_ids_and_handles_empty(session):
    found = await get_places(session, ["contract_a", "contract_b", "no_such_place"])
    assert set(found) == {"contract_a", "contract_b"}
    assert await get_places(session, []) == {}


@pytest.mark.db
async def test_get_all_places_is_ordered_by_place_code(session):
    mine = [p.place_id for p in await get_all_places(session) if p.place_id in IDS]
    assert mine == IDS  # K901, K902, K903


@pytest.mark.db
async def test_get_places_near_filters_and_sorts_by_distance(session):
    near = await get_places_near(session, *ORIGIN, radius_m=1000)
    mine = [(n.place_id, n.distance_m) for n in near if n.place_id in IDS]
    assert [pid for pid, _ in mine] == ["contract_a", "contract_b"]  # C is 5 km away
    assert mine[0][1] == 0
    assert mine[1][1] == pytest.approx(500, abs=2)


@pytest.mark.db
async def test_get_places_near_respects_limit(session):
    near = await get_places_near(session, *ORIGIN, radius_m=10_000, limit=1)
    assert len(near) == 1
    assert near[0].place_id == "contract_a"