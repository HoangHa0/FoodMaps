"""Pure functions (no database), unit-tested in tests/auth/test_security.py."""

import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import get_settings

_ALGORITHM = "HS256"


def hash_password(plain: str) -> str:
    """Return a bcrypt hash (cost factor 12)."""
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    """Check a password against a bcrypt hash (constant-time; never compare hashes with ==)."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("ascii"))
    except ValueError:  # malformed hash, or password > 72 bytes (bcrypt >= 5 raises)
        return False


def create_access_token(user_id: uuid.UUID, username: str) -> str:
    """Signed JWT (HS256) with claims: sub=str(user_id), username, iat, exp."""
    s = get_settings()
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "username": username,
        "iat": now,
        "exp": now + timedelta(days=s.jwt_expire_days),
    }
    return jwt.encode(payload, s.jwt_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> tuple[uuid.UUID, str] | None:
    """Return (user_id, username) for a valid, unexpired token; otherwise None (never raises).

    Always pass the expected algorithm explicitly when decoding; never let the library infer it.
    """
    try:
        claims = jwt.decode(
            token, get_settings().jwt_secret, algorithms=[_ALGORITHM], options={"require": ["sub", "exp"]}
        )
        return uuid.UUID(claims["sub"]), claims["username"]
    except (jwt.PyJWTError, ValueError, KeyError, TypeError):
        return None
