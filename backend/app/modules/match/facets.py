"""Facet scoring: how well do the REVIEWERS' tags answer what the user asked (pure, no model).

The embedding sees one blurred vector per place. The reviews, however, contain exact answers:
people ticked "Học bài, làm việc", "Date", "Yên tĩnh" ... So for every wish found in the query
(a "facet") we count how many reviews of the place carry a matching tag, and combine the evidence.

    share      = reviews with the tag / (n_reviews + 1)       one review is weak evidence, never 1.0
    evidence   = 1 - prod(1 - weight * share)                 several tags add up, bounded by 1
    penalty    = prod(1 - weight * negative_share)            "Ồn ào" hurts "yên tĩnh"
    facet      = mean over the facets of the query of  evidence * penalty

`None` when the query has no known facet: the component is then dropped from the final score.
Tune the lexicon (`FACETS`) with the tags that really exist in the review form.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from app.modules.match.query_intent import RequiredTag, _rx, fold

SUITABLE, ATMOSPHERE, FACILITIES, FOOD, PROS, CROWD = (
    "suitable_for",
    "atmosphere",
    "facilities",
    "food_types",
    "pros",
    "crowd_level",
)

Signal = tuple[str, str, float]  # (review field, tag casefolded, weight)


@dataclass(frozen=True)
class Facet:
    key: str
    pattern: re.Pattern[str]  # on the folded query
    positive: tuple[Signal, ...]
    negative: tuple[Signal, ...] = ()


FACETS: tuple[Facet, ...] = (
    Facet(
        "study",
        _rx(
            "hoc bai",
            "lam viec",
            "hoc",
            "study",
            "work",
            "deadline",
            "laptop",
            "on thi",
            "workspace",
            "co working",
        ),
        (
            (SUITABLE, "học bài, làm việc", 0.9),
            (FACILITIES, "nhiều ổ điện", 0.35),
            (FACILITIES, "wifi", 0.15),
            (FACILITIES, "có nhiều sách", 0.15),
        ),
        ((ATMOSPHERE, "ồn ào", 0.4),),
    ),
    Facet(
        "quiet",
        _rx("yen tinh", "yen lang", "im lang", "it on", "tinh lang", "khong on", "tap trung", "vang"),
        (
            (ATMOSPHERE, "yên tĩnh", 0.9),
            (PROS, "yên tĩnh", 0.6),
            (CROWD, "vắng", 0.3),
        ),
        (
            (ATMOSPHERE, "ồn ào", 0.7),
            (ATMOSPHERE, "sôi động", 0.5),
            (PROS, "nhộn nhịp", 0.4),
            (CROWD, "đông", 0.25),
        ),
    ),
    Facet(
        "date",
        _rx("date", "hen ho", "lang man", "nguoi yeu", "crush", "cap doi", "romantic", "hai nguoi"),
        (
            (SUITABLE, "date", 0.9),
            (ATMOSPHERE, "ấm cúng", 0.35),
            (ATMOSPHERE, "xinh xắn", 0.25),
            (ATMOSPHERE, "sang trọng", 0.25),
            (ATMOSPHERE, "vintage", 0.2),
            (ATMOSPHERE, "yên tĩnh", 0.2),
        ),
        ((ATMOSPHERE, "ồn ào", 0.6), (ATMOSPHERE, "bí bách", 0.4), (ATMOSPHERE, "bình dân", 0.15)),
    ),
    Facet(
        "group",
        _rx(
            "nhom",
            "dong nguoi",
            "hop nhom",
            "lien hoan",
            "sinh nhat",
            "tu tap",
            "4 nguoi",
            "5 nguoi",
            "6 nguoi",
        ),
        (
            (SUITABLE, "nhóm đông người (4+)", 0.9),
            (SUITABLE, "quán phù hợp nhất cho nhóm 3-4 người", 0.6),
            (SUITABLE, "tổ chức các cuộc họp / sự kiện", 0.5),
            (FACILITIES, "có phòng riêng", 0.4),
        ),
    ),
    Facet(
        "friends",
        _rx("ban be", "gap ban", "di choi", "tam su"),
        ((SUITABLE, "gặp gỡ bạn bè", 0.9), (SUITABLE, "nhóm đông người (4+)", 0.3)),
    ),
    Facet(
        "solo",
        _rx("mot minh", "1 minh", "di mot minh", "solo"),
        ((SUITABLE, "ăn một mình", 0.9), (SUITABLE, "ngồi 1 mình", 0.9)),
    ),
    Facet(
        "family",
        _rx("gia dinh", "bo me", "tre em", "con nho", "ong ba"),
        ((SUITABLE, "ăn cùng gia đình", 0.9), (FACILITIES, "có cho trẻ con tô màu", 0.4)),
    ),
    Facet(
        "quick",
        _rx("an nhanh", "nhanh gon", "nhanh", "nhanh chong"),
        ((SUITABLE, "ăn nhanh", 0.9), (PROS, "ra món nhanh", 0.6)),
    ),
    Facet(
        "relax",
        _rx("thu gian", "chill", "nghi ngoi", "xa stress", "thoai mai"),
        ((SUITABLE, "thư giãn", 0.9), (ATMOSPHERE, "chill, dễ chịu", 0.7)),
    ),
    Facet(
        "photo",
        _rx("chup anh", "song ao", "check in", "view dep", "xinh", "dep"),
        (
            (SUITABLE, "chụp ảnh", 0.9),
            (ATMOSPHERE, "xinh xắn", 0.5),
            (ATMOSPHERE, "nhiều ánh sáng", 0.3),
            (PROS, "không gian đẹp", 0.4),
            (PROS, "trang trí đẹp mắt / bày biện tinh tế", 0.4),
        ),
    ),
    Facet(
        "light",
        _rx("thanh dam", "nhe bung", "healthy", "eat clean", "an nhe", "it dau mo", "lanh manh"),
        ((FOOD, "thanh đạm, nhẹ bụng", 0.9), (FOOD, "chay", 0.5), (PROS, "nguyên liệu tươi, sạch", 0.3)),
        ((FOOD, "nhiều dầu mỡ", 0.6), (FOOD, "đồ chiên rán", 0.5), (FOOD, "ngấy, đầy bụng", 0.5)),
    ),
    Facet(
        "veg",
        _rx("chay", "thuan chay", "vegan", "vegetarian"),
        ((FOOD, "chay", 1.0),),
    ),
    Facet(
        "cheap",
        _rx("gia re", "re", "sinh vien", "binh dan", "tiet kiem", "hat de"),
        (
            (PROS, "giá rẻ", 0.8),
            (PROS, "giá cả vừa phải / giá cả hợp lý", 0.4),
            (ATMOSPHERE, "bình dân", 0.3),
        ),
    ),
    Facet(
        "late",
        _rx("an khuya", "mo khuya", "khuya", "ngoi muon", "dong cua muon"),
        ((SUITABLE, "ăn khuya", 0.9), (FACILITIES, "cho phép ngồi muộn / đóng cửa muộn", 0.9)),
    ),
    Facet(
        "takeaway",
        _rx("mang ve", "take away", "takeaway", "mang di"),
        (
            (SUITABLE, "take away", 0.9),
            (SUITABLE, "quán chỉ có thể mua mang về", 0.9),
            (SUITABLE, "thích hợp mua mang về hơn", 0.9),
        ),
    ),
    Facet(
        "outdoor",
        _rx("ngoai troi", "thoang", "cay xanh", "san vuon", "mat me"),
        (
            (ATMOSPHERE, "ngoài trời", 0.8),
            (ATMOSPHERE, "nhiều cây xanh", 0.7),
            (ATMOSPHERE, "mát mẻ", 0.4),
            (PROS, "không gian thoáng đãng", 0.5),
        ),
    ),
)

_BY_KEY = {f.key: f for f in FACETS}


class ReviewTags(Protocol):
    """Fields of a review read here (a `Review` row or a plain stand-in in tests)."""

    suitable_for: Sequence[str]
    atmosphere: Sequence[str]
    facilities: Sequence[str]
    food_types: Sequence[str]
    pros: Sequence[str]
    crowd_level: str | None


def detect_facets(folded_query: str) -> tuple[str, ...]:
    """Keys of the facets whose words appear in the (already folded) query. Order = lexicon order."""
    return tuple(f.key for f in FACETS if f.pattern.search(folded_query))


def _values(review: ReviewTags, field: str) -> set[str]:
    if field == CROWD:
        raw = review.crowd_level
        folded = fold(raw) if raw else ""
        if folded.startswith("vang"):
            return {"vắng"}
        if folded.startswith(("dong", "phai cho")):
            return {"đông"}
        return set()
    return {t.strip().casefold() for t in getattr(review, field)}


def _share(reviews: Sequence[ReviewTags], field: str, tag: str) -> float:
    hits = sum(1 for r in reviews if tag in _values(r, field))
    return hits / (len(reviews) + 1)


def facet_score(facet: Facet, reviews: Sequence[ReviewTags]) -> float:
    if not reviews:
        return 0.0
    miss = 1.0
    for field, tag, weight in facet.positive:
        miss *= 1 - weight * _share(reviews, field, tag)
    evidence = 1 - miss
    keep = 1.0
    for field, tag, weight in facet.negative:
        keep *= 1 - weight * _share(reviews, field, tag)
    return max(0.0, min(1.0, evidence * keep))


def facets_score(keys: Sequence[str], reviews: Sequence[ReviewTags]) -> float | None:
    """Mean of the facets of the query; None when the query has no facet (component not applied)."""
    chosen = [_BY_KEY[k] for k in keys if k in _BY_KEY]
    if not chosen:
        return None
    return sum(facet_score(f, reviews) for f in chosen) / len(chosen)


def passes_required(required: Sequence[RequiredTag], name: str, reviews: Sequence[ReviewTags]) -> bool:
    """Hard rule: every dietary need must be answered by a review tag or by a word of the name."""
    folded_name = fold(name)
    for need in required:
        in_name = any(re.search(rf"\b{re.escape(w)}\b", folded_name) for w in need.name_words)
        in_tags = any(need.tag in _values(r, FOOD) for r in reviews)
        if not (in_name or in_tags):
            return False
    return True