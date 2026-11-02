"""GET /api/match/{place_id}/insights through PostgreSQL: what the offline job stored is what is shown."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.modules.match import service
from app.modules.match.embedding import EMBED_MODEL
from app.modules.match.insights import Insights
from app.modules.match.insights_store import save_insights, save_summary

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _real_pipeline(monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: Settings(use_stub_match=False))


async def store(engine, place_id: str, *, faq=None, dishes=None, summary: str | None = None):
    insights = Insights(
        pros=["Không gian rộng rãi", "Có nhiều ổ điện"],
        cons=["Giá đồ uống hơi cao"],
        faq=faq or {},
        highlights=[],
    )
    async with AsyncSession(engine) as session:
        await save_insights(
            session,
            place_id=place_id,
            insights=insights,
            vectors=[],
            dishes=dishes or [],
            review_count=3,
            input_hash="h",
            llm_model="openai/gpt-oss-120b",
            embedding_model=EMBED_MODEL,
        )
        if summary:
            await save_summary(
                session, place_id=place_id, summary=summary, summary_hash="s", web_review_count=2
            )
        await session.commit()


async def test_everything_the_job_stored_is_returned(db_client, engine, seed_place):
    pid = await seed_place("ins1")
    await store(
        engine,
        pid,
        faq={"date": "Có, không gian yên tĩnh.", "study": "Có, nhiều ổ điện."},
        dishes=[{"name": "Matcha Latte", "mentions": 2}, {"name": "Cà phê muối", "mentions": 1}],
        summary="Quán rộng rãi, hợp học bài.",
    )
    r = await db_client.get(f"/api/match/{pid}/insights")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["place_id"] == pid
    assert body["summary"] == "Quán rộng rãi, hợp học bài."
    assert body["pros"] == ["Không gian rộng rãi", "Có nhiều ổ điện"]
    assert body["cons"] == ["Giá đồ uống hơi cao"]
    assert body["top_dishes"] == [
        {"name": "Matcha Latte", "mentions": 2},
        {"name": "Cà phê muối", "mentions": 1},
    ]
    assert body["generated_at"]


async def test_faq_has_the_question_text_in_a_fixed_order_and_skips_unanswered_ones(
    db_client, engine, seed_place
):
    pid = await seed_place("ins2")
    # stored in a different order, with null answers: the reviews did not say
    await store(
        engine,
        pid,
        faq={"budget": "Tuỳ, một số món đắt.", "solo": None, "study": "Có, nhiều ổ điện.", "date": None},
    )
    body = (await db_client.get(f"/api/match/{pid}/insights")).json()
    assert body["faq"] == [
        {"key": "study", "question": "Có hợp học bài / làm việc không?", "answer": "Có, nhiều ổ điện."},
        {"key": "budget", "question": "Giá có hợp với sinh viên không?", "answer": "Tuỳ, một số món đắt."},
    ]


async def test_a_place_without_website_reviews_has_no_summary(db_client, engine, seed_place):
    pid = await seed_place("ins3")
    await store(engine, pid)
    body = (await db_client.get(f"/api/match/{pid}/insights")).json()
    assert body["summary"] is None and body["faq"] == [] and body["top_dishes"] == []


async def test_a_place_without_insights_is_404_insights_not_found(db_client, seed_place):
    pid = await seed_place("ins4")
    r = await db_client.get(f"/api/match/{pid}/insights")
    assert r.status_code == 404 and r.json()["error"]["code"] == "insights_not_found"


async def test_an_unknown_place_is_404_not_found(db_client, engine):
    r = await db_client.get("/api/match/match_test_does_not_exist/insights")
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"
