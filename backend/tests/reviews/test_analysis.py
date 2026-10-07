"""Review Analysis: pure aggregation, no database."""

from dataclasses import dataclass, field

from app.modules.reviews.analysis import analyze, count_terms


@dataclass
class R:
    source: str = "user"
    score_food: int = 4
    score_space: int = 4
    score_price: int = 4
    score_service: int = 4
    recommended_dishes: list[str] = field(default_factory=list)
    pros: list[str] = field(default_factory=list)
    cons: list[str] = field(default_factory=list)
    suitable_for: list[str] = field(default_factory=list)
    atmosphere: list[str] = field(default_factory=list)
    crowd_level: str | None = None
    price_per_person: int | None = None


def test_no_reviews_gives_empty_analysis():
    a = analyze("p1", [])
    assert a.review_count == 0
    assert a.overall is None
    assert a.aspects.model_dump() == {"food": None, "space": None, "price": None, "service": None}
    assert a.dishes == [] and a.crowd_level is None and a.typical_price is None


def test_aspect_averages_and_overall():
    first = R(score_food=5, score_space=3)
    second = R(score_food=4, score_space=2, score_price=5, score_service=1)
    a = analyze("p1", [first, second])
    assert a.aspects.food == 4.5
    assert a.aspects.space == 2.5
    assert a.aspects.price == 4.5
    assert a.aspects.service == 2.5
    assert a.overall == 3.5  # mean of 4.5, 2.5, 4.5, 2.5


def test_rounding_is_half_up():
    # food mean is exactly 4.25 -> 4.3 (Python's round() would give 4.2)
    rs = [R(score_food=5), R(score_food=4), R(score_food=4), R(score_food=4)]
    assert analyze("p1", rs).aspects.food == 4.3


def test_source_counts():
    a = analyze("p1", [R(source="user"), R(source="sheet"), R(source="sheet")])
    assert (a.user_review_count, a.sheet_review_count, a.review_count) == (1, 2, 3)


def test_terms_group_ignoring_case_and_accents_and_pick_best_spelling():
    rs = [
        R(recommended_dishes=["phở bò"]),
        R(recommended_dishes=["pho bo"]),
        R(recommended_dishes=["phở bò", "Bún chả"]),
    ]
    top = count_terms((r.recommended_dishes for r in rs), 5)
    # all three spellings are one dish; "phở bò" is used twice, so it is the displayed spelling
    assert [(t.name, t.mentions) for t in top] == [("phở bò", 3), ("Bún chả", 1)]


def test_dish_counts_once_per_review():
    rs = [R(recommended_dishes=["phở", "Phở", "PHỞ"]), R(recommended_dishes=["bún"])]
    top = count_terms((r.recommended_dishes for r in rs), 5)
    assert {t.name: t.mentions for t in top} == {"phở": 1, "bún": 1}  # 3 spellings in one review = 1


def test_blank_terms_are_ignored_and_order_is_stable():
    top = count_terms([["", "  ", "b"], ["a"], ["b"], ["a"]], 5)
    assert [(t.name, t.mentions) for t in top] == [("a", 2), ("b", 2)]  # tie -> alphabetical


def test_top_n_limit():
    top = count_terms([[str(i)] for i in range(20)], 3)
    assert len(top) == 3


def test_crowd_level_and_typical_price():
    rs = [
        R(crowd_level="Vừa phải", price_per_person=40_000),
        R(crowd_level="vừa phải", price_per_person=60_000),
        R(crowd_level="Đông", price_per_person=100_000),
        R(price_per_person=None),
    ]
    a = analyze("p1", rs)
    assert a.crowd_level == "Vừa phải"
    assert a.typical_price == 60_000  # median of 40k, 60k, 100k


def test_sheet_style_fields_are_summarised():
    rs = [
        R(
            source="sheet",
            pros=["Yên tĩnh"],
            cons=["Hơi đắt"],
            suitable_for=["Học bài"],
            atmosphere=["Ấm cúng"],
        ),
        R(source="sheet", pros=["yên tĩnh", "Wifi mạnh"], suitable_for=["học bài", "Làm việc"]),
    ]
    a = analyze("p1", rs)
    assert (a.pros[0].name, a.pros[0].mentions) == ("Yên tĩnh", 2)  # tie of spellings -> capitalised
    assert a.cons[0].name == "Hơi đắt"
    assert a.suitable_for[0].mentions == 2
    assert a.atmosphere[0].name == "Ấm cúng"
