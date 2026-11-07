import pytest

from app.modules.match.query_intent import CAT_BAKERY, CAT_CAFE, CAT_FOOD, parse_query


@pytest.mark.parametrize(
    ("query", "cats"),
    [
        ("quán cà phê yên tĩnh học bài", (CAT_CAFE,)),
        ("quan ca phe phu hop di date", (CAT_CAFE,)),
        ("quán ăn chay thanh đạm", (CAT_FOOD,)),
        ("tiệm bánh ngọt ấm cúng", (CAT_BAKERY,)),
        ("quán yên tĩnh học bài", ()),
        ("bánh mì ngon", ()),
        ("quán cà phê có đồ ăn", ()),  # two kinds: ambiguous, no filter
    ],
)
def test_category(query, cats):
    assert parse_query(query).categories == cats


def test_chay_is_required_and_a_facet():
    intent = parse_query("quán ăn chay thanh đạm")
    assert [r.label for r in intent.required] == ["chay"]
    assert {"veg", "light"} <= set(intent.facets)


def test_no_required_for_plain_mood():
    assert parse_query("quán yên tĩnh học bài").required == ()
