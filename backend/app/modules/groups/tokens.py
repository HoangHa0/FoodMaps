"""Room codes and participant tokens."""

# Excludes characters that are easy to confuse when read aloud or retyped: 0/O, 1/I/L
ROOM_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
ROOM_CODE_LEN = 6


def new_room_code() -> str:
    """Random code of ROOM_CODE_LEN characters from ROOM_CODE_ALPHABET (cryptographically secure)."""
    raise NotImplementedError  # TODO(M5)


def new_participant_token() -> str:
    """Random URL-safe token with at least 32 bytes of entropy."""
    raise NotImplementedError  # TODO(M5)


def hash_token(token: str) -> str:
    """Hex SHA-256 of the token.

    A plain hash is enough (no bcrypt): the token is long and random, not a user-chosen password.
    """
    raise NotImplementedError  # TODO(M5)
