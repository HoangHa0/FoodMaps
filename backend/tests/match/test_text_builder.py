from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.modules.match.text_builder import (
    MAX_CHARS,
    MAX_COMMENTS,
    build_place_text,
    pick_comments,
    top_values,
)


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
    assert build_place_text("Tiny Cafe", "cafe", []) == "Tiny Cafe là cafe."


def test_tags_come_before_free_text():
    reviews = [review(suitable_for=["Học bài"], comment="Quán yên tĩnh, wifi mạnh, nhiều ổ điện để làm việc")]
    text = build_place_text("A", "cafe", reviews)
    assert text.index("Phù hợp") < text.index("Nhận xét")


def test_duplicate_comments_are_kept_once():
    same = "Quán yên tĩnh, wifi mạnh, nhiều ổ điện để làm việc"
    reviews = [review(comment=same), review(comment=f" {same} ")]
    assert build_place_text("A", "cafe", reviews).count("nhiều ổ điện") == 1


def test_at_most_max_comments():
    topics = [
        "phở bò tái nạm",
        "cà phê muối",
        "bánh flan",
        "trà đào cam sả",
        "bún chả nướng",
        "chè khúc bạch",
    ]
    reviews = [review(comment=f"Gọi {t}, vị đậm đà, phục vụ nhanh, bàn ghế sạch") for t in topics]
    assert len(pick_comments(reviews, MAX_COMMENTS)) == MAX_COMMENTS


def test_text_is_capped():
    reviews = [review(comment="x" * 5000)]
    assert len(build_place_text("A", "cafe", reviews)) <= MAX_CHARS


def test_cons_are_never_embedded():
    reviews = [review(cons=["Chật chội", "Không gian nhỏ"], pros=["Giá rẻ"])]
    text = build_place_text("A", "Cà phê & Trà", reviews)
    assert "Chật chội" not in text and "Không gian nhỏ" not in text
    assert "Giá rẻ" in text


def test_rare_tag_gets_synonyms():
    text = build_place_text("Q", "Quán ăn", [review(food_types=["Chay"])])
    assert "quán chay" in text and "món chay" in text


def test_category_is_written_as_plain_words():
    assert "quán cà phê" in build_place_text("A", "Cà phê & Trà", [])


def test_junk_and_empty_praise_are_not_picked():
    junk = [
        "Ngon tuyệt vời, quá đỉnh, 10 điểm, nên ghé nha mọi người",  # praise with no content
        "Liên hệ zalo 0912345678 để đặt bàn giá tốt nhất thị trường",  # ad
        "NGON QUÁ TRỜI ƠI ĐẸP LẮM MỌI NGƯỜI NÊN ĐẾN NHÉ BẠN ƠI",  # shouting
        "ngon",
    ]
    assert pick_comments([review(comment=c) for c in junk], 4) == []


def test_one_comment_per_author_stops_a_seeded_batch():
    batch = [
        review(user_id="seed", comment=f"Quán {w} có ổ điện, wifi mạnh, ngồi học bài được cả buổi")
        for w in ("này", "mình", "bạn")
    ]
    real = review(user_id="real", comment="Phở bò tái nạm, nước dùng trong, bánh phở mềm vừa")
    picked = pick_comments([*batch, real], 4)
    assert len(picked) == 2 and "Phở bò" in " ".join(picked)


def test_near_duplicates_keep_one():
    a = review(comment="Quán có nhiều ổ điện, wifi mạnh, ngồi học bài cả buổi được")
    b = review(comment="Quán có nhiều ổ điện, wifi mạnh, ngồi học bài cả buổi rất ổn")
    assert len(pick_comments([a, b], 4)) == 1


def test_concrete_beats_long_and_recent_beats_old():
    now = datetime.now(UTC)
    old = review(
        created_at=now - timedelta(days=400), comment="Bún chả nướng than thơm, nước chấm chua ngọt vừa miệng"
    )
    new = review(created_at=now, comment="Bún chả nướng than thơm, chả viên mềm, nem rán giòn, rau sống tươi")
    rant = review(created_at=now, comment="Chờ " + "rất lâu " * 30)  # long but nothing concrete
    picked = pick_comments([old, rant, new], 1)
    assert picked == [new.comment]


def test_expansion_does_not_repeat_the_tag():
    text = build_place_text("A", "cafe", [review(suitable_for=["Ăn một mình"])])
    assert text.count("ăn một mình") + text.count("Ăn một mình") == 1


def test_comment_of_a_low_rated_review_is_skipped():
    text = "Phở bò tái nạm, nước dùng trong, bánh phở mềm vừa miệng"
    sad = review(comment=text, score_food=2, score_space=3, score_price=3, score_service=2)
    happy = review(comment=text + " lắm", score_food=5, score_space=4, score_price=4, score_service=5)
    assert pick_comments([sad], 4) == []
    assert pick_comments([happy], 4) == [happy.comment]