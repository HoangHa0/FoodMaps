"""/api/match with the stub provider (no database, no model needed)."""

import pytest

from app.core.config import Settings
from app.modules.match import service


@pytest.fixture(autouse=True)
def _stub_on(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=True))


async def test_match_returns_best_and_three_backups(client):
    r = await client.post("/api/match", json={"mood": "quán yên tĩnh để học bài"})
    assert r.status_code == 200
    body = r.json()
    assert body["best"]["place_id"] == "stub_place_cafe_yen_tinh"
    assert len(body["backups"]) == 3
    expected = {
        "place_id", "match_score", "tags", "distance_m", "reasons",
        "price_per_person", "avg_rating", "review_count",
    }  # fmt: skip
    assert expected <= set(body["best"])


async def test_match_rejects_inverted_budget(client):
    r = await client.post("/api/match", json={"mood": "x", "price_min": 200_000, "price_max": 100_000})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_budget"


async def test_match_requires_mood(client):
    assert (await client.post("/api/match", json={})).status_code == 422


def _reject_body(reason="too_far", rejected="stub_place_cafe_yen_tinh", remaining=None, **criteria):
    return {
        "criteria": {"mood": "x", **criteria},
        "reason": reason,
        "rejected_place_id": rejected,
        "remaining": remaining
        if remaining is not None
        else ["stub_place_bun_cha", "stub_place_tra_chanh", "stub_place_lau_nuong"],
    }


async def test_reject_never_returns_the_rejected_place(client):
    r = await client.post("/api/match/reject", json=_reject_body(rejected="stub_place_bun_cha"))
    assert r.status_code == 200
    body = r.json()
    ids = [body["best"]["place_id"]] + [b["place_id"] for b in body["backups"]]
    assert "stub_place_bun_cha" not in ids
    assert sorted(ids) == ["stub_place_lau_nuong", "stub_place_tra_chanh"]


async def test_reject_too_far_puts_the_closest_remaining_place_first(client):
    # the stub places get further away the lower they are in the list
    r = await client.post(
        "/api/match/reject",
        json=_reject_body(remaining=["stub_place_lau_nuong", "stub_place_tra_chanh", "stub_place_bun_cha"]),
    )
    body = r.json()
    assert body["best"]["place_id"] == "stub_place_bun_cha"
    assert [b["place_id"] for b in body["backups"]] == ["stub_place_tra_chanh", "stub_place_lau_nuong"]


async def test_reject_with_no_backups_left_returns_nothing(client):
    r = await client.post("/api/match/reject", json=_reject_body(remaining=[]))
    assert r.status_code == 200 and r.json() == {"best": None, "backups": []}


async def test_reject_ignores_a_remaining_id_equal_to_the_rejected_one(client):
    body = _reject_body(rejected="stub_place_bun_cha", remaining=["stub_place_bun_cha"])
    r = await client.post("/api/match/reject", json=body)
    assert r.json() == {"best": None, "backups": []}


async def test_reject_validates_the_input(client):
    assert (await client.post("/api/match/reject", json=_reject_body(reason="boring"))).status_code == 422
    too_many = _reject_body(remaining=[f"p{i}" for i in range(11)])
    assert (await client.post("/api/match/reject", json=too_many)).status_code == 422
    bad_budget = _reject_body(price_min=200_000, price_max=100_000)
    r = await client.post("/api/match/reject", json=bad_budget)
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_budget"


async def test_why_is_not_implemented_yet(client):
    assert (await client.get("/api/match/abc/why", params={"mood": "x"})).status_code == 501
