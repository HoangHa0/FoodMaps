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