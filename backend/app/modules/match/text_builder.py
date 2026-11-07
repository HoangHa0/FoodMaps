"""Build the text that describes one place for semantic search.

Pure functions (no database, no model), so they are easy to unit test. Used by
`scripts/compute_embeddings.py`. The text only contains data we own: our own reviews (Google Form
sheet + website users).

Rules that keep the vectors honest (see DECISIONS):
- NEGATIVE data ("Điểm trừ") is NOT embedded. A sentence embedding cannot read "Điểm trừ: Không gian
  nhỏ" as a complaint, so a cramped place ended up matching "không gian nhỏ, ấm cúng" for a date.
  Cons are handled elsewhere (facet penalties in `facets.py`, the insights tab).
- Rare tags are expanded with plain synonyms ("Chay" -> "quán chay, món chay, ăn chay"), because the
  model barely knows a one-word tag.
- The text is capped near the model's real window (256 tokens ~ 900 chars). Everything after that
  is silently cut by the encoder, so a long text only made places with long comments look different.
"""

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from datetime import datetime
from typing import Protocol

from app.modules.match.query_intent import fold

MAX_COMMENTS = 4
COMMENT_CHARS = 120  # per comment; the first sentence(s) carry the signal
MAX_CHARS = 900

# Synonyms added next to a tag. Only true equivalents: never add a quality the reviewers did not say.
TAG_EXPANSIONS: dict[str, str] = {
    "chay": "quán chay, món chay, đồ chay thuần thực vật",
    "thanh đạm, nhẹ bụng": "ăn nhẹ, healthy, ít dầu mỡ",
    "học bài, làm việc": "ngồi học, study, workspace",
    "date": "đi date, hẹn hò, cặp đôi",
    "yên tĩnh": "yên lặng, ít ồn, tập trung",
    "ấm cúng": "cozy, thân mật",
    "nhóm đông người (4+)": "họp nhóm, tụ tập",
    "chụp ảnh": "sống ảo, check-in",
    "ăn nhanh": "bữa trưa nhanh gọn",
    "nhiều ổ điện": "cắm laptop, sạc pin",
    "ăn một mình": "đi một mình",
    "ăn cùng gia đình": "đi với bố mẹ",
}

# What the reviewers ticked as "loại hình" -> a plain phrase.
REVIEW_CATEGORY_PHRASES: dict[str, str] = {
    "cà phê / trà / đồ uống": "quán cà phê, trà, đồ uống",
    "tiệm bánh / đồ ngọt": "tiệm bánh, đồ ngọt",
    "quán ăn bình dân": "quán ăn bình dân",
    "nhà hàng": "nhà hàng",
    "ăn vặt": "ăn vặt",
    "chỗ học tập": "chỗ học tập, không gian học tập",
    "quán học tập": "chỗ học tập, không gian học tập",
}

CATEGORY_PHRASES: dict[str, str] = {
    "cà phê & trà": "quán cà phê, trà, đồ uống",
    "quán ăn": "quán ăn",
    "tiệm bánh": "tiệm bánh, đồ ngọt",
    "quán chè": "quán chè",
}


class ReviewLike(Protocol):
    """The attributes of `reviews.models.Review` that the text uses.

    `categories` and `facilities` are optional (read with getattr) so older callers keep working.
    `cons` stays in the protocol only for compatibility: it is deliberately not used.
    """

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


def _expand(values: list[str]) -> list[str]:
    """Add the synonym phrase after a tag that has one ('Chay' -> 'Chay (quán chay, món chay, ...)')."""
    out: list[str] = []
    for v in values:
        extra = TAG_EXPANSIONS.get(v.strip().casefold())
        out.append(f"{v} ({extra})" if extra else v)
    return out


def _short(comment: str) -> str:
    one_line = " ".join(comment.split())
    if len(one_line) <= COMMENT_CHARS:
        return one_line
    cut = one_line[:COMMENT_CHARS]
    last_stop = max(cut.rfind(". "), cut.rfind("; "), cut.rfind(", "))
    return (cut[:last_stop] if last_stop > COMMENT_CHARS // 2 else cut.rstrip()) + "."


# ---- which comments go into the text ---------------------------------------------------------------
# Same idea as the "most relevant" sort of Google Maps / Yelp, kept to a few plain rules:
# drop junk, drop empty praise, keep one comment per author, drop near duplicates, then prefer
# comments that say something concrete and are recent. Length alone never wins.
MIN_COMMENT_CHARS = 15
MIN_CONTENT_WORDS = 3  # words that are not generic praise; "ngon tuyệt vời 10 điểm" has none
DUPLICATE_OVERLAP = 0.6  # word overlap (Jaccard) from which two comments count as the same

# Words that carry no information about WHAT the place is like (folded, no accents).
_GENERIC_WORDS = frozenset(
    "ngon tuyet voi dep qua rat nhat dinh chat xin so tot hay ok oke diem quan an uong nen thu "
    "recommend dang gia tien phuc vu moi nguoi ghe di la va co the cho minh toi mot nay nha "
    "cuc pham sieu lam that su khong chi cung nua roi nhe nha nhieu hon thi ma duoc cac nhung "
    "cua cho voi tai khi neu nen can han chac chan nhat dinh".split()
)
_JUNK = re.compile(
    r"(https?://|www\.|\b\d{9,11}\b|\b(zalo|inbox|ib|sdt|hotline|follow|fanpage)\b|(.)\3{4,})",
    re.IGNORECASE,
)


def _content_words(text: str) -> set[str]:
    return {w for w in fold(text).split() if len(w) >= 3 and not w.isdigit() and w not in _GENERIC_WORDS}


def _usable(text: str) -> bool:
    if len(text) < MIN_COMMENT_CHARS or _JUNK.search(text):
        return False
    letters = [c for c in text if c.isalpha()]
    if len(letters) < MIN_COMMENT_CHARS * 0.6:
        return False
    if sum(c.isupper() for c in letters) / len(letters) > 0.6:  # SHOUTING / pasted ad
        return False
    return len(_content_words(text)) >= MIN_CONTENT_WORDS


MIN_REVIEW_SCORE = 3.5  # mean of the 4 scores; below it the comment is most likely a complaint


def _mean_score(review: object) -> float | None:
    scores = [getattr(review, f, None) for f in ("score_food", "score_space", "score_price", "score_service")]
    known = [x for x in scores if isinstance(x, int | float)]
    return sum(known) / len(known) if known else None


def pick_comments(reviews: Sequence[ReviewLike], n: int) -> list[str]:
    """Up to n comments that describe the place best. Works with or without `created_at`/`user_id`."""
    candidates: list[tuple[str, set[str], object, datetime | None]] = []
    for idx, r in enumerate(reviews):
        text = " ".join((r.comment or "").split())
        mean = _mean_score(r)
        if mean is not None and mean < MIN_REVIEW_SCORE:
            continue  # the complaint stays visible in the reviews and the insights tab, not in the vector
        if text and _usable(text):
            author = getattr(r, "user_id", None) or f"anonymous-{idx}"  # sheet rows have no author
            candidates.append((text, _content_words(text), author, getattr(r, "created_at", None)))
    if not candidates:
        return []

    dated = sorted(c[3] for c in candidates if c[3] is not None)
    newest_rank = {d: i / max(len(dated) - 1, 1) for i, d in enumerate(dated)}  # 0 oldest .. 1 newest

    def score(c: tuple[str, set[str], object, datetime | None]) -> float:
        specific = min(len(c[1]), 25) / 25  # concrete words, capped so a long rant cannot win
        recent = newest_rank.get(c[3], 0.5) if c[3] is not None else 0.5
        return 0.6 * specific + 0.4 * recent

    chosen: list[tuple[str, set[str], object, datetime | None]] = []
    seen_authors: set[object] = set()
    for c in sorted(candidates, key=lambda c: (-score(c), c[0])):
        if c[2] in seen_authors:
            continue  # one comment per account: stops a seeded batch from filling the slots
        if any(len(c[1] & o[1]) / len(c[1] | o[1]) >= DUPLICATE_OVERLAP for o in chosen):
            continue
        chosen.append(c)
        seen_authors.add(c[2])
        if len(chosen) == n:
            break
    return [c[0] for c in chosen]


def build_place_text(
    name: str,
    category: str,
    reviews: Sequence[ReviewLike],
) -> str:
    """Short structured tags FIRST, long free text LAST: if the model truncates, tags survive."""
    n_tags = 4
    phrase = CATEGORY_PHRASES.get(category.strip().casefold(), category)
    parts = [f"{name} là {phrase}."]

    def add(label: str, values: list[str], expand: bool = False) -> None:
        if values:
            parts.append(f"{label}: {', '.join(_expand(values) if expand else values)}.")

    kinds = top_values((t for r in reviews for t in getattr(r, "categories", [])), 2)
    kind_phrases = [REVIEW_CATEGORY_PHRASES.get(k.casefold(), k) for k in kinds]
    add("Loại hình", [k for k in kind_phrases if k.casefold() not in phrase.casefold()])
    add("Phù hợp", top_values((t for r in reviews for t in r.suitable_for), n_tags), expand=True)
    add("Không khí", top_values((t for r in reviews for t in r.atmosphere), n_tags), expand=True)
    add("Tiện ích", top_values((t for r in reviews for t in getattr(r, "facilities", [])), 3), expand=True)
    add("Loại món", top_values((t for r in reviews for t in r.food_types), n_tags), expand=True)
    add("Món nên thử", top_values((t for r in reviews for t in r.recommended_dishes), n_tags))
    add("Điểm cộng", top_values((t for r in reviews for t in r.pros), n_tags))
    # No "Điểm trừ" here on purpose (see module docstring).

    comments = pick_comments(reviews, MAX_COMMENTS)
    if comments:
        parts.append("Nhận xét: " + " ".join(_short(c) for c in comments))

    return " ".join(parts)[:MAX_CHARS]
