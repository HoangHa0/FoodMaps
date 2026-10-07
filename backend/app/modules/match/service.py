"""match business logic.

Other modules must not import this file; expose what they need through app/shared/.

Pipeline (shared by AI Match, Group Session and Food Journey, only `k` differs):
    1. encode the mood into a vector
    2. ONE SQL query: cosine similarity (pgvector) + bounding box (radius pre-filter) + category
       + our own review average, for every place that has an embedding from the current model
    3. in Python: exact distance, hard filters (radius, budget), Match Score, top k  (scoring.py)
    4. short tags for the winners only, taken from their reviews
"""

import math
from collections import defaultdict

from fastapi.concurrency import run_in_threadpool
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.errors import AppError
from app.modules.match.embedding import EMBED_MODEL, encode_queries
from app.modules.match.models import Place, PlaceEmbedding
from app.modules.match.schemas import MatchResponse, MatchResult
from app.modules.match.scoring import (
    RawCandidate,
    Scored,
    build_reasons,
    haversine_m,
    score_candidates,
)
from app.modules.match.text_builder import top_values
from app.modules.reviews.models import Review
from app.shared.contracts import MatchCriteria, PlaceCandidate, StubCandidateProvider

BACKUP_COUNT = 3  # spec: "top 2-3 quán dự phòng"
POOL_LIMIT = 300  # safety cap on rows read per search (the real data is 100-300 places)
METERS_PER_DEGREE = 111_320
MAX_TAGS = 4


# --------------------------------------------------------------------------- helpers


def _validate(criteria: MatchCriteria) -> None:
    lo, hi = criteria.price_min, criteria.price_max
    if lo is not None and hi is not None and lo > hi:
        raise AppError(422, "invalid_budget", "Ngân sách tối thiểu không được lớn hơn tối đa")


def _bounding_box(lat: float, lng: float, radius_m: int) -> tuple[float, float, float, float]:
    """Cheap pre-filter on plain columns; the exact radius is checked with haversine afterwards."""
    dlat = radius_m / METERS_PER_DEGREE
    dlng = radius_m / (METERS_PER_DEGREE * max(math.cos(math.radians(lat)), 0.01))
    return lat - dlat, lat + dlat, lng - dlng, lng + dlng


async def _encode_mood(mood: str) -> list[float]:
    try:
        return (await run_in_threadpool(encode_queries, [mood]))[0]
    except ImportError:
        raise AppError(503, "match_unavailable", "Tìm quán bằng AI chưa sẵn sàng, thử lại sau") from None


async def _tags_for(db: AsyncSession, scored: list[Scored]) -> dict[str, list[str]]:
    """Up to 4 short tags per place from its visible reviews: suitable_for > atmosphere > food_types."""
    if not scored:
        return {}
    rows = await db.execute(
        select(Review.place_id, Review.suitable_for, Review.atmosphere, Review.food_types).where(
            Review.place_id.in_([s.place_id for s in scored]), Review.status == "visible"
        )
    )
    by_place: dict[str, list] = defaultdict(list)
    for row in rows:
        by_place[row.place_id].append(row)

    tags: dict[str, list[str]] = {}
    for s in scored:
        rs = by_place[s.place_id]
        picked: list[str] = []
        for values in (
            top_values((t for r in rs for t in r.suitable_for), 2),
            top_values((t for r in rs for t in r.atmosphere), 2),
            top_values((t for r in rs for t in r.food_types), 1),
        ):
            for v in values:
                if v.casefold() not in {p.casefold() for p in picked}:
                    picked.append(v)
        tags[s.place_id] = (picked or [s.category])[:MAX_TAGS]
    return tags


# --------------------------------------------------------------------------- pipeline


class MatchCandidateProvider:
    """Satisfies `shared.contracts.CandidateProvider` (used by Group Session and Journey).

    `get_candidate_provider()` creates it WITHOUT a session, so it opens its own short-lived one.
    The /api/match router passes the request's session instead.
    """

    def __init__(self, db: AsyncSession | None = None) -> None:
        self._db = db

    async def find_candidates(self, criteria: MatchCriteria, k: int) -> list[PlaceCandidate]:
        results = await self.search(criteria, k)
        return [PlaceCandidate(**r.model_dump(exclude={"reasons"})) for r in results]

    async def search(self, criteria: MatchCriteria, k: int) -> list[MatchResult]:
        _validate(criteria)
        if self._db is not None:
            return await self._search(self._db, criteria, k)
        async with SessionLocal() as db:
            return await self._search(db, criteria, k)

    async def _search(self, db: AsyncSession, criteria: MatchCriteria, k: int) -> list[MatchResult]:
        query_vec = await _encode_mood(criteria.mood)

        ratings = (
            select(
                Review.place_id.label("place_id"),
                func.avg(
                    (Review.score_food + Review.score_space + Review.score_price + Review.score_service) / 4.0
                ).label("avg_rating"),
                func.count().label("n_reviews"),
            )
            .where(Review.status == "visible")
            .group_by(Review.place_id)
            .subquery()
        )
        distance = PlaceEmbedding.embedding.cosine_distance(query_vec)
        stmt = (
            select(
                Place.place_id,
                Place.category,
                Place.lat,
                Place.lng,
                Place.price_per_person,
                (1 - distance).label("similarity"),
                ratings.c.avg_rating,
                ratings.c.n_reviews,
            )
            .join(PlaceEmbedding, PlaceEmbedding.place_id == Place.place_id)
            .outerjoin(ratings, ratings.c.place_id == Place.place_id)
            .where(PlaceEmbedding.model_name == EMBED_MODEL)  # a query vector only matches its own model
            .order_by(distance)
            .limit(POOL_LIMIT)
        )
        if criteria.categories:
            stmt = stmt.where(func.lower(Place.category).in_([c.lower() for c in criteria.categories]))
        origin = criteria.origin
        if origin is not None:
            lat_lo, lat_hi, lng_lo, lng_hi = _bounding_box(origin.lat, origin.lng, criteria.radius_m)
            stmt = stmt.where(Place.lat.between(lat_lo, lat_hi), Place.lng.between(lng_lo, lng_hi))

        rows = (await db.execute(stmt)).all()
        pool = [
            RawCandidate(
                place_id=r.place_id,
                category=r.category,
                price_per_person=r.price_per_person,
                similarity=float(r.similarity),
                distance_m=(
                    None if origin is None else round(haversine_m(origin.lat, origin.lng, r.lat, r.lng))
                ),
                avg_rating=None if r.avg_rating is None else float(r.avg_rating),  # Decimal -> float
                n_reviews=int(r.n_reviews or 0),
            )
            for r in rows
        ]
        top = score_candidates(
            pool,
            radius_m=criteria.radius_m,
            price_min=criteria.price_min,
            price_max=criteria.price_max,
            k=k,
        )
        tags = await _tags_for(db, top)
        return [
            MatchResult(
                place_id=s.place_id,
                match_score=round(s.score, 4),
                tags=tags[s.place_id],
                distance_m=s.distance_m,
                price_per_person=s.price_per_person,
                avg_rating=None if s.avg_rating is None else round(s.avg_rating, 1),
                review_count=s.n_reviews,
                reasons=build_reasons(s),
            )
            for s in top
        ]


# --------------------------------------------------------------------------- endpoint logic


def split_best_and_backups(results: list[MatchResult]) -> MatchResponse:
    return MatchResponse(best=results[0] if results else None, backups=results[1 : 1 + BACKUP_COUNT])


async def match(db: AsyncSession, criteria: MatchCriteria) -> MatchResponse:
    """POST /api/match. With USE_STUB_MATCH=true it returns sample data so the UI can be built first."""
    k = 1 + BACKUP_COUNT
    if get_settings().use_stub_match:
        _validate(criteria)
        stub = await StubCandidateProvider().find_candidates(criteria, k)
        return split_best_and_backups([MatchResult(**c.model_dump()) for c in stub])
    return split_best_and_backups(await MatchCandidateProvider(db).search(criteria, k))
