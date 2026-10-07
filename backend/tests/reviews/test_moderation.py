"""Text filter: pure functions, no database."""

import pytest

from app.modules.reviews.moderation import check_text, check_texts


@pytest.mark.parametrize(
    "text",
    [
        "Quán ngon, nhân viên dễ thương, giá 50.000đ/người",
        "Đụng hàng với bạn bè ở đây, rất vui",  # "đụng" is not "đụ"
        "Đĩa phở rất đầy",  # "đĩa" is not "đĩ"
        "Hôm nay mình đeo kính ngồi học bài",  # "đeo" is an ordinary word
        "Cơm tấm 45k, sườn to, mở cửa từ 0h đến 23h",
        "Lon nước ngọt giá 15k, các món đều ổn",  # "lon", "các" are ordinary words
        "Đánh giá 4.5 sao, giá 50.000 - 70.000 mỗi người",
        "Đi ngày 12/03/2026 thấy khá đông",
        "Ngon quá, ngon lắm",
        "Mình thích cà phê trứng ở đây. Com tấm cũng ổn",
        "",
        None,
        "   ",
    ],
)
def test_normal_text_is_clean(text):
    assert check_text(text) == ()


@pytest.mark.parametrize(
    "text",
    [
        "Đồ ăn như cứt",
        "địt mẹ quán này",
        "ĐỊT MẸ",
        "đ.m phục vụ tệ",
        "dit me cai quan nay",
        "vcl dở quá",
        "Địttttt",  # stretched letters
        "this place is FUCKING bad",
        "Đ.M!",
    ],
)
def test_profanity_is_caught(text):
    assert "profanity" in check_text(text)


def test_profanity_written_with_decomposed_unicode_is_caught():
    import unicodedata

    assert "profanity" in check_text(unicodedata.normalize("NFD", "địt mẹ"))


@pytest.mark.parametrize(
    "text",
    [
        "đặt bàn tại https://abc.xyz",
        "xem thêm www.quan.vn",
        "ghé shop.com/ao nhé",
        "inbox zalo.me/123456",
        "http://bit.ly/abc",
    ],
)
def test_links_are_caught(text):
    assert "link" in check_text(text)


@pytest.mark.parametrize(
    "text", ["liên hệ 0912 345 678", "gọi +84 912345678", "sđt 0912.345.678", "0912345678"]
)
def test_phone_numbers_are_caught(text):
    assert "phone" in check_text(text)


@pytest.mark.parametrize("text", ["giá 120.000 - 150.000", "mở cửa 0h", "ngày 03/04", "mã 0123"])
def test_prices_and_dates_are_not_phone_numbers(text):
    assert "phone" not in check_text(text)


@pytest.mark.parametrize("text", ["ngon" + "n" * 12, "a" * 10, "ngon ngon ngon ngon ngon ngon"])
def test_keyboard_mashing_is_caught(text):
    assert "repeated" in check_text(text)


def test_normal_repetition_is_fine():
    assert check_text("ngon ngon lắm, rất rất ngon") == ()


def test_check_texts_merges_reasons_without_duplicates():
    result = check_texts(["địt mẹ", "xem www.a.vn", None, "vcl", "gọi 0912345678"])
    assert result.flagged
    assert result.reasons == ("profanity", "link", "phone")


def test_check_texts_clean_and_empty():
    assert not check_texts(["Quán ngon", "Phở bò", None]).flagged
    assert not check_texts([]).flagged
