"""GET /api/match/{place_id}/why with the stub provider (no database, no model needed)."""

import pytest

from app.core.config import Settings
from app.modules.match import service


@pytest.fixture(autouse=True)
def _stub_on(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=True))


async def test_why_returns_sample_bullets(client):
    r = await client.get("/api/match/stub_place_cafe_yen_tinh/why", params={"mood": "quán yên tĩnh"})
    assert r.status_code == 200
    body = r.json()
    assert body["place_id"] == "stub_place_cafe_yen_tinh"
    assert 3 <= len(body["points"]) <= 4
    assert set(body["points"][0]) == {"text", "matched"}
    assert body["why"] == "; ".join(p["text"] for p in body["points"])


async def test_why_requires_a_mood(client):
    assert (await client.get("/api/match/x/why")).status_code == 422
    assert (await client.get("/api/match/x/why", params={"mood": ""})).status_code == 422
