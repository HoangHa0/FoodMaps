"""saved_places API contract (Pydantic request/response models)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SavedListOut(BaseModel):
    id: uuid.UUID
    name: str
    icon: str = Field(description="an emoji, also used as the pin icon of the places in this list")
    position: int
    is_default: bool = Field(description="the 'Yêu thích' list: can be renamed but not deleted")
    place_count: int


class SavedListIn(BaseModel):
    name: str = Field(min_length=1, max_length=30)
    icon: str = Field(min_length=1, max_length=16)


class SavedListUpdateIn(BaseModel):
    """Only the fields that are sent are changed."""

    name: str | None = Field(default=None, min_length=1, max_length=30)
    icon: str | None = Field(default=None, min_length=1, max_length=16)
    position: int | None = Field(default=None, ge=0)


class SavedPlaceOut(BaseModel):
    id: uuid.UUID
    place_id: str
    list_id: uuid.UUID
    list_icon: str
    note: str | None = None
    created_at: datetime


class SavedPlaceIn(BaseModel):
    place_id: str = Field(min_length=1, max_length=255)
    list_id: uuid.UUID | None = Field(
        default=None, description="omitted: the default list; saving again moves the place"
    )
    note: str | None = Field(default=None, max_length=500)


class SavedPlaceUpdateIn(BaseModel):
    """Only the fields that are sent are changed (send `note: null` to clear the note)."""

    list_id: uuid.UUID | None = None
    note: str | None = Field(default=None, max_length=500)
