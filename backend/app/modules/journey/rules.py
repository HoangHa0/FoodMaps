"""Pure rules of the Food Journey module: no database, no FastAPI, so they are tested directly.

The service calls these functions and turns their answers into database work and HTTP errors.
Every number comes from `constants.py`.
"""

import hashlib
import hmac
import secrets
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Any

from app.modules.journey.constants import (
    MAX_JOURNEYS_PER_USER,
    SHARE_CODE_BYTES,
    SHARE_LIFETIME_DAYS,
    SHARES_PER_IP_PER_HOUR,
)

SHARE_RATE_WINDOW = timedelta(hours=1)  # the window that SHARES_PER_IP_PER_HOUR is counted in


@dataclass(frozen=True)
class StopData:
    """One stop as the user typed it. The position is its place in the list (1..n)."""

    place_id: str
    planned_time: time | None = None
    note: str | None = None


@dataclass(frozen=True)
class SnapshotData:
    title: str | None
    planned_date: date | None
    stops: list[StopData]


def clean_text(value: str | None) -> str | None:
    """Trim a title or note; blank text means "nothing"."""
    if value is None:
        return None
    return value.strip() or None


# --- limits ----------------------------------------------------------------------------------
def journey_limit_reached(saved_count: int) -> bool:
    """True when the account already keeps the maximum number of journeys (so no new one)."""
    return saved_count >= MAX_JOURNEYS_PER_USER


def share_limit_reached(created_in_window: int) -> bool:
    """True when one address already created the maximum number of links in the last hour."""
    return created_in_window >= SHARES_PER_IP_PER_HOUR


def share_window_start(now: datetime) -> datetime:
    return now - SHARE_RATE_WINDOW


# --- share links -----------------------------------------------------------------------------
def new_share_code() -> str:
    """Unguessable URL-safe code. Anyone holding it can read the snapshot, so it is random."""
    return secrets.token_urlsafe(SHARE_CODE_BYTES)


def share_expires_at(now: datetime) -> datetime:
    return now + timedelta(days=SHARE_LIFETIME_DAYS)


def is_expired(expires_at: datetime, now: datetime) -> bool:
    return expires_at <= now


def hash_client_ip(ip: str, secret: str) -> str:
    """Keyed hash (64 hex characters) of an address: enough to count links, useless to read back.

    A plain hash of an IPv4 address could be reversed by trying every address, so the hash is
    keyed with an application secret.
    """
    return hmac.new(secret.encode(), ip.encode(), hashlib.sha256).hexdigest()


# --- snapshot (what a share link stores) -----------------------------------------------------
def make_snapshot(title: str | None, planned_date: date | None, stops: Sequence[StopData]) -> dict[str, Any]:
    """JSON-safe copy of a journey: dates and times become text, so JSONB can store them."""
    return {
        "title": title,
        "planned_date": planned_date.isoformat() if planned_date else None,
        "stops": [
            {
                "place_id": s.place_id,
                "planned_time": s.planned_time.isoformat(timespec="minutes") if s.planned_time else None,
                "note": s.note,
            }
            for s in stops
        ],
    }


def read_snapshot(data: Mapping[str, Any]) -> SnapshotData:
    """Inverse of `make_snapshot`."""
    planned_date = data.get("planned_date")
    return SnapshotData(
        title=data.get("title"),
        planned_date=date.fromisoformat(planned_date) if planned_date else None,
        stops=[
            StopData(
                place_id=s["place_id"],
                planned_time=time.fromisoformat(s["planned_time"]) if s.get("planned_time") else None,
                note=s.get("note"),
            )
            for s in data.get("stops", [])
        ],
    )
