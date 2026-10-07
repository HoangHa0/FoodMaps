"""Match Score: pure functions (no database, no model, no FastAPI), easy to unit test.

Final score = weighted average of four components, each in 0..1:

    semantic  how close the place's embedding is to the mood (cosine similarity, calibrated)
    distance  1 at the origin, 0 at the edge of the radius (skipped when there is no origin)
    rating    average of our own reviews, shrunk towards a neutral prior
    budget    1 when the price is inside [price_min, price_max] (skipped when no budget is given).

A component that does not apply (no origin, no budget) is dropped and the remaining weights are
re-normalised, so a search without a location is not punished for it.

All tunable numbers are constants at the top: adjust them after looking at real data
(`scripts/try_match.py` prints the raw cosine values).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

# --- weights (relative; they are re-normalised) -------------
W_SEMANTIC = 0.55
W_DISTANCE = 0.20
W_RATING = 0.15
W_BUDGET = 0.10

# --- semantic calibration ---------------------------------------------------------------------
# paraphrase-multilingual-MiniLM cosine for a relevant place is typically 0.2-0.6, so it cannot be
# shown as a percentage directly. Values <= SIM_LOW map to 0 and >= SIM_HIGH map to 1.
SIM_LOW = 0.15
SIM_HIGH = 0.60

# --- rating (our own reviews) -----------------------------------------------------------------
RATING_PRIOR = 3.5  # average score (1..5) assumed for a place with no reviews
RATING_PRIOR_WEIGHT = 3  # how many "virtual reviews" the prior counts for

# --- budget -----------------------------------------------------------------------------------
BUDGET_UNKNOWN_SCORE = 0.5  # the place has no price but the user gave a budget

EARTH_RADIUS_M = 6_371_000


def clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def haversine_m(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_M * math.asin(math.sqrt(a))


def semantic_score(cosine: float) -> float:
    return clamp01((cosine - SIM_LOW) / (SIM_HIGH - SIM_LOW))


def distance_score(distance_m: float, radius_m: int) -> float:
    return clamp01(1 - distance_m / radius_m)


def rating_score(avg_rating: float | None, n_reviews: int) -> float:
    """Bayesian average: one 5-star review does not beat ten 4.5-star reviews."""
    n = n_reviews if avg_rating is not None else 0
    total = (avg_rating or 0.0) * n + RATING_PRIOR * RATING_PRIOR_WEIGHT
    shrunk = total / (n + RATING_PRIOR_WEIGHT)
    return clamp01((shrunk - 1) / 4)


def budget_allowed(price: int | None, price_min: int | None, price_max: int | None) -> bool:
    """Hard filter on the exact price stored in the database. No tolerance.

    An unknown price is kept: we cannot prove the place is out of budget.
    """
    if price is None:
        return True
    if price_min is not None and price < price_min:
        return False
    return not (price_max is not None and price > price_max)


def budget_score(price: int | None, price_min: int | None, price_max: int | None) -> float | None:
    """None = no budget given, so the component does not apply."""
    if price_min is None and price_max is None:
        return None
    if price is None:
        return BUDGET_UNKNOWN_SCORE
    return 1.0 if budget_allowed(price, price_min, price_max) else 0.0


def combine(components: dict[str, float | None]) -> float:
    weights = {
        "semantic": W_SEMANTIC,
        "distance": W_DISTANCE,
        "rating": W_RATING,
        "budget": W_BUDGET,
    }
    used = {name: w for name, w in weights.items() if components.get(name) is not None}
    total = sum(used.values())
    if total == 0:
        return 0.0
    return clamp01(sum(components[name] * w for name, w in used.items()) / total)  


@dataclass(frozen=True)
class RawCandidate:
    """One row coming out of the database, before scoring."""

    place_id: str
    category: str
    price_per_person: int | None
    similarity: float  # raw cosine similarity (-1..1)
    distance_m: int | None  # None when the search has no origin
    avg_rating: float | None  # mean of the 4 review scores, None when there is no review
    n_reviews: int


@dataclass(frozen=True)
class Scored:
    place_id: str
    category: str
    score: float
    distance_m: int | None
    components: dict[str, float | None] = field(default_factory=dict)
    price_per_person: int | None = None
    n_reviews: int = 0
    avg_rating: float | None = None  # raw mean of the review scores (1..5), NOT the shrunk one


def score_candidates(
    rows: Sequence[RawCandidate],
    *,
    radius_m: int,
    price_min: int | None,
    price_max: int | None,
    k: int,
) -> list[Scored]:
    """Apply the hard filters (radius, budget), score the survivors, return the best k."""
    scored: list[Scored] = []
    for r in rows:
        if r.distance_m is not None and r.distance_m > radius_m:
            continue
        if not budget_allowed(r.price_per_person, price_min, price_max):
            continue
        components = {
            "semantic": semantic_score(r.similarity),
            "distance": None if r.distance_m is None else distance_score(r.distance_m, radius_m),
            "rating": rating_score(r.avg_rating, r.n_reviews),
            "budget": budget_score(r.price_per_person, price_min, price_max),
        }
        scored.append(
            Scored(
                place_id=r.place_id,
                category=r.category,
                score=combine(components),
                distance_m=r.distance_m,
                components=components,
                price_per_person=r.price_per_person,
                n_reviews=r.n_reviews,
                avg_rating=r.avg_rating,
            )
        )
    scored.sort(key=lambda s: (-s.score, s.place_id))  # place_id breaks ties: same input, same output
    return scored[:k]


def format_vnd(amount: int) -> str:
    """Display only: 40000 -> "40.000đ". Same number the budget filter compares, so the card is consistent."""
    return f"{amount:,}".replace(",", ".") + "đ"


def format_distance(distance_m: int) -> str:
    """Straight-line distance, so the text says "khoảng": it is shorter than the real route."""
    if distance_m < 1000:
        return f"{round(distance_m / 50) * 50} m"  # nearest 50 m: 347 -> "350 m"
    return f"{distance_m / 1000:.1f}".replace(".", ",") + " km"  # 2140 -> "2,1 km"


MAX_REASONS = 4


def build_reasons(s: Scored) -> list[str]:
    """Short Vietnamese lines shown on the card, in a fixed order (mood, distance, price, rating).

    A line is left out when its data is missing (no origin, no price, no review).
    """
    reasons: list[str] = []
    sem = s.components.get("semantic")
    if sem is not None and sem >= 0.7:
        reasons.append("✨ Rất hợp với mood của bạn")
    elif sem is not None and sem >= 0.4:
        reasons.append("✨ Khá hợp với mood của bạn")
    if s.distance_m is not None:
        reasons.append(f"📍 Cách khoảng {format_distance(s.distance_m)}")
    if s.price_per_person is not None:
        reasons.append(f"💰 ~ {format_vnd(s.price_per_person)}/người")
    if s.avg_rating is not None and s.n_reviews > 0:
        reasons.append(f"⭐ {s.avg_rating:.1f} ({s.n_reviews} đánh giá)")
    return reasons[:MAX_REASONS]