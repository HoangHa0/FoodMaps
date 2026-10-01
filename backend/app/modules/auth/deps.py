"""Authentication dependencies, re-exported to other modules via `app/shared/auth.py`.

The token is read from the httpOnly cookie `settings.auth_cookie_name`, with an
`Authorization: Bearer <token>` header as a fallback (handy for Swagger UI and Postman).
"""

import uuid
from typing import Annotated

from fastapi import Depends, Request
from pydantic import BaseModel

from app.core.config import get_settings
from app.modules.auth.security import decode_access_token


class AuthUser(BaseModel):
    """All that other modules ever see of a user: no password hash, no ORM object."""

    id: uuid.UUID
    username: str


def _extract_token(request: Request) -> str | None:
    token = request.cookies.get(get_settings().auth_cookie_name)
    if token:
        return token
    scheme, _, value = request.headers.get("Authorization", "").partition(" ")
    if scheme.lower() == "bearer" and value.strip():
        return value.strip()
    return None


async def get_optional_user(request: Request) -> AuthUser | None:
    """Return the logged-in user, or None for guests.

    An invalid or expired token also yields None, so guests with a stale cookie can still use
    the map and search. Only decodes the JWT (no database query), which keeps it cheap enough
    to use on every endpoint.
    """
    token = _extract_token(request)
    if token is None:
        return None
    decoded = decode_access_token(token)
    if decoded is None:
        return None
    user_id, username = decoded
    return AuthUser(id=user_id, username=username)


async def get_current_user(
    user: Annotated[AuthUser | None, Depends(get_optional_user)],
) -> AuthUser:
    """Require a logged-in user (saving places, writing reviews)."""
    from app.core.errors import AppError

    if user is None:
        raise AppError(401, "unauthenticated", "Bạn cần đăng nhập để dùng tính năng này")
    return user
