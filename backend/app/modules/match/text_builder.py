"""Build the text that describes one place for semantic search.

Pure functions (no database, no model), so they are easy to unit test. Used by
`scripts/compute_embeddings.py`. The text only contains data we own: our own reviews (Google Form
sheet + website users).
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from typing import Protocol

MAX_COMMENTS = 8
MAX_CHARS = 2000


class ReviewLike(Protocol):
    """The attributes of `reviews.models.Review` that the text uses."""

    suitable_for: list[str]
    atmosphere: list[str]
    food_types: list[str]
    recommended_dishes: list[str]
    pros: list[str]
    cons: list[str]
    comment: str | None


def top_values(items: Iterable[str], n: int) -> list[str]:
    """The n most frequent values, ignoring case and surrounding spaces ('Trà chanh' == 'trà chanh ')."""
    counts: Counter[str] = Counter()
    first_seen: dict[str, str] = {}
    for raw in items:
        value = (raw or "").strip()
        if not value:
            continue
        key = value.casefold()
        first_seen.setdefault(key, value)
        counts[key] += 1
    return [first_seen[key] for key, _ in counts.most_common(n)]


def build_place_text(
    name: str,
    category: str,
    reviews: Sequence[ReviewLike],
) -> str:
    """Short structured tags FIRST, long free text LAST: if the model truncates, tags survive."""
    parts = [f"{name} ({category})."]

    def add(label: str, values: list[str]) -> None:
        if values:
            parts.append(f"{label}: {', '.join(values)}.")

    add("Phù hợp", top_values((t for r in reviews for t in r.suitable_for), 5))
    add("Không khí", top_values((t for r in reviews for t in r.atmosphere), 5))
    add("Loại món", top_values((t for r in reviews for t in r.food_types), 5))
    add("Món nên thử", top_values((t for r in reviews for t in r.recommended_dishes), 5))
    add("Điểm cộng", top_values((t for r in reviews for t in r.pros), 5))
    add("Điểm trừ", top_values((t for r in reviews for t in r.cons), 3))

    comments = sorted(
        {c.strip() for r in reviews if (c := r.comment) and c.strip()}, key=lambda c: (-len(c), c)
    )
    if comments:
        parts.append("Nhận xét: " + " ".join(comments[:MAX_COMMENTS]))

    return " ".join(parts)[:MAX_CHARS]
