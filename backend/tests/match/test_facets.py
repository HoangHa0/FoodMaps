from types import SimpleNamespace

from app.modules.match.facets import facets_score, passes_required
from app.modules.match.query_intent import parse_query


def rv(**kw):
    base = dict(suitable_for=[], atmosphere=[], facilities=[], food_types=[], pros=[], crowd_level=None)
    return SimpleNamespace(**(base | kw))


def test_no_facet_means_not_applied():
    assert facets_score((), [rv()]) is None


def test_more_reviews_with_the_tag_score_higher_and_one_review_is_weak():
    one = facets_score(("date",), [rv(suitable_for=["Date"])])
    four = facets_score(("date",), [rv(suitable_for=["Date"])] * 4)
    assert 0 < one < four < 1


def test_noise_penalises_quiet():
    quiet = facets_score(("quiet",), [rv(atmosphere=["Yên tĩnh"])] * 3)
    mixed = facets_score(("quiet",), [rv(atmosphere=["Yên tĩnh", "Ồn ào"])] * 3)
    assert mixed < quiet


def test_place_without_reviews_scores_zero():
    assert facets_score(("study",), []) == 0.0


def test_required_chay_by_tag_or_name_only():
    need = parse_query("quán chay").required
    assert passes_required(need, "Phở - 52 Phố Vọng", [rv(food_types=["Thanh đạm, nhẹ bụng"])]) is False
    assert passes_required(need, "Đi Ăn Chay Đi", []) is True
    assert passes_required(need, "Quán X", [rv(food_types=["Chay"])]) is True
