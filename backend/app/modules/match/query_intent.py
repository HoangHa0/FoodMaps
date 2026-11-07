"""Read the HARD parts of a search sentence (pure, no model, no database).

An embedding is good at vibes ("yên tĩnh", "ấm cúng") but bad at constraints: "quán CÀ PHÊ yên tĩnh"
should never return a bakery, and "quán ăn CHAY" should never return a noodle shop only because it
is "nhẹ bụng". So the constraints are read here with plain rules, and the embedding only ranks
what is left:

    category   "cà phê / trà" -> 'Cà phê & Trà'; exactly one kind detected, otherwise no filter
    required   dietary needs that must be true ("chay"): the place must carry the tag or the word
    facets     soft wishes ("học bài", "date", "yên tĩnh"): scored from the reviews' tags in facets.py

Matching is done on accent-less lower-case text, so "ca phe", "cà phê" and "CÀ PHÊ" are the same.
"""

import re
import unicodedata
from dataclasses import dataclass

CAT_CAFE = "Cà phê & Trà"
CAT_FOOD = "Quán ăn"
CAT_BAKERY = "Tiệm Bánh"
CAT_CHE = "Quán chè"


def fold(text: str) -> str:
    """'Cà Phê  Yên tĩnh' -> 'ca phe yen tinh' (no accents, lower case, single spaces)."""
    t = unicodedata.normalize("NFD", text.replace("đ", "d").replace("Đ", "D"))
    t = "".join(c for c in t if not unicodedata.combining(c)).casefold()
    return " ".join(re.sub(r"[^\w\s+]", " ", t).split())


def _rx(*words: str) -> re.Pattern[str]:
    return re.compile(r"\b(?:" + "|".join(words) + r")\b")


# Category words. Folded text, whole words only. "banh mi / banh cuon" are meals, not bakeries.
_CATEGORY_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (CAT_CAFE, _rx("ca phe", "cafe", "coffee", "cf", "tra sua", "tra chanh", "tra", "do uong", "matcha")),
    (CAT_BAKERY, _rx("tiem banh", "banh ngot", "banh kem", "bakery", "croissant", "donut", "do ngot")),
    (CAT_CHE, _rx("che")),
    (
        CAT_FOOD,
        _rx(
            "quan an", "an trua", "an toi", "an sang", "an khuya", "bua an", "bua trua", "bua toi",
            "com", "pho", "bun", "mien", "lau", "nuong", "mi cay", "an chay", "quan chay", "do an",
        ),
    ),
)  # fmt: skip

# Dietary needs: query pattern -> (label, tag casefolded, words that also count in the place name)
_REQUIRED: tuple[tuple[str, re.Pattern[str], str, tuple[str, ...]], ...] = (
    ("chay", _rx("chay", "thuan chay", "vegan", "vegetarian", "do an chay", "an chay"), "chay", ("chay",)),
)


@dataclass(frozen=True)
class RequiredTag:
    """A dietary need. A place passes if a visible review has the tag OR its name has a word."""

    label: str
    tag: str  # compared with the casefolded food_types of the reviews
    name_words: tuple[str, ...]


@dataclass(frozen=True)
class QueryIntent:
    categories: tuple[str, ...] = ()
    required: tuple[RequiredTag, ...] = ()
    facets: tuple[str, ...] = ()


def parse_query(text: str) -> QueryIntent:
    from app.modules.match.facets import detect_facets  # local import: facets imports `fold` from here

    folded = fold(text)
    found = [cat for cat, rx in _CATEGORY_PATTERNS if rx.search(folded)]
    # Exactly one kind -> filter. Two kinds ("cà phê có đồ ăn") is ambiguous -> no filter.
    categories: tuple[str, ...] = tuple(found) if len(found) == 1 else ()
    required = tuple(RequiredTag(lbl, tag, words) for lbl, rx, tag, words in _REQUIRED if rx.search(folded))
    return QueryIntent(categories=categories, required=required, facets=detect_facets(folded))
