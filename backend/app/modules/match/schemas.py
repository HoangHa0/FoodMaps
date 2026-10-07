"""match API contract (Pydantic request/response models).

The frontend types are generated from these models (`make api-types`), so a change here is the
contract change that Person C sees.
"""

from enum import StrEnum

from pydantic import BaseModel, Field

from app.shared.contracts import MatchCriteria, PlaceCandidate


class MatchResult(PlaceCandidate):
    """A candidate plus the short reasons behind its score.

    Inherited from PlaceCandidate: place_id, match_score (0..1, show it as round(score * 100) %),
    tags (3-4 short tags), distance_m (straight-line metres, None when the request has no origin).
    """

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


class WhyOut(BaseModel):
    """'Why this place?'. Separate endpoint because the LLM call is slow."""

    place_id: str
    why: str
