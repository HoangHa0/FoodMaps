"""Specification for M5 decision rules. Remove `pytestmark` once rules.py is implemented."""

import pytest

from app.modules.groups.rules import Decision, Tally, decide, majority_threshold, most_liked


@pytest.mark.parametrize("n,need", [(1, 1), (2, 2), (3, 2), (4, 3), (5, 3), (6, 4), (12, 7)])
def test_majority_threshold(n, need):
    assert majority_threshold(n) == need


def T(key, rank, likes):
    return Tally(key, rank, likes)


def test_waits_when_no_majority_and_not_everyone_voted():
    assert decide([T("a", 0, 1), T("b", 1, 1)], member_count=4, all_voted=False) is None


def test_majority_wins_immediately():
    assert decide([T("a", 0, 1), T("b", 1, 3)], 4, False) == Decision("b", "majority")


def test_majority_tie_broken_by_rank():
    assert decide([T("a", 1, 3), T("b", 0, 3)], 4, False) == Decision("b", "majority")


def test_all_voted_picks_plurality():
    assert decide([T("a", 0, 1), T("b", 1, 2)], 5, True) == Decision("b", "all_voted")


def test_all_voted_nobody_liked_anything():
    assert decide([T("a", 0, 0), T("b", 1, 0)], 3, True) is None


def test_solo_room():
    assert decide([T("a", 0, 1)], 1, False) == Decision("a", "majority")


def test_majority_needs_strictly_more_than_half():
    # 2 of 4 is exactly 50%: not enough, keep waiting
    assert decide([T("a", 0, 2), T("b", 1, 0)], 4, False) is None


def test_all_voted_tie_broken_by_rank():
    assert decide([T("a", 2, 1), T("b", 1, 1), T("c", 0, 0)], 4, True) == Decision("b", "all_voted")


def test_most_liked_ignores_places_without_likes():
    assert most_liked([T("a", 0, 0), T("b", 1, 0)]) is None
    assert most_liked([T("a", 0, 0), T("b", 1, 1)]) == T("b", 1, 1)
