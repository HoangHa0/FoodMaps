"""Pure tests of which reviews go into the prompt when they do not all fit."""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.modules.match import insights as ins

T0 = datetime(2026, 1, 1, tzinfo=UTC)


@dataclass
class R:
    day: int  # day offset: a bigger day is newer
    id: uuid.UUID = field(default_factory=uuid.uuid4)
    score_food: int = 5
    score_space: int = 4
    score_price: int = 3
    score_service: int = 4
    recommended_dishes: list[str] = field(default_factory=list)
    suitable_for: list[str] = field(default_factory=list)
    price_per_person: int | None = None
    source: str = "user"

    @property
    def updated_at(self) -> datetime:
        return T0 + timedelta(days=self.day)

    @property
    def comment(self) -> str:
        return f"nhan-xet-ngay-{self.day:03d}"


def days_in(text: str) -> list[int]:
    return [int(part[:3]) for part in text.split("nhan-xet-ngay-")[1:]]


def reviews(n: int) -> list[R]:
    return [R(day=d) for d in range(n)]


LINE = len(ins._format_review(999, R(day=0))) + 1


def test_everything_is_kept_when_it_fits():
    text, used = ins.format_reviews(reviews(10), max_chars=LINE * 10)
    assert used == 10
    assert days_in(text) == list(range(9, -1, -1))  # all of them, newest first


def test_newest_reviews_take_half_and_older_ones_are_sampled_evenly():
    text, used = ins.format_reviews(reviews(100), max_chars=LINE * 20)
    days = days_in(text)
    assert used == len(days) and 18 <= used <= 20
    recent = [d for d in days if d >= 90]
    older = [d for d in days if d < 90]
    assert 9 <= len(recent) <= 10  # about half of the space for the newest
    assert recent == list(range(99, 99 - len(recent), -1))  # the newest ones, none skipped
    assert len(older) >= 8
    assert older == sorted(older, reverse=True)  # still newest first
    assert min(older) < 15 and max(older) > 75  # spread over the whole older range, not just the top
    gaps = [a - b for a, b in zip(older, older[1:], strict=False)]
    assert max(gaps) - min(gaps) <= 2  # evenly spaced


def test_a_burst_of_new_reviews_cannot_push_every_old_review_out():
    burst = [R(day=1000 + i) for i in range(50)]
    old = [R(day=i) for i in range(20)]
    text, _ = ins.format_reviews(burst + old, max_chars=LINE * 12)
    days = days_in(text)
    assert any(d < 1000 for d in days)  # an old (real) review is still read
    assert sum(1 for d in days if d >= 1000) <= 7  # the burst gets about half of the space


def test_the_prompt_never_exceeds_the_limit():
    for n in (13, 40, 100, 250):
        for cap in (LINE * 5, LINE * 12, LINE * 31):
            text, _ = ins.format_reviews(reviews(n), max_chars=cap)
            assert len(text) <= cap


def test_same_reviews_give_the_same_prompt():
    revs = reviews(60)
    assert ins.format_reviews(revs, max_chars=LINE * 15) == ins.format_reviews(
        list(reversed(revs)), max_chars=LINE * 15
    )


def test_at_least_one_review_even_when_the_limit_is_tiny():
    text, used = ins.format_reviews(reviews(30), max_chars=10)
    assert used == 1 and days_in(text) == [29]
