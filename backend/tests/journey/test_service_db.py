"""Tests of the Food Journey service against the real test database (needs PostgreSQL)."""

import asyncio
import uuid
from datetime import UTC, datetime, time, timedelta
from types import SimpleNamespace

import pytest
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.core.errors import AppError
from app.modules.journey import constants, rules, service
from app.modules.journey.models import Journey, JourneyShare, JourneyStop
from app.modules.journey.schemas import JourneyIn, ShareIn
from app.modules.match.models import Place

NOW = datetime(2026, 11, 8, 9, 0, tzinfo=UTC)


# --- helpers ---------------------------------------------------------------------------------
@pytest.fixture
async def db(db_session):
    await db_session.execute(text("TRUNCATE users, journey_shares CASCADE"))
    await db_session.commit()
    return db_session


async def make_user(db, name="lan"):
    user_id = uuid.uuid4()
    await db.execute(
        text("INSERT INTO users (id, username, password_hash) VALUES (:id, :name, 'x')"),
        {"id": user_id, "name": name},
    )
    await db.commit()
    return SimpleNamespace(id=user_id, username=name)  # the service only reads `.id`


async def make_places(db, *codes):
    for i, code in enumerate(codes):
        db.add(
            Place(
                place_id=f"gid_{code}",
                place_code=code,
                manual_name=f"Quán {code}",
                category="Cà phê & Trà",
                address=f"{i} Giải Phóng",
                google_maps_url=None,
                lat=20.98 + i / 1000,
                lng=105.84,
                price_per_person=None,
                tiktok_urls=[],
            )
        )
    await db.commit()
    db.expunge_all()


def body(*stops, **fields) -> JourneyIn:
    """A journey body: a string is a place code, a dict is a full stop."""
    listed = [{"place_id": f"gid_{s}"} if isinstance(s, str) else s for s in stops]
    return JourneyIn.model_validate({**fields, "stops": listed})


def share_body(*codes, **fields) -> ShareIn:
    return ShareIn.model_validate({**fields, "stops": [{"place_id": f"gid_{c}"} for c in codes]})


async def error_of(coro) -> AppError:
    with pytest.raises(AppError) as info:
        await coro
    return info.value


# --- library ---------------------------------------------------------------------------------
async def test_create_then_read_back_in_order(db):
    user = await make_user(db)
    await make_places(db, "Q001", "Q002", "Q003")
    with_time = {"place_id": "gid_Q001", "planned_time": "08:30", "note": "đặt bàn"}
    made = await service.create_journey(db, user, body("Q003", with_time, "Q002", title="Cuối tuần"))
    got = await service.get_journey(db, user, made.id)
    assert got.title == "Cuối tuần"
    assert [s.stop_order for s in got.stops] == [1, 2, 3]
    assert [s.place.place_id for s in got.stops] == ["gid_Q003", "gid_Q001", "gid_Q002"]
    assert (got.stops[1].planned_time, got.stops[1].note) == (time(8, 30), "đặt bàn")
    assert got.stops[0].place.name == "Quán Q003"


async def test_an_empty_journey_can_be_saved(db):
    user = await make_user(db)
    made = await service.create_journey(db, user, body(title="Chưa có quán"))
    assert made.stops == []


async def test_same_place_twice(db):
    user = await make_user(db)
    await make_places(db, "Q001")
    made = await service.create_journey(db, user, body("Q001", "Q001"))
    assert [s.place.place_id for s in made.stops] == ["gid_Q001", "gid_Q001"]


async def test_unknown_place_is_rejected_and_nothing_is_saved(db):
    user = await make_user(db)
    await make_places(db, "Q001")
    err = await error_of(service.create_journey(db, user, body("Q001", "Q999")))
    assert (err.status_code, err.code) == (422, "unknown_place")
    assert await service.list_journeys(db, user) == []


async def test_journey_limit_is_per_account(db, monkeypatch):
    monkeypatch.setattr(rules, "MAX_JOURNEYS_PER_USER", 2)
    lan, minh = await make_user(db, "lan"), await make_user(db, "minh")
    await service.create_journey(db, lan, body())
    await service.create_journey(db, lan, body())
    err = await error_of(service.create_journey(db, lan, body()))
    assert (err.status_code, err.code) == (409, "journey_limit")
    await service.create_journey(db, minh, body())  # another account is not affected


async def test_a_creation_waits_for_another_one_of_the_same_user(db):
    """The per-user lock is what stops two simultaneous requests from both passing the limit."""
    user = await make_user(db)
    sessions = async_sessionmaker(db.bind, expire_on_commit=False)
    async with sessions() as holder, sessions() as waiting:
        await holder.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:key))"), {"key": f"journey:{user.id}"}
        )
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(service.create_journey(waiting, user, body()), timeout=0.5)
        await holder.rollback()  # releases the lock


async def test_overwriting_a_full_account_is_still_allowed(db, monkeypatch):
    monkeypatch.setattr(rules, "MAX_JOURNEYS_PER_USER", 1)
    user = await make_user(db)
    made = await service.create_journey(db, user, body())
    await service.replace_journey(db, user, made.id, body(title="đổi tên"))


async def test_list_shows_only_own_journeys_with_stop_counts(db):
    lan, minh = await make_user(db, "lan"), await make_user(db, "minh")
    await make_places(db, "Q001", "Q002")
    first = await service.create_journey(db, lan, body("Q001", "Q002", title="A"))
    second = await service.create_journey(db, lan, body(title="B"))
    await service.create_journey(db, minh, body("Q001", title="của minh"))
    rows = await service.list_journeys(db, lan)
    assert {r.id: r.stop_count for r in rows} == {first.id: 2, second.id: 0}
    assert len(await service.list_journeys(db, minh)) == 1


async def test_someone_elses_journey_looks_missing(db):
    lan, minh = await make_user(db, "lan"), await make_user(db, "minh")
    made = await service.create_journey(db, lan, body())
    assert (await error_of(service.get_journey(db, minh, made.id))).status_code == 404
    assert (await error_of(service.replace_journey(db, minh, made.id, body()))).status_code == 404
    assert (await error_of(service.delete_journey(db, minh, made.id))).status_code == 404
    assert (await service.get_journey(db, lan, made.id)).id == made.id  # untouched


async def test_replace_overwrites_order_and_content(db):
    user = await make_user(db)
    await make_places(db, "Q001", "Q002", "Q003")
    made = await service.create_journey(db, user, body("Q001", "Q002", "Q003", title="cũ"))
    again = await service.replace_journey(
        db, user, made.id, body("Q003", {"place_id": "gid_Q001", "note": "mới"}, title="mới")
    )
    assert again.title == "mới"
    assert [(s.stop_order, s.place.place_id) for s in again.stops] == [(1, "gid_Q003"), (2, "gid_Q001")]
    assert again.stops[1].note == "mới"
    assert again.id == made.id and again.created_at == made.created_at
    count = await db.scalar(select(func.count()).select_from(JourneyStop))
    assert count == 2  # the old stops are gone, not piled up


async def test_replace_moves_updated_at_even_if_only_stops_change(db):
    user = await make_user(db)
    await make_places(db, "Q001", "Q002")
    made = await service.create_journey(db, user, body("Q001", title="x"))
    again = await service.replace_journey(db, user, made.id, body("Q001", "Q002", title="x"))
    assert again.updated_at > made.updated_at


async def test_replace_with_an_unknown_place_changes_nothing(db):
    user = await make_user(db)
    await make_places(db, "Q001", "Q002")
    made = await service.create_journey(db, user, body("Q001", "Q002", title="giữ nguyên"))
    err = await error_of(service.replace_journey(db, user, made.id, body("Q001", "Q999", title="hỏng")))
    assert err.code == "unknown_place"
    still = await service.get_journey(db, user, made.id)
    assert (still.title, len(still.stops)) == ("giữ nguyên", 2)


async def test_delete_removes_the_stops_too(db):
    user = await make_user(db)
    await make_places(db, "Q001")
    made = await service.create_journey(db, user, body("Q001"))
    await service.delete_journey(db, user, made.id)
    assert await db.scalar(select(func.count()).select_from(Journey)) == 0
    assert await db.scalar(select(func.count()).select_from(JourneyStop)) == 0
    assert (await error_of(service.delete_journey(db, user, made.id))).status_code == 404


async def test_deleting_a_place_removes_it_from_journeys(db):
    user = await make_user(db)
    await make_places(db, "Q001", "Q002")
    made = await service.create_journey(db, user, body("Q001", "Q002"))
    await db.execute(text("DELETE FROM places WHERE place_id = 'gid_Q001'"))
    await db.commit()
    got = await service.get_journey(db, user, made.id)
    assert [s.place.place_id for s in got.stops] == ["gid_Q002"]


# --- share links -----------------------------------------------------------------------------
async def test_share_round_trip(db):
    await make_places(db, "Q001", "Q002")
    first = {"place_id": "gid_Q002", "planned_time": "12:00", "note": "x"}
    data = ShareIn.model_validate({"title": "Đi ăn", "stops": [first, {"place_id": "gid_Q001"}]})
    made = await service.create_share(db, data, "203.0.113.7", now=NOW)
    assert made.expires_at == NOW + timedelta(days=constants.SHARE_LIFETIME_DAYS)
    seen = await service.read_share(db, made.code, now=NOW + timedelta(hours=1))
    assert seen.title == "Đi ăn" and seen.missing_places == 0
    assert [(s.stop_order, s.place.place_id) for s in seen.stops] == [(1, "gid_Q002"), (2, "gid_Q001")]
    assert (seen.stops[0].planned_time, seen.stops[0].note) == (time(12, 0), "x")
    assert "user" not in seen.model_dump_json() and "203" not in seen.model_dump_json()


async def test_share_stores_a_hash_not_the_address(db):
    await make_places(db, "Q001")
    made = await service.create_share(db, share_body("Q001"), "203.0.113.7", now=NOW)
    row = await db.get(JourneyShare, made.code)
    assert "203.0.113.7" not in row.creator_hash and len(row.creator_hash) == 64


async def test_unknown_code_is_404(db):
    assert (await error_of(service.read_share(db, "khong-co", now=NOW))).status_code == 404


async def test_share_expires_exactly_after_the_lifetime(db):
    await make_places(db, "Q001")
    made = await service.create_share(db, share_body("Q001"), "1.1.1.1", now=NOW)
    last_good = made.expires_at - timedelta(seconds=1)
    await service.read_share(db, made.code, now=last_good)
    err = await error_of(service.read_share(db, made.code, now=made.expires_at))
    assert err.status_code == 404


async def test_creating_a_link_removes_expired_ones(db):
    await make_places(db, "Q001")
    old = await service.create_share(db, share_body("Q001"), "1.1.1.1", now=NOW)
    later = NOW + timedelta(days=constants.SHARE_LIFETIME_DAYS, seconds=1)
    new = await service.create_share(db, share_body("Q001"), "2.2.2.2", now=later)
    assert await db.get(JourneyShare, old.code) is None
    assert await db.get(JourneyShare, new.code) is not None


async def test_share_rate_limit_per_address_and_hour(db, monkeypatch):
    monkeypatch.setattr(rules, "SHARES_PER_IP_PER_HOUR", 2)
    await make_places(db, "Q001")
    for _ in range(2):
        await service.create_share(db, share_body("Q001"), "9.9.9.9", now=NOW)
    err = await error_of(service.create_share(db, share_body("Q001"), "9.9.9.9", now=NOW))
    assert (err.status_code, err.code) == (429, "too_many_shares")
    await service.create_share(db, share_body("Q001"), "8.8.8.8", now=NOW)  # another address
    await service.create_share(db, share_body("Q001"), "9.9.9.9", now=NOW + timedelta(hours=1, seconds=1))


async def test_share_with_an_unknown_place_is_rejected(db):
    await make_places(db, "Q001")
    err = await error_of(service.create_share(db, share_body("Q001", "Q999"), "1.1.1.1", now=NOW))
    assert err.code == "unknown_place"


async def test_share_survives_a_deleted_place(db):
    await make_places(db, "Q001", "Q002", "Q003")
    made = await service.create_share(db, share_body("Q001", "Q002", "Q003"), "1.1.1.1", now=NOW)
    await db.execute(text("DELETE FROM places WHERE place_id = 'gid_Q002'"))
    await db.commit()
    seen = await service.read_share(db, made.code, now=NOW)
    assert [(s.stop_order, s.place.place_id) for s in seen.stops] == [(1, "gid_Q001"), (2, "gid_Q003")]
    assert seen.missing_places == 1
