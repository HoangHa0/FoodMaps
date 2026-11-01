"""Database side of the insights job: write one place's insights, replacing the old ones.

The MAIN call (`save_insights`) and the SUMMARY call (`save_summary`) are saved separately: each has
its own input, its own fingerprint, and one never overwrites the other's columns.

Kept out of the script so it can be tested against a real PostgreSQL. Functions do NOT commit:
the caller decides, and the script commits after every place so finished work survives a quota stop.
"""

from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, func, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.match.insights import Insights
from app.modules.match.models import PlaceHighlight, PlaceInsight


async def save_insights(
    session: AsyncSession,
    *,
    place_id: str,
    insights: Insights,
    vectors: Sequence[Sequence[float]],
    dishes: list[dict[str, Any]],
    review_count: int,
    input_hash: str,
    llm_model: str,
    embedding_model: str,
) -> None:
    """Insert or replace the MAIN-call part of the row and its highlights (one vector per highlight).

    The summary columns are left as they are, so a place keeps its summary while its pros/cons are redone.
    """
    if len(vectors) != len(insights.highlights):
        raise ValueError("one embedding per highlight is required")
    values = {
        "pros": insights.pros,
        "cons": insights.cons,
        "faq": insights.faq,
        "top_dishes": dishes,
        "review_count": review_count,
        "input_hash": input_hash,
        "llm_model": llm_model,
        "embedding_model": embedding_model,
    }
    stmt = insert(PlaceInsight).values(place_id=place_id, **values)
    stmt = stmt.on_conflict_do_update(
        index_elements=[PlaceInsight.place_id],
        set_={**values, "generated_at": func.now(), "updated_at": func.now()},
    )
    await session.execute(stmt)
    await session.execute(delete(PlaceHighlight).where(PlaceHighlight.place_id == place_id))
    session.add_all(
        PlaceHighlight(place_id=place_id, content=h.text, support=h.support, embedding=list(v))
        for h, v in zip(insights.highlights, vectors, strict=True)
    )


async def refresh_top_dishes(session: AsyncSession, place_id: str, dishes: list[dict[str, Any]]) -> None:
    """Dishes are counted by code, so they can be refreshed without calling the LLM."""
    await session.execute(
        update(PlaceInsight)
        .where(PlaceInsight.place_id == place_id)
        .values(top_dishes=dishes, updated_at=func.now())
    )


async def remove_insight(session: AsyncSession, place_id: str) -> None:
    """Delete a place's insight (its highlights go with it)."""
    await session.execute(delete(PlaceInsight).where(PlaceInsight.place_id == place_id))


async def save_summary(
    session: AsyncSession, *, place_id: str, summary: str, summary_hash: str, web_review_count: int
) -> None:
    """Store the AI summary (written from website reviews only). The insight row must already exist."""
    await session.execute(
        update(PlaceInsight)
        .where(PlaceInsight.place_id == place_id)
        .values(
            summary=summary,
            summary_hash=summary_hash,
            web_review_count=web_review_count,
            updated_at=func.now(),
        )
    )


async def clear_summary(session: AsyncSession, place_id: str) -> None:
    """The place has no website review any more: remove a summary that is now out of date."""
    await session.execute(
        update(PlaceInsight)
        .where(PlaceInsight.place_id == place_id)
        .values(summary=None, summary_hash=None, web_review_count=0, updated_at=func.now())
    )
