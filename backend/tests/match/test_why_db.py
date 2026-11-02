"""GET /api/match/{place_id}/why through PostgreSQL + pgvector, no AI model needed."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.match import service
from app.modules.match.embedding import EMBED_MODEL
from app.modules.match.insights import Highlight, Insights
from app.modules.match.insights_store import save_insights
from tests.match.conftest import query_vector, unit_vector

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _real_pipeline(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=False))

    async def fake_encode(_mood: str) -> list[float]:
        return query_vector()

    monkeypatch.setattr(service, "_encode_mood", fake_encode)


async def save_bullets(engine, place_id: str, bullets: list[tuple[str, int, float]], *, model=EMBED_MODEL):
    """bullets = (text, support, cosine similarity to the query)."""
    insights = Insights(pros=[], cons=[], faq={}, highlights=[Highlight(t, s) for t, s, _ in bullets])
    async with AsyncSession(engine) as session:
        await save_insights(
            session,
            place_id=place_id,
            insights=insights,
            vectors=[unit_vector(c) for _, _, c in bullets],
            dishes=[],
            review_count=3,
            input_hash="h",
            llm_model="openai/gpt-oss-120b",
            embedding_model=model,
        )
        await session.commit()


async def get_why(db_client, place_id: str, mood: str = "quán yên tĩnh để học bài"):
    return await db_client.get(f"/api/match/{place_id}/why", params={"mood": mood})


async def test_bullets_close_to_the_search_come_first(db_client, engine, seed_place):
    pid = await seed_place("why1")
    await save_bullets(
        engine,
        pid,
        [
            ("Không gian yên tĩnh", 2, 0.9),
            ("Có nhiều ổ điện", 3, 0.6),
            ("Giá đồ uống hơi cao", 9, 0.1),
            ("Quán thường đông vào mùa thi", 1, 0.05),
        ],
    )
    r = await get_why(db_client, pid)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["points"] == [
        {"text": "Không gian yên tĩnh", "matched": True},
        {"text": "Có nhiều ổ điện", "matched": True},
        {"text": "Giá đồ uống hơi cao", "matched": False},  # the strongest other bullet fills the list
    ]
    assert body["why"] == "Không gian yên tĩnh; Có nhiều ổ điện; Giá đồ uống hơi cao"


async def test_nothing_close_shows_general_strengths_without_claiming_a_match(db_client, engine, seed_place):
    pid = await seed_place("why2")
    await save_bullets(engine, pid, [("A", 1, 0.1), ("B", 5, 0.2), ("C", 3, 0.05), ("D", 2, 0.0)])
    body = (await get_why(db_client, pid)).json()
    assert [p["text"] for p in body["points"]] == ["B", "C", "D"]
    assert not any(p["matched"] for p in body["points"])


async def test_a_place_without_insights_gets_an_empty_list(db_client, seed_place):
    pid = await seed_place("why3")
    r = await get_why(db_client, pid)
    assert r.status_code == 200
    assert r.json() == {"place_id": pid, "why": "", "points": []}


async def test_bullets_from_another_embedding_model_are_ignored(db_client, engine, seed_place):
    pid = await seed_place("why4")
    await save_bullets(engine, pid, [("Không gian yên tĩnh", 2, 0.9)], model="some-other-model")
    assert (await get_why(db_client, pid)).json()["points"] == []


async def test_unknown_place_is_404(db_client, engine):
    r = await get_why(db_client, "match_test_does_not_exist")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
