"""Tests of the places read contract against the real test database (needs PostgreSQL).

Places are inserted here, so the team's private CSV is never read. Run with `make test` once the
database is up; CI runs them on every pull request.
"""

import math

import pytest

from app.modules.match.models import Place
from app.shared import places

# Centre of the test "map": Q001 of the team's catalogue
LAT, LNG = 20.9893215, 105.8406215


def offset(north_m: float = 0, east_m: float = 0) -> tuple[float, float]:
    """Coordinates `north_m` / `east_m` metres away from the centre."""
    lat = LAT + north_m / places.METRES_PER_DEGREE
    lng = LNG + east_m / (places.METRES_PER_DEGREE * math.cos(math.radians(LAT)))
    return lat, lng


def make_place(code: str, name: str, north_m: float = 0, east_m: float = 0, **fields) -> Place:
    lat, lng = offset(north_m, east_m)
    values = {
        "place_id": f"gid_{code}",
        "place_code": code,
        "manual_name": name,
        "category": "Cà phê & Trà",
        "address": None,
        "google_maps_url": None,
        "lat": lat,
        "lng": lng,
        "price_per_person": None,
        "tiktok_urls": [],
    }
    return Place(**{**values, **fields})


async def store(db, *rows: Place) -> None:
    db.add_all(rows)
    await db.commit()
    db.expunge_all()  # later reads must come from the database, not from the session's memory


async def test_get_place_returns_every_field(db_session):
    await store(
        db_session,
        make_place(
            "Q001",
            "Tiny Cafe - Revolution",
            address="348 Giải Phóng",
            google_maps_url="https://maps.app.goo.gl/x",
            price_per_person=45_000,
            tiktok_urls=["https://www.tiktok.com/a", "https://www.tiktok.com/b"],
        ),
    )
    got = await places.get_place(db_session, "gid_Q001")
    assert got is not None
    assert (got.place_code, got.name, got.category) == ("Q001", "Tiny Cafe - Revolution", "Cà phê & Trà")
    assert (got.address, got.google_maps_url) == ("348 Giải Phóng", "https://maps.app.goo.gl/x")
    assert (got.lat, got.lng, got.price_per_person) == (LAT, LNG, 45_000)
    assert got.tiktok_urls == ["https://www.tiktok.com/a", "https://www.tiktok.com/b"]


async def test_optional_fields_come_back_empty(db_session):
    await store(db_session, make_place("Q001", "A"))
    got = await places.get_place(db_session, "gid_Q001")
    assert got is not None
    assert (got.address, got.google_maps_url, got.price_per_person) == (None, None, None)
    assert got.tiktok_urls == []


async def test_unknown_place_is_none(db_session):
    assert await places.get_place(db_session, "gid_nope") is None


async def test_place_exists(db_session):
    await store(db_session, make_place("Q001", "A"))
    assert await places.place_exists(db_session, "gid_Q001") is True
    assert await places.place_exists(db_session, "gid_nope") is False


async def test_get_places_skips_unknown_and_repeated_ids(db_session):
    await store(db_session, make_place("Q001", "A"), make_place("Q002", "B"))
    got = await places.get_places(db_session, ["gid_Q001", "gid_Q001", "gid_nope", "gid_Q002"])
    assert set(got) == {"gid_Q001", "gid_Q002"}
    assert got["gid_Q002"].name == "B"


async def test_get_places_with_no_ids_is_empty(db_session):
    assert await places.get_places(db_session, []) == {}


async def test_get_all_places_is_sorted_by_code(db_session):
    await store(db_session, make_place("Q003", "C"), make_place("Q001", "A"), make_place("Q002", "B"))
    assert [p.place_code for p in await places.get_all_places(db_session)] == ["Q001", "Q002", "Q003"]


async def test_near_lists_nearest_first_with_distance(db_session):
    await store(
        db_session,
        make_place("Q001", "centre"),
        make_place("Q002", "east 100 m", east_m=100),
        make_place("Q003", "north 400 m", north_m=400),
        make_place("Q004", "far away", north_m=5_000),
    )
    found = await places.get_places_near(db_session, LAT, LNG, 500)
    assert [p.place_code for p in found] == ["Q001", "Q002", "Q003"]
    assert [p.distance_m for p in found] == [0, pytest.approx(100, abs=1), pytest.approx(400, abs=1)]


async def test_near_respects_the_radius(db_session):
    await store(db_session, make_place("Q001", "centre"), make_place("Q002", "east 300 m", east_m=300))
    assert [p.place_code for p in await places.get_places_near(db_session, LAT, LNG, 200)] == ["Q001"]
    assert len(await places.get_places_near(db_session, LAT, LNG, 400)) == 2


async def test_near_drops_the_corner_of_the_box(db_session):
    """400 m north and 400 m east lies inside the 500 m box but about 566 m away."""
    await store(db_session, make_place("Q001", "corner", north_m=400, east_m=400))
    assert await places.get_places_near(db_session, LAT, LNG, 500) == []


async def test_near_limit_keeps_the_nearest(db_session):
    await store(
        db_session,
        make_place("Q001", "a", east_m=300),
        make_place("Q002", "b", east_m=100),
        make_place("Q003", "c", east_m=200),
    )
    found = await places.get_places_near(db_session, LAT, LNG, 500, limit=2)
    assert [p.place_code for p in found] == ["Q002", "Q003"]


async def test_near_breaks_ties_by_place_id(db_session):
    await store(db_session, make_place("Q002", "b", east_m=100), make_place("Q001", "a", east_m=100))
    found = await places.get_places_near(db_session, LAT, LNG, 500)
    assert [p.place_id for p in found] == ["gid_Q001", "gid_Q002"]
