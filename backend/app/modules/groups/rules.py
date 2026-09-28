"""Decision rules for a group session.

Pure functions (no database, no clock), fully unit-tested in tests/groups/test_rules.py.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Tally:
    candidate_key: str  # place_id or candidate id; opaque to the rules
    rank: int  # 0 = highest match score
    likes: int


@dataclass(frozen=True)
class Decision:
    candidate_key: str
    reason: str  # "majority" | "all_voted"


def majority_threshold(member_count: int) -> int:
    """Minimum likes for an automatic decision: strictly more than 50% of members.

    1 -> 1, 2 -> 2, 3 -> 2, 4 -> 3, 5 -> 3.
    """
    raise NotImplementedError  # TODO(M5)


def decide(tallies: list[Tally], member_count: int, all_voted: bool) -> Decision | None:
    """Return the winning place, or None to keep waiting.

    1. If any place reaches majority_threshold: pick the most-liked place
       (ties -> lower rank wins), reason="majority".
    2. Otherwise, if everyone has voted on every card: pick the most-liked place if it has at
       least one like (ties -> lower rank), reason="all_voted". If nothing got a like, return
       None (the host sees "no match" and can start over with different criteria).
    3. Otherwise: None (voting continues).
    """
    raise NotImplementedError  # TODO(M5)
