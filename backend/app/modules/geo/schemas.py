"""geo API contract (Pydantic response models).

`GET /api/geo/resolve` answers with `app.shared.contracts.GeoPoint`, the same shape as
`MatchCriteria.origin`, so the frontend can send the answer straight back as the search origin.
"""

from pydantic import BaseModel, Field


class GeoSuggestionOut(BaseModel):
    """One line of the suggestion list shown under the address field."""

    ref_id: str = Field(description="opaque id: pass it unchanged to `GET /api/geo/resolve`; do not store it")
    name: str = Field(description="short title: a place name, or house number + street")
    address: str = Field(description="ward / district / city, shown under the name; may be empty", default="")
