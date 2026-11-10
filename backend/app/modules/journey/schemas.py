"""M6 API contract: what the Food Journey endpoints accept and return.

`JourneyIn` is the body of "save journey" (POST/PUT /journeys); `ShareIn` is the body of "create
share link" (POST /journeys/shares). Both carry the WHOLE journey, so every save overwrites it.
Extra fields in a body are ignored. Limits come from `constants.py`.
"""

import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.modules.journey.constants import MAX_STOPS_PER_JOURNEY, NOTE_MAX_LENGTH, TITLE_MAX_LENGTH
from app.modules.journey.rules import clean_text


# --- input -----------------------------------------------------------------------------------
class StopIn(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    planned_time: time | None = Field(default=None, description="HH:MM, no time zone")
    note: str | None = Field(default=None, max_length=NOTE_MAX_LENGTH)

    @field_validator("planned_time")
    @classmethod
    def _minutes_only(cls, value: time | None) -> time | None:
        if value is None:
            return None
        if value.tzinfo is not None:
            raise ValueError("giờ không có múi giờ")
        return value.replace(second=0, microsecond=0)

    @field_validator("note")
    @classmethod
    def _clean_note(cls, value: str | None) -> str | None:
        return clean_text(value)


class JourneyIn(BaseModel):
    """A whole journey. The order of `stops` is the order shown; the server numbers it 1..n."""

    title: str | None = Field(default=None, max_length=TITLE_MAX_LENGTH)
    planned_date: date | None = None
    stops: list[StopIn] = Field(default_factory=list, max_length=MAX_STOPS_PER_JOURNEY)

    @field_validator("title")
    @classmethod
    def _clean_title(cls, value: str | None) -> str | None:
        return clean_text(value)


class ShareIn(JourneyIn):
    """Same body, but a link to an empty journey is pointless, so at least one stop is required."""

    stops: list[StopIn] = Field(min_length=1, max_length=MAX_STOPS_PER_JOURNEY)


# --- output ----------------------------------------------------------------------------------
class PlaceOut(BaseModel):
    """The part of a place that a journey screen needs. Read from `places`, never stored here."""

    model_config = ConfigDict(from_attributes=True)

    place_id: str
    name: str
    category: str
    address: str | None = None
    lat: float
    lng: float
    google_maps_url: str | None = None
    price_per_person: int | None = Field(default=None, description="VND")


class StopOut(BaseModel):
    id: uuid.UUID
    stop_order: int = Field(ge=1)
    planned_time: time | None = None
    note: str | None = None
    place: PlaceOut


class JourneyOut(BaseModel):
    id: uuid.UUID
    title: str | None = None
    planned_date: date | None = None
    created_at: datetime
    updated_at: datetime
    stops: list[StopOut]


class JourneySummaryOut(BaseModel):
    """One row of the library list."""

    id: uuid.UUID
    title: str | None = None
    planned_date: date | None = None
    updated_at: datetime
    stop_count: int = Field(ge=0)


class ShareCreatedOut(BaseModel):
    code: str
    expires_at: datetime


class SharedStopOut(BaseModel):
    """A stop of a share link. It has no `id`: the snapshot is not made of database rows."""

    stop_order: int = Field(ge=1)
    planned_time: time | None = None
    note: str | None = None
    place: PlaceOut


class SharedJourneyOut(BaseModel):
    """What anyone holding the link sees. Nothing about the account that created it."""

    title: str | None = None
    planned_date: date | None = None
    expires_at: datetime
    stops: list[SharedStopOut]
    missing_places: int = Field(
        default=0, ge=0, description="stops dropped because the place no longer exists"
    )
