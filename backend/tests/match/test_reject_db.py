"""POST /api/match/reject through the real pipeline (PostgreSQL + pgvector), no AI model needed."""

import pytest

from app.core.config import Settings
from app.modules.match import service
from tests.match.conftest import ORIGIN, query_vector

pytestmark = pytest.mark.db

CRITERIA = {"mood": "quán yên tĩnh", "origin": {"lat": ORIGIN[0], "lng": ORIGIN[1]}, "radius_m": 2000}


@pytest.fixture(autouse=True)
def _real_pipeline(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=False))

    async def fake_encode(_mood: str) -> list[float]:
        return query_vector()

    monkeypatch.setattr(service, "_encode_mood", fake_encode)


def _body(reason: str, rejected: str, remaining: list[str], **criteria) -> dict:
    return {
        "criteria": {**CRITERIA, **criteria},
        "reason": reason,
        "rejected_place_id": rejected,
        "remaining": remaining,
    }


def _ids(body: dict) -> list[str]:
    return ([body["best"]["place_id"]] if body["best"] else []) + [b["place_id"] for b in body["backups"]]


async def test_too_far_puts_the_closest_remaining_place_first(db_client, seed_place):
    rejected = await seed_place("rejected", cosine=0.6, meters_north=100)
    near = await seed_place("near", cosine=0.45, meters_north=150)
    mid = await seed_place("mid", cosine=0.5, meters_north=900)
    far = await seed_place("far", cosine=0.55, meters_north=1800)

    r = await db_client.post("/api/match/reject", json=_body("too_far", rejected, [far, mid, near]))

    assert r.status_code == 200, r.text
    body = r.json()
    assert _ids(body) == [near, mid, far]
    assert body["best"]["distance_m"] < 200  # the card still has real numbers
    assert body["best"]["match_score"] > 0


async def test_too_expensive_puts_the_cheapest_first(db_client, seed_place):
    rejected = await seed_place("rejected", price=120_000)
    dear = await seed_place("dear", cosine=0.55, price=150_000)
    cheap = await seed_place("cheap", cosine=0.50, price=30_000)

    r = await db_client.post("/api/match/reject", json=_body("too_expensive", rejected, [dear, cheap]))

    assert _ids(r.json()) == [cheap, dear]


async def test_too_crowded_puts_the_quietest_first(db_client, seed_place):
    rejected = await seed_place("rejected", crowd=["Đông"])
    packed = await seed_place("packed", cosine=0.55, crowd=["Rất đông", "Đông"])
    quiet = await seed_place("quiet", cosine=0.50, crowd=["Vắng"])

    r = await db_client.post("/api/match/reject", json=_body("too_crowded", rejected, [packed, quiet]))

    assert _ids(r.json()) == [quiet, packed]


async def test_wrong_vibe_puts_the_best_mood_match_first(db_client, seed_place):
    rejected = await seed_place("rejected", cosine=0.5)
    near_wrong = await seed_place("near_wrong", cosine=0.2, meters_north=50)
    far_right = await seed_place("far_right", cosine=0.6, meters_north=1500)

    r = await db_client.post("/api/match/reject", json=_body("wrong_vibe", rejected, [near_wrong, far_right]))

    assert _ids(r.json()) == [far_right, near_wrong]


async def test_only_the_remaining_places_are_considered(db_client, seed_place):
    rejected = await seed_place("rejected")
    wanted = await seed_place("wanted")
    await seed_place("not_in_the_list", cosine=0.9)  # better, but the client no longer holds it

    r = await db_client.post("/api/match/reject", json=_body("wrong_vibe", rejected, [wanted]))

    assert _ids(r.json()) == [wanted]


async def test_the_rejected_place_is_never_returned(db_client, seed_place):
    rejected = await seed_place("rejected", cosine=0.9)
    other = await seed_place("other")

    r = await db_client.post("/api/match/reject", json=_body("too_far", rejected, [rejected, other]))

    assert _ids(r.json()) == [other]


async def test_hard_filters_still_apply(db_client, seed_place):
    rejected = await seed_place("rejected")
    inside = await seed_place("inside", meters_north=500, price=50_000)
    outside = await seed_place("outside", meters_north=5000, price=50_000)  # beyond the 2 km radius
    too_dear = await seed_place("too_dear", meters_north=500, price=500_000)

    r = await db_client.post(
        "/api/match/reject",
        json=_body("too_far", rejected, [inside, outside, too_dear], price_max=100_000),
    )

    assert _ids(r.json()) == [inside]


async def test_a_place_without_embedding_is_dropped(db_client, seed_place):
    rejected = await seed_place("rejected")
    ok = await seed_place("ok")
    no_vector = await seed_place("no_vector", embedding=False)

    r = await db_client.post("/api/match/reject", json=_body("wrong_vibe", rejected, [ok, no_vector]))

    assert _ids(r.json()) == [ok]


async def test_nothing_left_gives_an_empty_answer(db_client, seed_place):
    rejected = await seed_place("rejected")

    r = await db_client.post("/api/match/reject", json=_body("too_far", rejected, []))

    assert r.status_code == 200 and r.json() == {"best": None, "backups": []}


async def test_without_origin_the_distance_is_null_and_nothing_crashes(db_client, seed_place):
    rejected = await seed_place("rejected")
    a = await seed_place("a", cosine=0.6)
    b = await seed_place("b", cosine=0.4)
    body = _body("too_far", rejected, [b, a])
    body["criteria"].pop("origin")

    r = await db_client.post("/api/match/reject", json=body)

    assert r.status_code == 200
    assert _ids(r.json()) == [a, b]  # no origin: the order falls back to the match score
    assert r.json()["best"]["distance_m"] is None
