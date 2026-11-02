"""Pure logic of "Why this place?": choose which pre-written bullets to show. No database, no model.

The bullets ("Không gian yên tĩnh", "Có nhiều ổ điện") are written OFFLINE by the insights job
(`scripts/generate_insights.py`) and stored as `place_highlights`, each with an embedding. When the
user searches, the service encodes the search text, asks PostgreSQL for the similarity to each bullet
of ONE place, and passes the rows here. No LLM runs at request time, so the wording of a bullet is
decided when the job runs (see the prompt in `insights.py`), and the answer is instant and free.

What is shown (DECISIONS D14):
  1. Bullets close enough to what the user typed (similarity >= WHY_MIN_SIMILARITY), best match first.
     They are flagged `matched=True`, so the UI may say "Phù hợp với bạn".
  2. If fewer than MIN_POINTS bullets matched, the place's strongest bullets (most reviews mention
     them) fill the rest, flagged `matched=False`. They are real facts about the place, only not
     tied to the search.
Nothing is invented: a place without bullets gets an empty list, and the UI falls back to the
`reasons` of Match (distance, price, rating).
"""

from collections.abc import Sequence
from dataclasses import dataclass

# MiniLM cosine between a short bullet and the user's sentence: related is typically 0.4-0.7 and
# unrelated 0.0-0.25. Tune with `scripts/try_why.py` on real searches, like SIM_LOW / SIM_HIGH.
WHY_MIN_SIMILARITY = 0.40
MIN_POINTS = 3  # show at least this many bullets when the place has them
MAX_POINTS = 4  # ...and never more than this many


@dataclass(frozen=True)
class Highlight:
    """One stored bullet and its cosine similarity to the user's search text."""

    text: str
    support: int  # how many reviews mention it
    similarity: float


@dataclass(frozen=True)
class WhyPick:
    text: str
    matched: bool  # True = close to what the user typed; False = a general strength of the place


def pick_points(
    highlights: Sequence[Highlight],
    *,
    min_similarity: float = WHY_MIN_SIMILARITY,
    min_points: int = MIN_POINTS,
    max_points: int = MAX_POINTS,
) -> list[WhyPick]:
    """Matched bullets first (best match first), then the strongest others up to `min_points`.

    Deterministic: ties are broken by support and then by text, so the same data always gives the
    same answer.
    """
    matched = sorted(
        (h for h in highlights if h.similarity >= min_similarity),
        key=lambda h: (-h.similarity, -h.support, h.text),
    )[:max_points]
    picks = [WhyPick(h.text, True) for h in matched]

    missing = min_points - len(picks)
    if missing > 0:
        taken = {h.text for h in matched}
        others = sorted(
            (h for h in highlights if h.text not in taken),
            key=lambda h: (-h.support, -h.similarity, h.text),
        )
        picks += [WhyPick(h.text, False) for h in others[:missing]]
    return picks


def join_points(picks: Sequence[WhyPick]) -> str:
    """One line for clients that show text instead of a list ("" when there is nothing to say)."""
    return "; ".join(p.text for p in picks)
