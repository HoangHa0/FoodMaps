"""place_insights / place_highlights and the functions that write them (real PostgreSQL)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.modules.match.embedding import EMBED_MODEL
from app.modules.match.insights import Highlight, Insights
from app.modules.match.insights_store import (
    clear_summary,
    refresh_top_dishes,
    remove_insight,
    save_insights,
    save_summary,
)
from tests.match.conftest import PLACE_PREFIX, query_vector, unit_vector

pytestmark = pytest.mark.db


def make_insights(*highlights: tuple[str, int]) -> Insights:
    return Insights(
        pros=["Yên tĩnh"],
        cons=[],
        faq={"date": "Có.", "study": None},
        highlights=[Highlight(t, s) for t, s in highlights],
    )


async def save(engine, place_id, insights, *, input_hash="h1", dishes=None, review_count=3):
    from sqlalchemy.ext.asyncio import AsyncSession

    vectors = [unit_vector(0.1 * (i + 1)) for i in range(len(insights.highlights))]
    async with AsyncSession(engine) as session:
        await save_insights(
            session,
            place_id=place_id,
            insights=insights,
            vectors=vectors,
            dishes=dishes or [],
            review_count=review_count,
            input_hash=input_hash,
            llm_model="openai/gpt-oss-20b",
            embedding_model=EMBED_MODEL,
        )
        await session.commit()


async def one(engine, sql, **params):
    async with engine.connect() as conn:
        return (await conn.execute(text(sql), params)).all()


async def test_save_stores_every_field(engine, seed_place):
    pid = await seed_place("a")
    dishes = [{"name": "Phở bò", "mentions": 3}]
    await save(engine, pid, make_insights(("Có nhiều ổ điện", 2), ("Yên tĩnh", 3)), dishes=dishes)

    (row,) = await one(engine, "SELECT * FROM place_insights WHERE place_id = :p", p=pid)
    assert row.pros == ["Yên tĩnh"] and row.cons == []
    assert row.summary is None and row.summary_hash is None and row.web_review_count == 0
    assert row.faq == {"date": "Có.", "study": None}
    assert row.top_dishes == dishes
    assert (row.review_count, row.input_hash, row.llm_model) == (3, "h1", "openai/gpt-oss-20b")
    assert row.embedding_model == EMBED_MODEL and row.generated_at and row.updated_at

    hl = await one(engine, "SELECT content, support FROM place_highlights WHERE place_id = :p", p=pid)
    assert sorted(hl) == [("Có nhiều ổ điện", 2), ("Yên tĩnh", 3)]


async def test_saving_again_replaces_the_row_and_the_highlights(engine, seed_place):
    pid = await seed_place("a")
    await save(engine, pid, make_insights(("Cũ 1", 1), ("Cũ 2", 1)), input_hash="h1")
    await save(engine, pid, make_insights(("Mới", 4)), input_hash="h2", review_count=5)

    rows = await one(engine, "SELECT input_hash, review_count FROM place_insights WHERE place_id = :p", p=pid)
    assert rows == [("h2", 5)]  # still ONE row
    hl = await one(engine, "SELECT content FROM place_highlights WHERE place_id = :p", p=pid)
    assert hl == [("Mới",)]


async def put_summary(engine, pid, text="Tóm tắt web", digest="s1", n=2):
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(engine) as session:
        await save_summary(session, place_id=pid, summary=text, summary_hash=digest, web_review_count=n)
        await session.commit()


async def summary_row(engine, pid):
    sql = "SELECT summary, summary_hash, web_review_count FROM place_insights WHERE place_id = :p"
    return (await one(engine, sql, p=pid))[0]


async def test_the_summary_is_saved_apart_from_the_main_part(engine, seed_place):
    pid = await seed_place("a")
    await save(engine, pid, make_insights(("A1", 1)), input_hash="main1")
    await put_summary(engine, pid)

    assert tuple(await summary_row(engine, pid)) == ("Tóm tắt web", "s1", 2)
    (row,) = await one(engine, "SELECT input_hash, pros FROM place_insights WHERE place_id = :p", p=pid)
    assert row == ("main1", ["Yên tĩnh"])  # untouched


async def test_redoing_the_main_part_keeps_the_summary(engine, seed_place):
    pid = await seed_place("a")
    await save(engine, pid, make_insights(("A1", 1)), input_hash="main1")
    await put_summary(engine, pid)

    await save(engine, pid, make_insights(("A2", 3)), input_hash="main2")  # e.g. a new sheet review

    assert tuple(await summary_row(engine, pid)) == ("Tóm tắt web", "s1", 2)
    (row,) = await one(engine, "SELECT input_hash FROM place_insights WHERE place_id = :p", p=pid)
    assert row == ("main2",)


async def test_clearing_the_summary_resets_its_bookkeeping(engine, seed_place):
    from sqlalchemy.ext.asyncio import AsyncSession

    pid = await seed_place("a")
    await save(engine, pid, make_insights(("A1", 1)))
    await put_summary(engine, pid)
    async with AsyncSession(engine) as session:
        await clear_summary(session, pid)
        await session.commit()

    assert tuple(await summary_row(engine, pid)) == (None, None, 0)
    assert len(await one(engine, "SELECT 1 FROM place_highlights WHERE place_id = :p", p=pid)) == 1


async def test_a_place_with_no_highlight_is_allowed(engine, seed_place):
    pid = await seed_place("a")
    await save(engine, pid, make_insights())
    assert await one(engine, "SELECT 1 FROM place_highlights WHERE place_id = :p", p=pid) == []
    assert len(await one(engine, "SELECT 1 FROM place_insights WHERE place_id = :p", p=pid)) == 1


async def test_defaults_for_a_minimal_row(engine, seed_place):
    pid = await seed_place("a")
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "INSERT INTO place_insights (place_id, review_count, input_hash, llm_model, embedding_model) "
                "VALUES (:p, 1, 'h', 'm', 'e')"
            ),
            {"p": pid},
        )
    sql = "SELECT pros, cons, faq, top_dishes, summary, summary_hash, web_review_count FROM place_insights"
    (row,) = await one(engine, sql + " WHERE place_id = :p", p=pid)
    assert row == ([], [], {}, [], None, None, 0)


async def test_mismatched_vectors_are_refused(engine, seed_place):
    from sqlalchemy.ext.asyncio import AsyncSession

    pid = await seed_place("a")
    async with AsyncSession(engine) as session:
        with pytest.raises(ValueError, match="one embedding per highlight"):
            await save_insights(
                session,
                place_id=pid,
                insights=make_insights(("A", 1), ("B", 1)),
                vectors=[unit_vector(0.5)],
                dishes=[],
                review_count=1,
                input_hash="h",
                llm_model="m",
                embedding_model="e",
            )


async def test_the_same_bullet_twice_for_one_place_is_refused(engine, seed_place):
    pid = await seed_place("a")
    await save(engine, pid, make_insights(("Yên tĩnh", 1)))
    with pytest.raises(IntegrityError):
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO place_highlights (place_id, content, support, embedding) "
                    "VALUES (:p, 'Yên tĩnh', 1, CAST(:v AS vector))"
                ),
                {"p": pid, "v": "[" + ",".join(["0"] * 384) + "]"},
            )


async def test_deleting_the_place_or_the_insight_removes_the_highlights(engine, seed_place):
    from sqlalchemy.ext.asyncio import AsyncSession

    a, b = await seed_place("a"), await seed_place("b")
    await save(engine, a, make_insights(("A1", 1)))
    await save(engine, b, make_insights(("B1", 1)))

    async with AsyncSession(engine) as session:
        await remove_insight(session, a)
        await session.commit()
    assert await one(engine, "SELECT 1 FROM place_highlights WHERE place_id = :p", p=a) == []

    async with engine.begin() as conn:
        await conn.execute(text("DELETE FROM places WHERE place_id = :p"), {"p": b})
    assert await one(engine, "SELECT 1 FROM place_insights WHERE place_id = :p", p=b) == []
    assert await one(engine, "SELECT 1 FROM place_highlights WHERE place_id = :p", p=b) == []


async def test_refresh_top_dishes_changes_only_the_dishes(engine, seed_place):
    from sqlalchemy.ext.asyncio import AsyncSession

    pid = await seed_place("a")
    await save(engine, pid, make_insights(("A1", 1)), dishes=[{"name": "Cũ", "mentions": 1}])
    await put_summary(engine, pid, text="Tóm tắt")
    async with AsyncSession(engine) as session:
        await refresh_top_dishes(session, pid, [{"name": "Mới", "mentions": 2}])
        await session.commit()
    (row,) = await one(
        engine, "SELECT top_dishes, input_hash, summary FROM place_insights WHERE place_id = :p", p=pid
    )
    assert row == ([{"name": "Mới", "mentions": 2}], "h1", "Tóm tắt")


async def test_highlights_can_be_matched_to_a_query_by_vector(engine, seed_place):
    """What the later 'Why this place' step will do: nearest highlight of ONE place to the query."""
    pid = await seed_place("a")
    await save(engine, pid, make_insights(("Xa", 1), ("Gần", 1), ("Giữa", 1)))
    # unit_vector(0.1*(i+1)): "Xa" is cos 0.1, "Gần" is cos 0.2, "Giữa" is cos 0.3 to the query
    vec = "[" + ",".join(f"{x:.8f}" for x in query_vector()) + "]"
    rows = await one(
        engine,
        "SELECT content, 1 - (embedding <=> CAST(:v AS vector)) AS sim FROM place_highlights "
        "WHERE place_id = :p ORDER BY embedding <=> CAST(:v AS vector) LIMIT 2",
        v=vec,
        p=pid,
    )
    assert [r.content for r in rows] == ["Giữa", "Gần"]
    assert rows[0].sim == pytest.approx(0.3, abs=1e-4)


def test_test_places_use_the_shared_prefix():
    assert PLACE_PREFIX == "match_test_"
