"""GET /api/match/{place_id}/insights with the stub provider (no database, no model needed)."""

import pytest

from app.core.config import Settings
from app.modules.match import service


@pytest.fixture(autouse=True)
def _stub_on(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=True))


async def test_insights_returns_sample_data_with_the_documented_shape(client):
    r = await client.get("/api/match/stub_place_cafe_yen_tinh/insights")
    assert r.status_code == 200
    body = r.json()
    assert body["place_id"] == "stub_place_cafe_yen_tinh"
    assert {"summary", "pros", "cons", "faq", "top_dishes", "generated_at"} <= set(body)
    assert set(body["faq"][0]) == {"key", "question", "answer"}
    assert set(body["top_dishes"][0]) == {"name", "mentions"}
