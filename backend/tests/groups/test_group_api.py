"""M5 integration tests against a real PostgreSQL (foodmaps_test), using the stub CandidateProvider."""

import asyncio

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from tests.conftest import TEST_DATABASE_URL

pytestmark = pytest.mark.db

CRITERIA = {"criteria": {"mood": "ăn tối cùng nhóm"}}
K = get_settings().group_candidate_count  # number of candidate cards per room (6)


# --------------------------------------------------------------------------- helpers


async def create(c, name="Hà"):
    r = await c.post("/api/groups", json={"display_name": name})
    assert r.status_code == 201, r.text
    return r.json()


async def join(c, code, name):
    return await c.post(f"/api/groups/{code}/join", json={"display_name": name})


def h(member):
    """X-Participant-Token header of a member (the JoinedOut dict)."""
    return {"X-Participant-Token": member["participant_token"]}


async def state(c, member, **params):
    r = await c.get(f"/api/groups/{member['code']}", headers=h(member), params=params)
    assert r.status_code == 200, r.text
    return r.json()


async def start(c, host):
    r = await c.post(f"/api/groups/{host['code']}/start", json=CRITERIA, headers=h(host))
    assert r.status_code == 200, r.text
    return r.json()


async def vote(c, member, candidate_id, liked=True):
    return await c.post(
        f"/api/groups/{member['code']}/votes",
        json={"candidate_id": candidate_id, "liked": liked},
        headers=h(member),
    )


async def room_with_members(c, n):
    """A room with n members in total (host first), not started yet."""
    host = await create(c, "Host")
    members = [host]
    for i in range(1, n):
        r = await join(c, host["code"], f"Ban {i}")
        assert r.status_code == 201, r.text
        members.append(r.json())
    return members


async def expire_now(code: str):
    """Move expires_at into the past directly in the DB, so the test does not wait 30 minutes."""
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(
            text("UPDATE group_rooms SET expires_at = now() - interval '1 minute' WHERE code = :c"),
            {"c": code},
        )
    await engine.dispose()


# --------------------------------------------------------------------------- create / join


async def test_create_room_makes_a_host_in_the_lobby(db_client):
    host = await create(db_client)
    assert host["is_host"] is True and len(host["code"]) == 6
    s = await state(db_client, host)
    assert s["status"] == "lobby" and s["candidates"] == []
    assert [p["display_name"] for p in s["participants"]] == ["Hà"]
    assert s["participants"][0]["is_host"] is True
    assert s["me"] == host["participant_id"]


async def test_code_collision_retries_with_a_new_code(db_client, monkeypatch):
    from app.modules.groups import service

    monkeypatch.setattr(service, "new_room_code", lambda: "AAAAAA")
    assert (await create(db_client, "A"))["code"] == "AAAAAA"
    codes = iter(["AAAAAA", "AAAAAA", "BBBBBB"])  # two collisions, then a free code
    monkeypatch.setattr(service, "new_room_code", lambda: next(codes))
    second = await create(db_client, "B")
    assert second["code"] == "BBBBBB"
    assert (await state(db_client, second))["participants"][0]["display_name"] == "B"


async def test_join_lowercase_code_and_member_list(db_client):
    host = await create(db_client)
    r = await join(db_client, host["code"].lower(), "An")  # codes are case-insensitive
    assert r.status_code == 201 and r.json()["is_host"] is False
    names = [p["display_name"] for p in (await state(db_client, host))["participants"]]
    assert names == ["Hà", "An"]


async def test_duplicate_name_ignores_case(db_client):
    host = await create(db_client, "Hà")
    r = await join(db_client, host["code"], "hà")
    assert r.status_code == 409 and r.json()["error"]["code"] == "name_taken"


async def test_blank_name_is_422(db_client):
    assert (await db_client.post("/api/groups", json={"display_name": "   "})).status_code == 422


async def test_unknown_room_is_404(db_client):
    assert (await join(db_client, "ZZZZZZ", "An")).status_code == 404


async def test_room_full(db_client, monkeypatch):
    monkeypatch.setattr(get_settings(), "group_max_participants", 2)
    host = await create(db_client)
    assert (await join(db_client, host["code"], "An")).status_code == 201
    r = await join(db_client, host["code"], "Binh")
    assert r.status_code == 409 and r.json()["error"]["code"] == "room_full"


async def test_cannot_join_after_start(db_client):
    host = await create(db_client)
    await start(db_client, host)
    r = await join(db_client, host["code"], "An")
    assert r.status_code == 409 and r.json()["error"]["code"] == "room_started"


# --------------------------------------------------------------------------- authentication


async def test_wrong_token_is_401_and_token_does_not_work_in_another_room(db_client):
    a = await create(db_client, "A")
    b = await create(db_client, "B")
    r = await db_client.get(f"/api/groups/{b['code']}", headers=h(a))  # A's token in room B
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_participant_token"
    r = await db_client.get(f"/api/groups/{a['code']}", headers={"X-Participant-Token": "bad"})
    assert r.status_code == 401


async def test_missing_token_header_is_422(db_client):
    host = await create(db_client)
    assert (await db_client.get(f"/api/groups/{host['code']}")).status_code == 422


async def test_only_host_can_start_and_finalize(db_client):
    host, guest = await room_with_members(db_client, 2)
    r = await db_client.post(f"/api/groups/{host['code']}/start", json=CRITERIA, headers=h(guest))
    assert r.status_code == 403 and r.json()["error"]["code"] == "not_host"
    await start(db_client, host)
    r = await db_client.post(f"/api/groups/{host['code']}/finalize", headers=h(guest))
    assert r.status_code == 403


# --------------------------------------------------------------------------- start / vote / decide


async def test_start_creates_candidates_and_fixes_member_count(db_client):
    host, _, _ = await room_with_members(db_client, 3)
    s = await start(db_client, host)
    assert s["status"] == "voting"
    assert len(s["candidates"]) == K
    assert [c["rank"] for c in s["candidates"]] == list(range(K))
    assert all(c["likes"] == 0 and c["my_vote"] is None for c in s["candidates"])
    assert s["majority_threshold"] == 2  # 3 members -> more than 50% = 2
    r = await db_client.post(f"/api/groups/{host['code']}/start", json=CRITERIA, headers=h(host))
    assert r.status_code == 409  # already started


async def test_full_flow_decides_automatically_at_majority(db_client):
    host, a, b = await room_with_members(db_client, 3)
    cands = (await start(db_client, host))["candidates"]
    target = cands[2]["id"]

    s = (await vote(db_client, host, target)).json()
    assert s["status"] == "voting"  # 1 of 3: not yet
    mine = {c["id"]: c["my_vote"] for c in s["candidates"]}
    assert mine[target] is True and mine[cands[0]["id"]] is None

    s = (await vote(db_client, a, target)).json()  # 2 of 3 -> majority
    assert s["status"] == "decided"
    assert s["winner_place_id"] == cands[2]["place_id"] and s["decided_by"] == "majority"

    r = await vote(db_client, b, target)  # voting is over
    assert r.status_code == 409 and r.json()["error"]["code"] == "room_not_voting"


async def test_changing_a_vote_updates_instead_of_adding(db_client):
    host, _ = await room_with_members(db_client, 2)
    cid = (await start(db_client, host))["candidates"][0]["id"]
    await vote(db_client, host, cid, liked=True)
    s = (await vote(db_client, host, cid, liked=False)).json()
    card = next(c for c in s["candidates"] if c["id"] == cid)
    assert card["likes"] == 0 and card["my_vote"] is False
    assert s["participants"][0]["votes_cast"] == 1


async def test_all_voted_picks_most_liked(db_client):
    host, a, b = await room_with_members(db_client, 3)
    cands = (await start(db_client, host))["candidates"]
    likes_by = {0: host, 1: a, 2: b}  # each member likes a different card: no majority
    s = None
    for i, member in enumerate((host, a, b)):
        for j, c in enumerate(cands):
            s = (await vote(db_client, member, c["id"], liked=(likes_by.get(j) is member))).json()
            if i < 2:
                assert s["status"] == "voting"
    # all 3 x K cards voted, 1 like each on cards 0..2 -> tie broken by rank -> card 0
    assert s["status"] == "decided" and s["decided_by"] == "all_voted"
    assert s["winner_place_id"] == cands[0]["place_id"]


async def test_all_voted_with_no_like_stays_open(db_client):
    host, a = await room_with_members(db_client, 2)
    cands = (await start(db_client, host))["candidates"]
    for member in (host, a):
        for c in cands:
            s = (await vote(db_client, member, c["id"], liked=False)).json()
    assert s["status"] == "voting" and s["winner_place_id"] is None


async def test_candidate_from_another_room_is_404(db_client):
    host1, _ = await room_with_members(db_client, 2)
    host2, _ = await room_with_members(db_client, 2)
    await start(db_client, host1)
    other = (await start(db_client, host2))["candidates"][0]["id"]
    r = await vote(db_client, host1, other)
    assert r.status_code == 404 and r.json()["error"]["code"] == "candidate_not_found"


async def test_host_finalize(db_client):
    host, a, b = await room_with_members(db_client, 3)
    cands = (await start(db_client, host))["candidates"]
    r = await db_client.post(f"/api/groups/{host['code']}/finalize", headers=h(host))
    assert r.status_code == 409 and r.json()["error"]["code"] == "no_likes_yet"
    await vote(db_client, a, cands[1]["id"])
    r = await db_client.post(f"/api/groups/{host['code']}/finalize", headers=h(host))
    assert r.status_code == 200
    s = r.json()
    assert s["status"] == "decided" and s["decided_by"] == "host"
    assert s["winner_place_id"] == cands[1]["place_id"]


# --------------------------------------------------------------------------- polling


async def test_since_version_returns_changed_false_when_nothing_changed(db_client):
    host = await create(db_client)
    s = await state(db_client, host)
    idle = await state(db_client, host, since_version=s["version"])
    assert idle["changed"] is False and idle["participants"] == []
    await join(db_client, host["code"], "An")  # a change bumps the version
    fresh = await state(db_client, host, since_version=s["version"])
    assert fresh["changed"] is True and fresh["version"] == s["version"] + 1
    assert len(fresh["participants"]) == 2


async def test_state_includes_timing_fields(db_client):
    host = await create(db_client)
    s = await state(db_client, host)
    assert s["poll_interval_ms"] == get_settings().group_poll_interval_ms
    assert s["expires_at"] > s["server_time"]


# --------------------------------------------------------------------------- expiry


async def test_expired_lobby(db_client):
    host = await create(db_client)
    await expire_now(host["code"])
    assert (await state(db_client, host))["status"] == "expired"
    r = await join(db_client, host["code"], "An")
    assert r.status_code == 410 and r.json()["error"]["code"] == "room_expired"


async def test_expired_voting_room_with_likes_is_decided(db_client):
    host, a = await room_with_members(db_client, 2)
    cands = (await start(db_client, host))["candidates"]
    await vote(db_client, a, cands[3]["id"])
    await expire_now(host["code"])
    s = await state(db_client, host)
    assert s["status"] == "decided" and s["decided_by"] == "expired"
    assert s["winner_place_id"] == cands[3]["place_id"]


# --------------------------------------------------------------------------- concurrency


async def test_simultaneous_votes_decide_exactly_once(db_client):
    """3 members like the same card at the same moment: each request gets its own DB session.

    The FOR UPDATE lock makes them queue up, so the counts are never stale: the room is decided
    exactly once and every vote bumps the version exactly once.
    """
    members = await room_with_members(db_client, 3)
    host = members[0]
    target = (await start(db_client, host))["candidates"][0]["id"]
    v0 = (await state(db_client, host))["version"]

    results = await asyncio.gather(*(vote(db_client, m, target) for m in members))
    codes = sorted(r.status_code for r in results)
    # majority (2 of 3) is reached by the 2nd vote to commit; the 3rd finds the room decided
    assert codes == [200, 200, 409]

    s = await state(db_client, host)
    assert s["status"] == "decided" and s["decided_by"] == "majority"
    assert s["version"] == v0 + 2  # two accepted votes, one decision, no double increment
    assert next(c for c in s["candidates"] if c["id"] == target)["likes"] == 2
