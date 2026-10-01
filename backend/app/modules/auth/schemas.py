"""M1 API contract. The frontend generates its TypeScript types from these (via OpenAPI)."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

USERNAME_PATTERN = r"^[A-Za-z0-9_.]{3,30}$"


class RegisterIn(BaseModel):
    username: str = Field(pattern=USERNAME_PATTERN, examples=["ha_nguyen"])
    # bcrypt only uses the first 72 bytes: reject longer passwords instead of truncating silently.
    password: str = Field(min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def _fits_bcrypt(cls, v: str) -> str:
        # max_length counts characters; bcrypt counts BYTES ("ầ" = 3 bytes in UTF-8)
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Mật khẩu quá dài")
        return v


class LoginIn(BaseModel):
    # No format rules at login (a wrong format is just "wrong credentials"), only size caps
    username: str
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    created_at: datetime
