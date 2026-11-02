"""Pure tests of "Why this place?": which stored bullets are shown for a search."""

from app.modules.match.why import (
    MAX_POINTS,
    MIN_POINTS,
    WHY_MIN_SIMILARITY,
    Highlight,
    WhyPick,
    join_points,
    pick_points,
)


def h(text: str, similarity: float, support: int = 1) -> Highlight:
    return Highlight(text, support, similarity)


def test_matched_bullets_come_first_best_match_first_and_are_flagged():
    picks = pick_points([h("a", 0.5), h("b", 0.9), h("c", 0.7), h("d", 0.1, support=9)], max_points=3)
    assert picks == [WhyPick("b", True), WhyPick("c", True), WhyPick("a", True)]


def test_matched_bullets_are_capped():
    many = [h(f"x{i}", 0.9 - i * 0.01) for i in range(10)]
    picks = pick_points(many)
    assert len(picks) == MAX_POINTS and all(p.matched for p in picks)
    assert [p.text for p in picks] == ["x0", "x1", "x2", "x3"]


def test_too_few_matches_are_topped_up_with_the_strongest_bullets():
    picks = pick_points(
        [h("match", 0.8), h("popular", 0.1, support=9), h("some", 0.2, support=4), h("rare", 0.3, support=1)]
    )
    assert picks == [
        WhyPick("match", True),
        WhyPick("popular", False),  # most reviews mention it
        WhyPick("some", False),
    ]
    assert len(picks) == MIN_POINTS


def test_no_match_at_all_shows_general_strengths_never_flagged_as_matched():
    picks = pick_points([h("a", 0.1, 2), h("b", 0.2, 5), h("c", 0.05, 3), h("d", 0.3, 1)])
    assert [p.text for p in picks] == ["b", "c", "a"]
    assert not any(p.matched for p in picks)


def test_a_place_with_few_bullets_just_shows_them():
    assert pick_points([h("only", 0.9)]) == [WhyPick("only", True)]
    assert pick_points([h("only", 0.0)]) == [WhyPick("only", False)]


def test_a_place_without_bullets_gets_nothing_instead_of_an_invented_reason():
    assert pick_points([]) == []


def test_threshold_is_inclusive_and_can_be_changed():
    assert pick_points([h("edge", WHY_MIN_SIMILARITY)])[0].matched is True
    assert pick_points([h("edge", WHY_MIN_SIMILARITY - 0.01)])[0].matched is False
    assert pick_points([h("x", 0.3)], min_similarity=0.25)[0].matched is True


def test_ties_are_broken_by_support_then_text_so_the_output_is_stable():
    a = pick_points([h("b", 0.6, 1), h("a", 0.6, 1), h("c", 0.6, 5)])
    assert [p.text for p in a] == ["c", "a", "b"]
    assert a == pick_points([h("c", 0.6, 5), h("b", 0.6, 1), h("a", 0.6, 1)])


def test_join_points():
    assert join_points([WhyPick("A", True), WhyPick("B", False)]) == "A; B"
    assert join_points([]) == ""
