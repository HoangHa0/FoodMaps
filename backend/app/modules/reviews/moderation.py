"""Basic text filter for reviews: profanity, links, phone numbers, keyboard-mashing.

Pure functions (no database), so they are easy to unit test. A hit does NOT delete or reject the
review: the service stores it with `status = 'flagged'`, which hides it from other users, from
Match ranking and from the embeddings, while the author still sees it. A false positive is
therefore cheap (an admin can set the status back to `visible`), so the filter prefers catching
spam over perfect precision, but it avoids words that are common in everyday Vietnamese.

Matching rules
- Text is Unicode-normalised (NFC) and lower-cased; repeated letters are collapsed first, so
  "địttttt" is caught.
- Words are matched on word boundaries: "đụ" does not match "đụng", "đĩ" does not match "đĩa".
- Vietnamese profanity is matched WITH diacritics. Accent-stripped forms are only matched for
  forms that are not ordinary words ("dit me", "dmm", "vcl"): "deo", "lon", "cac" are also normal
  words ("đeo", "lon" = can, "các"), so they are not on the list.
"""

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

# --- profanity -----------------------------------------------------------------------------
# Each entry is a regex fragment; the whole alternation is wrapped in word boundaries below.
_PROFANITY_WORDS = (
    r"địt",
    r"đụ",
    r"đéo",
    r"lồn",
    r"cặc",
    r"buồi",
    r"đĩ",
    r"cứt",
    r"đm",
    r"đmm",
    r"đcm",
    r"đjt",
    r"đ[.\-_*]m",  # "đ.m", "đ-m", "đ*m"
    r"dm",
    r"dmm",
    r"dcm",
    r"vcl",
    r"vkl",
    r"clgt",
    r"dit\s+(?:con\s+)?me",  # accent-stripped "địt (con) mẹ"
    r"fuck\w*",  # also "fucking", "fucked"
    r"shit\w*",
    r"bitch\w*",
)
_PROFANITY = re.compile(r"(?<!\w)(?:" + "|".join(_PROFANITY_WORDS) + r")(?!\w)")

# --- spam signals --------------------------------------------------------------------------
_TLDS = r"com|vn|net|org|info|xyz|me|io|co|shop|top|site|online|store|biz|ly|gl"
_LINK = re.compile(
    r"https?://|www\.|(?<![\w.])[a-z0-9][a-z0-9\-]*\.(?:" + _TLDS + r")(?:/|(?![\w]))",
)
# Vietnamese mobile number: 0xx / +84xx / 84xx followed by 8 more digits, with optional separators.
_PHONE = re.compile(r"(?<!\d)(?:\+?84|0)[\s.\-]?[35789]\d(?:[\s.\-]?\d){7}(?!\d)")
_CHAR_RUN = re.compile(r"(\w)\1{9,}")  # the same letter/digit 10+ times in a row
_WORD_RUN = re.compile(r"(?<!\w)(\w+)(?:\s+\1(?!\w)){5,}")  # the same word 6+ times in a row
_LETTER_STRETCH = re.compile(r"(\w)\1{2,}")  # "địttttt" -> "địt"


@dataclass(frozen=True)
class ModerationResult:
    flagged: bool
    reasons: tuple[str, ...] = ()


def _normalize(text: str) -> str:
    return unicodedata.normalize("NFC", text).casefold()


def check_text(text: str | None) -> tuple[str, ...]:
    """Reasons (subset of profanity/link/phone/repeated) why this one text looks bad; () if clean."""
    if not text or not text.strip():
        return ()
    norm = _normalize(text)
    reasons: list[str] = []
    if _PROFANITY.search(_LETTER_STRETCH.sub(r"\1", norm)):
        reasons.append("profanity")
    if _LINK.search(norm):
        reasons.append("link")
    if _PHONE.search(norm):
        reasons.append("phone")
    if _CHAR_RUN.search(norm) or _WORD_RUN.search(norm):
        reasons.append("repeated")
    return tuple(reasons)


def check_texts(texts: Iterable[str | None]) -> ModerationResult:
    """Check every free-text field of a review (comment, dishes, tags) and merge the reasons."""
    reasons: list[str] = []
    for text in texts:
        for reason in check_text(text):
            if reason not in reasons:
                reasons.append(reason)
    return ModerationResult(flagged=bool(reasons), reasons=tuple(reasons))
