"""Review Analysis: summarise the visible reviews of one place with plain code (no LLM).

Pure functions (no database), so they are unit tested directly. The service loads the reviews and
calls `analyze`.

Both review sources are summarised together: reviews imported from the team's form (rich
structured fields) and reviews written on the website (4 scores, free comment, optional dishes /
suitable_for / price). A field nobody filled in simply gives an empty list, never an error, so the
same code keeps working when an LLM job later fills `pros` / `cons` for website reviews.

A term counts ONCE per review, so one person listing "phở" three times is one mention. Terms are
grouped ignoring case and accents ("Phở bò" == "pho bo"); the most common spelling is displayed.
"""

import unicodedata
from collections import Counter
from collections.abc import Iterable, Sequence
from decimal import ROUND_HALF_UP, Decimal
from statistics import median
from typing import Protocol

from app.modules.reviews.schemas import AspectScores, ReviewAnalysisOut, TermCount

TOP_DISHES = 8
TOP_OTHER = 5


class ReviewLike(Protocol):
    """The attributes of `reviews.models.Review` that the analysis reads."""

    source: str
    score_food: int
    score_space: int
    score_price: int
    score_service: int
    recommended_dishes: list[str]
    pros: list[str]
    cons: list[str]
    suitable_for: list[str]
    atmosphere: list[str]
    crowd_level: str | None
    price_per_person: int | None


def _fold(text: str) -> str:
    """Grouping key: no accents, no case, single spaces ('Phở  Bò' -> 'pho bo')."""
    decomposed = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    stripped = "".join(c for c in decomposed if not unicodedata.combining(c))
    return " ".join(stripped.casefold().split())


def _round1(value: float) -> float:
    """Round half up to 1 decimal (Python's round() would turn 4.25 into 4.2)."""
    return float(Decimal(repr(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


def _mean(values: Sequence[int]) -> float | None:
    return sum(values) / len(values) if values else None


def count_terms(per_review: Iterable[Iterable[str]], n: int) -> list[TermCount]:
    """The n terms mentioned by the most reviews. Ties are broken alphabetically (stable output)."""
    mentions: Counter[str] = Counter()
    spellings: dict[str, Counter[str]] = {}
    for terms in per_review:
        in_this_review: set[str] = set()
        for raw in terms:
            display = " ".join((raw or "").split())
            key = _fold(display)
            if not key or key in in_this_review:
                continue
            in_this_review.add(key)
            mentions[key] += 1
            spellings.setdefault(key, Counter())[display] += 1

    def best_spelling(key: str) -> str:
        # most used spelling; on a tie prefer accents, then alphabetical (capitalised sorts first)
        return min(
            spellings[key].items(),
            key=lambda kv: (-kv[1], not any(ord(c) > 127 for c in kv[0]), kv[0]),
        )[0]

    ranked = sorted(mentions.items(), key=lambda kv: (-kv[1], kv[0]))[:n]
    return [TermCount(name=best_spelling(key), mentions=count) for key, count in ranked]


def analyze(place_id: str, reviews: Sequence[ReviewLike]) -> ReviewAnalysisOut:
    aspect_means = {
        "food": _mean([r.score_food for r in reviews]),
        "space": _mean([r.score_space for r in reviews]),
        "price": _mean([r.score_price for r in reviews]),
        "service": _mean([r.score_service for r in reviews]),
    }
    present = [v for v in aspect_means.values() if v is not None]
    prices = [r.price_per_person for r in reviews if r.price_per_person]
    crowd = count_terms(([r.crowd_level] if r.crowd_level else [] for r in reviews), 1)

    return ReviewAnalysisOut(
        place_id=place_id,
        review_count=len(reviews),
        user_review_count=sum(1 for r in reviews if r.source == "user"),
        sheet_review_count=sum(1 for r in reviews if r.source == "sheet"),
        overall=_round1(sum(present) / len(present)) if present else None,
        aspects=AspectScores(**{k: None if v is None else _round1(v) for k, v in aspect_means.items()}),
        dishes=count_terms((r.recommended_dishes for r in reviews), TOP_DISHES),
        pros=count_terms((r.pros for r in reviews), TOP_OTHER),
        cons=count_terms((r.cons for r in reviews), TOP_OTHER),
        suitable_for=count_terms((r.suitable_for for r in reviews), TOP_OTHER),
        atmosphere=count_terms((r.atmosphere for r in reviews), TOP_OTHER),
        crowd_level=crowd[0].name if crowd else None,
        typical_price=int(median(prices)) if prices else None,
    )
