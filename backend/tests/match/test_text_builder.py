from types import SimpleNamespace

from app.modules.match.text_builder import MAX_CHARS, MAX_COMMENTS, build_place_text, top_values


def review(**kw):
    base = dict(
        suitable_for=[], atmosphere=[], food_types=[], recommended_dishes=[], pros=[], cons=[], comment=None
    )
    return SimpleNamespace(**(base | kw))


def test_top_values_counts_ignoring_case_and_spaces():
    assert top_values(["Trà chanh", "trà chanh ", "Cà phê", ""], 5) == ["Trà chanh", "Cà phê"]


def test_top_values_orders_by_frequency_and_limits():
    assert top_values(["a", "b", "b", "c", "c", "c"], 2) == ["c", "b"]


def test_top_values_is_deterministic_on_ties():
    assert top_values(["x", "y", "z"], 3) == ["x", "y", "z"]


def test_text_without_reviews_is_name_and_category_only():
    assert build_place_text("Tiny Cafe", "cafe", []) == "Tiny Cafe (cafe)."


def test_tags_come_before_free_text():
    reviews = [review(suitable_for=["Học bài"], comment="Quán yên tĩnh, wifi mạnh")]
    text = build_place_text("A", "cafe", reviews)
    assert text.index("Phù hợp") < text.index("Nhận xét")


def test_duplicate_comments_are_kept_once():
    reviews = [review(comment="Rất ngon"), review(comment=" Rất ngon ")]
    assert build_place_text("A", "cafe", reviews).count("Rất ngon") == 1


def test_at_most_max_comments():
    reviews = [review(comment=f"nhan xet so {i:02d}") for i in range(MAX_COMMENTS + 5)]
    text = build_place_text("A", "cafe", reviews)
    assert text.count("nhan xet so") == MAX_COMMENTS


def test_text_is_capped():
    reviews = [review(comment="x" * 5000)]
    assert len(build_place_text("A", "cafe", reviews)) == MAX_CHARS
