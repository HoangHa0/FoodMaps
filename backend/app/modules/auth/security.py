"""Pure functions (no database), unit-tested in tests/auth/test_security.py."""

import uuid


def hash_password(plain: str) -> str:
    """Return a bcrypt hash (cost factor 12)."""
    raise NotImplementedError  # TODO(M1)


def verify_password(plain: str, hashed: str) -> bool:
    """Check a password against a bcrypt hash (constant-time; never compare hashes with ==)."""
    raise NotImplementedError  # TODO(M1)


def create_access_token(user_id: uuid.UUID, username: str) -> str:
    """Signed JWT (HS256) with claims: sub=str(user_id), username, iat, exp."""
    raise NotImplementedError  # TODO(M1)


def decode_access_token(token: str) -> tuple[uuid.UUID, str] | None:
    """Return (user_id, username) for a valid, unexpired token; otherwise None (never raises).

    Always pass the expected algorithm explicitly when decoding; never let the library infer it.
    """
    raise NotImplementedError  # TODO(M1)
