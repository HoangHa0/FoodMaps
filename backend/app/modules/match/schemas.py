"""match API contract (Pydantic request/response models).

The frontend types are generated from these models (`make api-types`), so a change here is the
contract change that Person C sees.
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from app.shared.contracts import MatchCriteria, PlaceCandidate


class MatchResult(PlaceCandidate):
    """A candidate plus the short reasons behind its score.

    Inherited from PlaceCandidate: place_id, match_score (0..1, show it as round(score * 100) %),
    tags (3-4 short tags), distance_m (straight-line metres, None when the request has no origin).
    """

    name: str | None = Field(
        default=None,
        description="the team's own name for the place (`places.manual_name`), not Google data: show it "
        "on the result card. The live Google name, photo and rating come from M7 with attribution",
    )
    price_per_person: int | None = Field(
        default=None, description="estimated VND per person (median of the reviews); null if unknown"
    )
    avg_rating: float | None = Field(
        default=None,
        description="mean of our own reviews (sheet + web), 1..5; null when the place has no review",
    )
    review_count: int = Field(default=0, description="number of visible reviews behind avg_rating")
    reasons: list[str] = Field(
        default_factory=list,
        description="up to 4 ready-to-show Vietnamese lines (mood, distance, price, rating); a line is "
        "omitted when its data is missing. distance_m is straight-line: show it with a '~' or 'khoảng'",
    )


class MatchResponse(BaseModel):
    best: MatchResult | None = Field(description="null when nothing matches the criteria")
    backups: list[MatchResult] = Field(
        default_factory=list,
        description="up to 3 fallback places, best first; used by the 'Không hợp' button",
    )


class RejectReason(StrEnum):
    too_far = "too_far"
    too_expensive = "too_expensive"
    too_crowded = "too_crowded"
    wrong_vibe = "wrong_vibe"


class RejectIn(BaseModel):
    """'Không hợp': the client keeps the backup list, so the server stays stateless."""

    criteria: MatchCriteria
    reason: RejectReason
    rejected_place_id: str
    remaining: list[str] = Field(
        max_length=10, description="place_ids of the backups still available (client-side list)"
    )


class WhyPoint(BaseModel):
    text: str = Field(description="one short Vietnamese bullet taken from the place's reviews")
    matched: bool = Field(
        description="true when the bullet is close to what the user typed; false when it is one of the "
        "place's general strengths shown to fill the list"
    )


class WhyOut(BaseModel):
    """'Why this place?'. Bullets written offline from the reviews and picked by similarity to the
    search text: no LLM runs here, so the answer is instant.

    Show `points` as a list (a "Khớp với bạn" label may be used for `matched` ones) and put the
    `reasons` of the Match result (distance, price, rating) next to them. `points` is empty when the
    place has no insights yet: show the Match `reasons` only.
    """

    place_id: str
    why: str = Field(description="the `points` joined into one line; empty when there are none")
    points: list[WhyPoint] = Field(default_factory=list, description="3-4 bullets, matched ones first")


class FaqItem(BaseModel):
    key: str = Field(description="preset key, e.g. 'date', 'study', 'budget'")
    question: str = Field(description="the preset question, ready to show: 'Có hợp đi date không?'")
    answer: str = Field(description="the answer written from the reviews, ready to show")


class DishCount(BaseModel):
    name: str
    mentions: int = Field(description="number of reviews that recommend the dish")


class InsightsOut(BaseModel):
    """What the offline job (`scripts/generate_insights.py`) wrote about one place: ready to show,
    read from the database, no LLM runs when this is requested."""

    place_id: str
    summary: str | None = Field(
        description="AI summary written from website reviews only; null while the place has none"
    )
    pros: list[str] = Field(description="up to 5 short points that reviewers praise")
    cons: list[str] = Field(description="up to 5 short points reviewers complain about; empty if none")
    faq: list[FaqItem] = Field(
        description="only the preset questions the reviews can answer, always in the same order; "
        "an unanswered question is left out, never answered with a guess"
    )
    top_dishes: list[DishCount] = Field(description="most mentioned dishes, most mentioned first")
    generated_at: datetime = Field(description="when the insights were last generated")
