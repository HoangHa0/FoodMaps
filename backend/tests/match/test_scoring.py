"""Pure scoring tests: no database, no model."""

import pytest

from app.modules.match import scoring as sc
from app.modules.match.scoring import RawCandidate


def raw(place_id="p", sim=0.5, dist=500, price=50_000, avg=4.0, n=5, category="cafe"):
    return RawCandidate(place_id, category, price, sim, dist, avg, n)


def run(rows, **kw):
    args = dict(radius_m=2000, price_min=None, price_max=None, k=4) | kw
    return sc.score_candidates(rows, **args)


def test_semantic_is_calibrated_and_clamped():
    assert sc.semantic_score(0.0) == 0
    assert sc.semantic_score(sc.SIM_HIGH + 0.2) == 1
    assert 0 < sc.semantic_score(0.4) < 1


def test_rating_shrinks_towards_prior():
    one_five_star = sc.rating_score(5.0, 1)
    ten_good = sc.rating_score(4.5, 10)
    assert ten_good > one_five_star
    assert sc.rating_score(None, 0) == pytest.approx((sc.RATING_PRIOR - 1) / 4)


def test_budget_is_strict_no_tolerance():
    assert sc.budget_allowed(100_000, None, 100_000)  # the edge itself is allowed
    assert not sc.budget_allowed(100_001, None, 100_000)
    assert not sc.budget_allowed(40_000, None, 35_000)
    assert not sc.budget_allowed(49_999, 50_000, None)
    assert sc.budget_allowed(None, None, 100_000)  # unknown price is kept


def test_budget_score():
    assert sc.budget_score(80_000, 50_000, 100_000) == 1.0
    assert sc.budget_score(None, None, 100_000) == sc.BUDGET_UNKNOWN_SCORE
    assert sc.budget_score(10, None, None) is None


def test_combine_drops_missing_components():
    full = sc.combine({"semantic": 1.0, "distance": None, "rating": None, "budget": None})
    assert full == 1.0  # only semantic applies


def test_radius_is_a_hard_filter():
    out = run([raw("near", dist=500), raw("far", dist=2500)])
    assert [s.place_id for s in out] == ["near"]


def test_budget_is_a_hard_filter():
    out = run([raw("ok", price=80_000), raw("pricey", price=300_000)], price_max=100_000)
    assert [s.place_id for s in out] == ["ok"]


def test_no_origin_skips_distance():
    out = run([raw("a", dist=None)])
    assert out[0].distance_m is None and out[0].components["distance"] is None


def test_sorted_by_score_and_cut_to_k():
    rows = [raw(f"p{i}", sim=0.2 + i * 0.05) for i in range(6)]
    out = run(rows, k=3)
    assert [s.place_id for s in out] == ["p5", "p4", "p3"]
    assert [s.score for s in out] == sorted((s.score for s in out), reverse=True)


def test_ties_are_deterministic():
    out = run([raw("b"), raw("a")])
    assert [s.place_id for s in out] == ["a", "b"]


def test_score_stays_in_range():
    for sim in (-1, 0, 0.3, 1):
        for s in run([raw(sim=sim)]):
            assert 0 <= s.score <= 1


def test_haversine_known_distance():
    # Hoan Kiem Lake -> Temple of Literature is about 2 km
    d = sc.haversine_m(21.0285, 105.8522, 21.0287, 105.8354)
    assert 1500 < d < 1900


def test_format_helpers():
    assert sc.format_vnd(40_000) == "40.000đ"
    assert sc.format_vnd(1_250_000) == "1.250.000đ"
    assert sc.format_distance(347) == "350 m"
    assert sc.format_distance(2140) == "2,1 km"


def test_reasons_show_distance_price_and_rating():
    s = run([raw(sim=0.6, dist=347, price=40_000, avg=4.26, n=12)])[0]
    reasons = sc.build_reasons(s)
    assert "📍 Cách khoảng 350 m" in reasons
    assert "💰 ~ 40.000đ/người" in reasons
    assert "⭐ 4.3 (12 đánh giá)" in reasons
    assert len(reasons) <= sc.MAX_REASONS


def test_reasons_skip_missing_data():
    s = run([raw(sim=0.1, dist=None, price=None, avg=None, n=0)])[0]
    assert sc.build_reasons(s) == []


# --------------------------------------------------------------------------- "Not Match" rerank


def scored(place_id, *, score=0.7, distance=None, semantic=0.6, price=None, crowd=None, radius=2000):
    """A place already scored, built by hand so each rerank rule is tested on its own."""
    return sc.Scored(
        place_id=place_id,
        category="cafe",
        score=score,
        distance_m=distance,
        components={
            "semantic": semantic,
            "distance": None if distance is None else sc.distance_score(distance, radius),
        },
        price_per_person=price,
        crowd=crowd,
    )


def order(places):
    return [p.place_id for p in places]


def test_reject_removes_the_rejected_place():
    out = sc.rerank_after_reject([scored("a"), scored("b")], sc.REASON_WRONG_VIBE, rejected_place_id="a")
    assert order(out) == ["b"]


def test_reject_with_nothing_left_is_empty():
    assert sc.rerank_after_reject([], sc.REASON_TOO_FAR) == []
    assert sc.rerank_after_reject([scored("a")], sc.REASON_TOO_FAR, rejected_place_id="a") == []


def test_too_far_prefers_the_closer_place_even_with_a_slightly_lower_score():
    far_but_better = scored("far", score=0.80, distance=1800)
    near = scored("near", score=0.72, distance=200)
    assert order(sc.rerank_after_reject([far_but_better, near], sc.REASON_TOO_FAR)) == ["near", "far"]


def test_too_far_without_origin_keeps_the_score_order():
    a, b = scored("a", score=0.9), scored("b", score=0.6)
    assert order(sc.rerank_after_reject([b, a], sc.REASON_TOO_FAR)) == ["a", "b"]


def test_too_expensive_prefers_the_cheaper_place():
    dear = scored("dear", score=0.80, price=150_000)
    cheap = scored("cheap", score=0.72, price=30_000)
    assert order(sc.rerank_after_reject([dear, cheap], sc.REASON_TOO_EXPENSIVE)) == ["cheap", "dear"]


def test_too_expensive_unknown_price_is_neutral_not_cheap():
    unknown = scored("unknown", score=0.75, price=None)
    cheap = scored("cheap", score=0.75, price=30_000)
    dear = scored("dear", score=0.75, price=150_000)
    out = sc.rerank_after_reject([dear, unknown, cheap], sc.REASON_TOO_EXPENSIVE)
    assert order(out) == ["cheap", "unknown", "dear"]


def test_too_expensive_with_equal_prices_keeps_the_score_order():
    a, b = scored("a", score=0.9, price=50_000), scored("b", score=0.6, price=50_000)
    assert order(sc.rerank_after_reject([b, a], sc.REASON_TOO_EXPENSIVE)) == ["a", "b"]


def test_too_crowded_prefers_the_quieter_place():
    packed = scored("packed", score=0.80, crowd=1.0)
    quiet = scored("quiet", score=0.72, crowd=0.0)
    assert order(sc.rerank_after_reject([packed, quiet], sc.REASON_TOO_CROWDED)) == ["quiet", "packed"]


def test_too_crowded_unknown_crowd_sits_between_quiet_and_packed():
    packed, unknown, quiet = (
        scored("packed", crowd=1.0),
        scored("unknown", crowd=None),
        scored("quiet", crowd=0.0),
    )
    out = sc.rerank_after_reject([packed, unknown, quiet], sc.REASON_TOO_CROWDED)
    assert order(out) == ["quiet", "unknown", "packed"]


def test_wrong_vibe_prefers_the_better_mood_match():
    # "near" wins on distance in the original score, but the user said the vibe is wrong
    near_wrong_vibe = scored("near", score=0.75, semantic=0.2, distance=100)
    far_right_vibe = scored("far", score=0.70, semantic=0.9, distance=1500)
    out = sc.rerank_after_reject([near_wrong_vibe, far_right_vibe], sc.REASON_WRONG_VIBE)
    assert order(out) == ["far", "near"]


def test_unknown_reason_keeps_the_score_order():
    a, b = scored("a", score=0.9), scored("b", score=0.6)
    assert order(sc.rerank_after_reject([b, a], "something_else")) == ["a", "b"]


def test_rerank_keeps_the_original_score_for_display():
    out = sc.rerank_after_reject([scored("a", score=0.61)], sc.REASON_TOO_FAR)
    assert out[0].score == 0.61


def test_rerank_is_deterministic_on_ties():
    out = sc.rerank_after_reject([scored("b"), scored("a")], sc.REASON_WRONG_VIBE)
    assert order(out) == ["a", "b"]
    assert order(sc.rerank_after_reject([scored("a"), scored("b")], sc.REASON_WRONG_VIBE)) == ["a", "b"]


def test_rerank_does_not_change_its_input():
    items = [scored("b", score=0.5), scored("a", score=0.9)]
    sc.rerank_after_reject(items, sc.REASON_TOO_FAR)
    assert order(items) == ["b", "a"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Vắng", 0.0),
        ("vắng khách", 0.0),
        ("Không đông", 0.0),
        ("Vừa phải", 0.5),
        ("Bình thường", 0.5),
        ("Đông", 0.8),
        ("Rất đông", 1.0),
        ("Đông nghịt, phải chờ", 1.0),
        ("không nhớ", None),
        ("", None),
        (None, None),
    ],
)
def test_crowd_level_to_number(text, expected):
    assert sc.crowd_level_to_number(text) == expected


def test_mean_crowd_ignores_unknown_answers():
    assert sc.mean_crowd(["Vắng", "Đông", "???", None]) == pytest.approx(0.4)
    assert sc.mean_crowd(["???", None]) is None
    assert sc.mean_crowd([]) is None


def test_with_crowd_attaches_numbers():
    out = sc.with_crowd([scored("a"), scored("b")], {"a": 0.3})
    assert [p.crowd for p in out] == [0.3, None]
