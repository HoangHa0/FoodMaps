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


async def test_reject_and_why_are_not_implemented_yet(client):
    body = {
        "criteria": {"mood": "x"},
        "reason": "too_far",
        "rejected_place_id": "a",
        "remaining": ["b"],
    }
    assert (await client.post("/api/match/reject", json=body)).status_code == 501
    assert (await client.get("/api/match/abc/why", params={"mood": "x"})).status_code == 501
