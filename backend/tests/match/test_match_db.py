"""POST /api/match through the real pipeline, without requiring the embedding model."""

import pytest

from app.core.config import Settings
from app.modules.match import service
from tests.match.conftest import query_vector

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _real_pipeline(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=False))

    async def fake_encode(_mood: str) -> list[float]:
        return query_vector()

    monkeypatch.setattr(service, "_encode_mood", fake_encode)


async def test_match_hides_sheet_ratings_without_changing_their_effect_on_ranking(db_client, seed_place):
    sheet_rated = await seed_place("sheet-rated", cosine=0.5, crowd=["Đông"])
    no_reviews = await seed_place("no-reviews", cosine=0.5)

    response = await db_client.post("/api/match", json={"mood": "quán yên tĩnh"})

    assert response.status_code == 200, response.text
    body = response.json()
    results = [body["best"], *body["backups"]]
    by_id = {result["place_id"]: result for result in results}
    assert by_id[sheet_rated]["match_score"] > by_id[no_reviews]["match_score"]
    assert by_id[sheet_rated]["avg_rating"] is None
    assert by_id[sheet_rated]["review_count"] == 0
    assert not any(reason.startswith("⭐ ") for reason in by_id[sheet_rated]["reasons"])
