"""Pure tests of the refresh policy: when a stale place is redone or deferred."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.modules.match import insights as ins
from app.modules.match.refresh_policy import STATUS_DEFERRED, apply_policy, count_changed

GENERATED = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)
NOW = GENERATED + timedelta(days=2)


@dataclass
class R:
    updated_at: datetime


def after(hours: int = 1) -> R:
    return R(GENERATED + timedelta(hours=hours))


def before() -> R:
    return R(GENERATED - timedelta(days=5))


def run(status, reviews, *, now=NOW, generated_at=GENERATED, **kw):
    return apply_policy(status, reviews=reviews, generated_at=generated_at, now=now, **kw)


def test_count_changed_counts_only_reviews_after_generation():
    assert count_changed([before(), after(), after(5)], GENERATED) == 2
    assert count_changed([R(GENERATED)], GENERATED) == 0  # equal is not "after"


def test_few_changes_and_young_insight_is_deferred():
    assert run(ins.STATUS_STALE, [before(), after(), after(2)]) == STATUS_DEFERRED


def test_three_changes_redo_the_place():
    assert run(ins.STATUS_STALE, [after(), after(2), after(3)]) == ins.STATUS_STALE


def test_old_insight_is_redone_even_with_no_countable_change():
    # e.g. a review was hidden or deleted: it cannot be counted, so age decides
    later = GENERATED + timedelta(days=14)
    assert run(ins.STATUS_STALE, [before()], now=later) == ins.STATUS_STALE
    just_before = GENERATED + timedelta(days=14) - timedelta(minutes=1)
    assert run(ins.STATUS_STALE, [before()], now=just_before) == STATUS_DEFERRED


def test_other_statuses_are_never_changed():
    for status in (ins.STATUS_NEW, ins.STATUS_FRESH, ins.STATUS_FORCED, ins.STATUS_TOO_FEW):
        assert run(status, [after()]) == status
    assert run(ins.STATUS_STALE, [after()], generated_at=None) == ins.STATUS_STALE


def test_zero_turns_the_policy_off():
    assert run(ins.STATUS_STALE, [after()], min_changes=0) == ins.STATUS_STALE
    assert run(ins.STATUS_STALE, [after()], stale_days=0) == ins.STATUS_STALE


def test_custom_thresholds():
    assert run(ins.STATUS_STALE, [after()], min_changes=1) == ins.STATUS_STALE
    assert run(ins.STATUS_STALE, [after()], min_changes=5, stale_days=1) == ins.STATUS_STALE
