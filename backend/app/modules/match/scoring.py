"""Match Score: pure functions (no database, no model, no FastAPI), easy to unit test.

Final score = weighted average of four components, each in 0..1:

    semantic  how close the place's embedding is to the mood (cosine similarity, calibrated)
    distance  1 at the origin, 0 at the edge of the radius (skipped when there is no origin)
    rating    average of our own reviews, shrunk towards a neutral prior
    budget    1 when the price is inside [price_min, price_max] (skipped when no budget is given).

A component that does not apply (no origin, no budget) is dropped and the remaining weights are
re-normalised, so a search without a location is not punished for it.

The "Not Match" button reuses the same components (see `rerank_after_reject` at the bottom).

All tunable numbers are constants at the top: adjust them after looking at real data
(`scripts/try_match.py` prints the raw cosine values).
"""

import math
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass, field, replace

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

# --- "Not Match" rerank -----------------------------------------------------------------------
# new key = (1 - REJECT_PREFERENCE_WEIGHT) * original score + REJECT_PREFERENCE_WEIGHT * preference.
# 0 would ignore the complaint, 1 would ignore the original score. 0.6 lets the complaint win when
# two places are close, but a clearly better match is not thrown away for a tiny gain.
REJECT_PREFERENCE_WEIGHT = 0.6
NEUTRAL_PREFERENCE = 0.5  # the data needed to judge the complaint is missing: neither good nor bad

REASON_TOO_FAR = "too_far"
REASON_TOO_EXPENSIVE = "too_expensive"
REASON_TOO_CROWDED = "too_crowded"
REASON_WRONG_VIBE = "wrong_vibe"

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
    crowd: float | None = None  # 0 (quiet) .. 1 (packed); only filled for the reject rerank


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
    crowd: float | None = None  # 0 (quiet) .. 1 (packed); None = nobody said


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
                crowd=r.crowd,
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


MAX_REASONS = 3


def build_reasons(s: Scored) -> list[str]:
    """Short Vietnamese lines shown on the card, displaying hard facts only.

    A line is left out when its data is missing (no origin, no price, no review).
    Semantic score is omitted here because the UI already shows it as a "% MATCH" badge.
    """
    reasons: list[str] = []

    if s.distance_m is not None:
        reasons.append(f"📍 Cách khoảng {format_distance(s.distance_m)}")

    if s.price_per_person is not None:
        reasons.append(f"💰 ~ {format_vnd(s.price_per_person)}/người")

    if s.avg_rating is not None and s.n_reviews > 0:
        reasons.append(f"⭐ {s.avg_rating:.1f} ({s.n_reviews} đánh giá)")

    return reasons[:MAX_REASONS]


# --------------------------------------------------------------------------- "Not Match" rerank


def crowd_level_to_number(text: str | None) -> float | None:
    """Turn a review's free-text crowd answer into 0 (quiet) .. 1 (packed).

    Reviews store the answer as text ("Vắng", "Vừa phải", "Đông", ...), so the words are matched
    ignoring case and accents. An answer we do not recognise gives None (unknown), never a guess.
    """
    if not text:
        return None
    folded = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    t = " ".join("".join(c for c in folded if not unicodedata.combining(c)).casefold().split())
    if not t:
        return None
    if any(w in t for w in ("vang", "khong dong", "it nguoi", "thoang", "yen tinh")):
        return 0.0
    if any(w in t for w in ("rat dong", "qua dong", "kin cho", "phai cho", "dong nghit")):
        return 1.0
    if any(w in t for w in ("vua", "binh thuong", "trung binh")):
        return 0.5
    if "dong" in t:
        return 0.8
    return None


def mean_crowd(levels: Sequence[str | None]) -> float | None:
    """Average crowd of a place over the reviews that said something recognisable."""
    numbers = [n for level in levels if (n := crowd_level_to_number(level)) is not None]
    return sum(numbers) / len(numbers) if numbers else None


def _cheapness(candidates: Sequence[Scored]) -> dict[str, float]:
    """1 for the cheapest place of the group, 0 for the dearest, relative to the group itself.

    Only the order matters here (nothing is shown as a percentage), so a relative scale is fine.
    A place with an unknown price, or a group where every price is equal, stays neutral.
    """
    prices = [c.price_per_person for c in candidates if c.price_per_person is not None]
    low, high = (min(prices), max(prices)) if prices else (0, 0)
    out: dict[str, float] = {}
    for c in candidates:
        if c.price_per_person is None or high == low:
            out[c.place_id] = NEUTRAL_PREFERENCE
        else:
            out[c.place_id] = (high - c.price_per_person) / (high - low)
    return out


def rerank_after_reject(
    candidates: Sequence[Scored],
    reason: str,
    *,
    rejected_place_id: str | None = None,
) -> list[Scored]:
    """Reorder the remaining backups after the user pressed "Not Match" (pure, deterministic).

    The rejected place is removed. Every other place keeps its original `score`, which is still
    what the card shows as "% MATCH" (the mood did not change); only the ORDER changes:

        too_far        prefer the closer place        (distance component; neutral without origin)
        too_expensive  prefer the cheaper place       (relative to the other backups)
        too_crowded    prefer the quieter place       (from the reviews' crowd answers)
        wrong_vibe     prefer the better mood match   (semantic component)

    An unknown reason keeps the original order. Ties are broken by `place_id`.
    """
    pool = [c for c in candidates if c.place_id != rejected_place_id]
    cheap = _cheapness(pool) if reason == REASON_TOO_EXPENSIVE else {}

    def preference(c: Scored) -> float:
        if reason == REASON_TOO_FAR:
            value = c.components.get("distance")
        elif reason == REASON_TOO_EXPENSIVE:
            value = cheap[c.place_id]
        elif reason == REASON_TOO_CROWDED:
            value = None if c.crowd is None else 1.0 - c.crowd
        elif reason == REASON_WRONG_VIBE:
            value = c.components.get("semantic")
        else:
            return NEUTRAL_PREFERENCE
        return NEUTRAL_PREFERENCE if value is None else clamp01(value)

    w = REJECT_PREFERENCE_WEIGHT
    return sorted(pool, key=lambda c: (-((1 - w) * c.score + w * preference(c)), c.place_id))


def with_crowd(candidates: Sequence[Scored], crowd_by_place: dict[str, float | None]) -> list[Scored]:
    """Attach the crowd number to already-scored places (it is only needed for the reject rerank)."""
    return [replace(c, crowd=crowd_by_place.get(c.place_id)) for c in candidates]
