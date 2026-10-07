"""reviews API contract (Pydantic request/response models).

The frontend types are generated from these models (`make api-types`), so a change here is a
contract change that the other members see.
"""

import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

Score = Annotated[int, Field(ge=1, le=5)]
# Whitespace is stripped BEFORE the length check, so "   " is rejected instead of stored.
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
ReviewStatus = Literal["visible", "flagged", "hidden"]
ReportReason = Literal["spam", "offensive", "wrong_place", "other"]

MAX_TAGS = 8


def _dedupe(values: list[str]) -> list[str]:
    """Keep the first spelling of each value, ignoring case ('Phở bò' == 'phở bò')."""
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        key = v.casefold()
        if key not in seen:
            seen.add(key)
            out.append(v)
    return out


class ReviewBody(BaseModel):
    """What the author can write (and later change). `place_id` is fixed once the review exists."""

    score_food: Score
    score_space: Score
    score_price: Score
    score_service: Score
    comment: Annotated[str, StringConstraints(strip_whitespace=True, max_length=1000)] | None = Field(
        default=None, description="free text; an empty string is stored as null"
    )
    recommended_dishes: list[Tag] = Field(
        default_factory=list, max_length=MAX_TAGS, description="optional: dishes worth trying"
    )
    suitable_for: list[Tag] = Field(
        default_factory=list, max_length=MAX_TAGS, description="optional: 'date', 'học bài', 'đi nhóm'..."
    )
    price_per_person: int | None = Field(
        default=None, ge=1_000, le=5_000_000, description="optional: VND spent per person"
    )

    @field_validator("comment")
    @classmethod
    def _empty_comment_is_none(cls, v: str | None) -> str | None:
        return v or None

    @field_validator("recommended_dishes", "suitable_for")
    @classmethod
    def _no_duplicate_tags(cls, v: list[str]) -> list[str]:
        return _dedupe(v)


class ReviewIn(ReviewBody):
    place_id: str = Field(min_length=1, max_length=255)


class ReviewUpdateIn(ReviewBody):
    """PUT replaces every editable field, so the form can send the whole object back."""


class ReviewOut(BaseModel):
    id: uuid.UUID
    place_id: str
    author: str | None = Field(description="username; null for reviews imported from the team's form")
    source: Literal["user", "sheet"]
    score_food: int
    score_space: int
    score_price: int
    score_service: int
    comment: str | None
    recommended_dishes: list[str]
    suitable_for: list[str]
    price_per_person: int | None
    status: ReviewStatus = Field(
        description="other people only ever see 'visible'; the author may also see 'flagged'"
    )
    is_mine: bool = Field(description="true when the caller wrote it: show the edit/delete buttons")
    created_at: datetime
    updated_at: datetime


class ReviewListOut(BaseModel):
    items: list[ReviewOut]
    total: int = Field(description="number of visible reviews of the place (for paging)")
    limit: int
    offset: int


class ReportIn(BaseModel):
    reason: ReportReason
    note: Annotated[str, StringConstraints(strip_whitespace=True, max_length=300)] | None = None

    @field_validator("note")
    @classmethod
    def _empty_note_is_none(cls, v: str | None) -> str | None:
        return v or None


class ReportOut(BaseModel):
    review_id: uuid.UUID
    reason: ReportReason
    created_at: datetime


# --------------------------------------------------------------------------- review analysis


class TermCount(BaseModel):
    name: str
    mentions: int = Field(description="how many reviews mention it")


class AspectScores(BaseModel):
    """Average of 1..5 scores per aspect, rounded to 1 decimal; null when there is no review."""

    food: float | None
    space: float | None
    price: float | None
    service: float | None


class ReviewAnalysisOut(BaseModel):
    """Summary of the visible reviews of one place, computed with plain code (no LLM)."""

    place_id: str
    review_count: int
    user_review_count: int = Field(description="reviews written on the website")
    sheet_review_count: int = Field(description="reviews imported from the team's form")
    overall: float | None = Field(description="mean of the four aspect averages, 1 decimal")
    aspects: AspectScores
    dishes: list[TermCount] = Field(description="most mentioned recommended dishes")
    pros: list[TermCount]
    cons: list[TermCount]
    suitable_for: list[TermCount]
    atmosphere: list[TermCount]
    crowd_level: str | None = Field(description="most common answer, null when nobody said")
    typical_price: int | None = Field(description="median VND per person, null when nobody said")
