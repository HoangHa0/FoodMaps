"""When is an insight worth redoing? Pure logic (no database, no network), so it is unit-tested.

A place whose reviews changed (its fingerprint differs) is "stale". Redoing it costs Groq quota, so a
stale place is redone only when ONE of these is true:

  - at least `min_changes` visible reviews were created or edited after the insight was generated, or
  - the insight is at least `stale_days` days old (this also catches deleted/hidden reviews, which
    cannot be counted with `updated_at`).

Otherwise it is "deferred": nothing is sent to Groq, the old insight stays, and a later run decides again.
A place without any insight is never deferred. `--force` ignores this policy.
Setting `min_changes` to 0 (or `stale_days` to 0) turns the policy off: every stale place is redone.
"""

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

from app.modules.match.insights import STATUS_STALE

STATUS_DEFERRED = "deferred"  # stale, but not worth the quota yet

DEFAULT_MIN_CHANGES = 3
DEFAULT_STALE_DAYS = 14


class HasUpdatedAt(Protocol):
    updated_at: datetime


def count_changed(reviews: Sequence[HasUpdatedAt], generated_at: datetime) -> int:
    """How many of these (visible) reviews were created or edited after the insight was generated."""
    return sum(1 for r in reviews if r.updated_at > generated_at)


def apply_policy(
    status: str,
    *,
    reviews: Sequence[HasUpdatedAt],
    generated_at: datetime | None,
    now: datetime,
    min_changes: int = DEFAULT_MIN_CHANGES,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> str:
    """Turn STALE into DEFERRED when the change is too small and the insight is still young.

    Any other status (new, fresh, forced, too_few) is returned unchanged.
    """
    if status != STATUS_STALE or generated_at is None:
        return status
    if count_changed(reviews, generated_at) >= min_changes:
        return status
    age_days = (now - generated_at).total_seconds() / 86_400
    return status if age_days >= stale_days else STATUS_DEFERRED
