"""Match Score: 

Final score = weighted average of four components, each in 0..1:

    semantic  how close the place's embedding is to the mood (cosine similarity, calibrated)
    distance  1 at the origin, 0 at the edge of the radius (skipped when there is no origin)
    rating    average of our own reviews, shrunk towards a neutral prior 
    budget    1 inside [price_min, price_max], decays outside it (skipped when no budget is given)

A component that does not apply (no origin, no budget) is dropped and the remaining weights are
re-normalised, so a search without a location is not punished for it.

All tunable numbers are constants at the top: adjust them after looking at real data
(`scripts/try_match.py` prints the raw cosine values).
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, field

# --- weights (relative; they are re-normalised) -----------------------------------------------
W_SEMANTIC = 0.55
W_DISTANCE = 0.20
W_RATING = 0.15
W_BUDGET = 0.10

# --- semantic calibration ---------------------------------------------------------------------
# paraphrase-multilingual-MiniLM cosine for a relevant place is typically 0.2-0.6, so it cannot be
# shown as a percentage directly. Values <= SIM_LOW map to 0 and >= SIM_HIGH map to 1.
SIM_LOW = 0.15
SIM_HIGH = 0.60

# --- rating -----------------------------------------------------------------------------------
RATING_PRIOR = 3.5  # average score (1..5) assumed for a place with no reviews
RATING_PRIOR_WEIGHT = 1  # how many "virtual reviews" the prior counts for

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
    """Hard filter. Lọc cứng không cho phép vượt. Quán không có giá được giữ lại."""
    if price is None:
        return True
    if price_max is not None and price > price_max:
        return False
    if price_min is not None and price < price_min:
        return False
    return True


def budget_score(price: int | None, price_min: int | None, price_max: int | None) -> float | None:
    """None = no budget given. 1.0 = meets budget. 0.5 = unknown price."""
    if price_min is None and price_max is None:
        return None
    if price is None:
        return BUDGET_UNKNOWN_SCORE

    return 1.0


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
            )
        )
    scored.sort(key=lambda s: (-s.score, s.place_id))  
    return scored[:k]


def build_reasons(s: Scored, price_given: bool) -> list[str]:
    """Short Vietnamese reasons shown under the badge. At most 3, strongest signals first."""
    reasons: list[str] = []
    sem = s.components.get("semantic")
    if sem is not None and sem >= 0.7:
        reasons.append("Rất hợp với mood của bạn")
    elif sem is not None and sem >= 0.4:
        reasons.append("Khá hợp với mood của bạn")
    if s.distance_m is not None:
        d = s.distance_m
        reasons.append(f"Cách bạn {d} m" if d < 1000 else f"Cách bạn {d / 1000:.1f} km")
    bud = s.components.get("budget")
    if price_given and bud == 1.0:
        reasons.append("Đúng ngân sách")
    rating = s.components.get("rating")
    if s.n_reviews >= 2 and rating is not None and rating >= 0.75:
        reasons.append("Được review đánh giá cao")
    return reasons[:3]