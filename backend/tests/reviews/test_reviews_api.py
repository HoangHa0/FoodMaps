"""M4 review API against a real PostgreSQL (foodmaps_test)."""

import uuid

import pytest
from sqlalchemy import text

from app.modules.reviews import service

pytestmark = pytest.mark.db

PW = "matkhau123"
BODY = {
    "score_food": 5,
    "score_space": 4,
    "score_price": 3,
    "score_service": 4,
    "comment": "Quán rất ngon, phục vụ nhanh",
    "recommended_dishes": ["Phở bò"],
    "suitable_for": ["date"],
    "price_per_person": 60_000,
}


def _review(place_id: str, **override) -> dict:
    return {"place_id": place_id, **BODY, **override}


async def _as(c, username: str) -> None:
    """Act as this user (registering the account the first time)."""
    c.cookies.clear()
    r = await c.post("/api/auth/login", json={"username": username, "password": PW})
    if r.status_code != 200:
        r = await c.post("/api/auth/register", json={"username": username, "password": PW})
        assert r.status_code == 201, r.text


async def _post(c, place_id: str, **override):
    return await c.post("/api/reviews", json=_review(place_id, **override))


async def _sheet_review(engine, place_id: str, **cols) -> str:
    """Insert a review imported from the team's form (no author)."""
    values = {
        "place_id": place_id,
        "key": f"test-{uuid.uuid4()}",
        "pros": [],
        "cons": [],
        "dishes": [],
        "crowd": None,
        "price": None,
        "food": 4,
        **cols,
    }
    async with engine.begin() as conn:
        row = await conn.execute(
            text(
                "INSERT INTO reviews (place_id, source, import_key, score_food, score_space, "
                "score_price, score_service, pros, cons, recommended_dishes, crowd_level, "
                "price_per_person, comment) VALUES (:place_id, 'sheet', :key, :food, 4, 4, 4, "
                "CAST(:pros AS text[]), CAST(:cons AS text[]), CAST(:dishes AS text[]), :crowd, "
                ":price, 'nhận xét từ form') RETURNING id"
            ),
            values,
        )
        return str(row.scalar_one())


# --------------------------------------------------------------------------- access rules


async def test_guest_can_read_but_not_write(db_client, places):
    r = await db_client.get("/api/reviews", params={"place_id": places[0]})
    assert r.status_code == 200
    assert r.json() == {"items": [], "total": 0, "limit": 20, "offset": 0}
    assert (await db_client.get(f"/api/reviews/analysis/{places[0]}")).status_code == 200

    some_id = str(uuid.uuid4())
    assert (await _post(db_client, places[0])).status_code == 401
    assert (await db_client.put(f"/api/reviews/{some_id}", json=BODY)).status_code == 401
    assert (await db_client.delete(f"/api/reviews/{some_id}")).status_code == 401
    assert (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).status_code == 401
    assert (
        await db_client.post(f"/api/reviews/{some_id}/report", json={"reason": "spam"})
    ).status_code == 401


async def test_unknown_place_is_404(db_client, places):
    assert (await db_client.get("/api/reviews", params={"place_id": "khong_co"})).status_code == 404
    assert (await db_client.get("/api/reviews/analysis/khong_co")).status_code == 404
    await _as(db_client, "ha_nguyen")
    assert (await _post(db_client, "khong_co")).status_code == 404


# --------------------------------------------------------------------------- create and read


async def test_create_review_and_read_it_back(db_client, places):
    await _as(db_client, "ha_nguyen")
    r = await _post(db_client, places[0])
    assert r.status_code == 201
    review = r.json()
    assert review["author"] == "ha_nguyen" and review["source"] == "user"
    assert review["status"] == "visible" and review["is_mine"] is True
    assert review["recommended_dishes"] == ["Phở bò"] and review["price_per_person"] == 60_000

    mine = (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).json()
    assert mine["id"] == review["id"]

    listed = (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()
    assert listed["total"] == 1 and listed["items"][0]["is_mine"] is True

    db_client.cookies.clear()  # as a guest the same review is shown, but it is not "mine"
    guest = (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()
    assert guest["items"][0]["author"] == "ha_nguyen" and guest["items"][0]["is_mine"] is False


async def test_list_is_newest_first_and_paged(db_client, places):
    await _as(db_client, "ha_nguyen")
    await _post(db_client, places[0], comment="một")
    await _as(db_client, "minh_tran")
    await _post(db_client, places[0], comment="hai")
    page = (await db_client.get("/api/reviews", params={"place_id": places[0], "limit": 1})).json()
    assert page["total"] == 2 and len(page["items"]) == 1 and page["items"][0]["comment"] == "hai"
    page2 = (
        await db_client.get("/api/reviews", params={"place_id": places[0], "limit": 1, "offset": 1})
    ).json()
    assert page2["items"][0]["comment"] == "một"


@pytest.mark.parametrize(
    "override",
    [
        {"score_food": 0},
        {"score_service": 6},
        {"score_space": "ngon"},
        {"recommended_dishes": [f"món {i}" for i in range(9)]},
        {"price_per_person": 10},
        {"comment": "x" * 1001},
        {"suitable_for": ["  "]},
    ],
)
async def test_invalid_input_is_422(db_client, places, override):
    await _as(db_client, "ha_nguyen")
    assert (await _post(db_client, places[0], **override)).status_code == 422


async def test_missing_score_is_422(db_client, places):
    await _as(db_client, "ha_nguyen")
    body = _review(places[0])
    del body["score_price"]
    assert (await db_client.post("/api/reviews", json=body)).status_code == 422


async def test_blank_comment_becomes_null_and_duplicate_tags_are_merged(db_client, places):
    await _as(db_client, "ha_nguyen")
    r = await _post(db_client, places[0], comment="   ", recommended_dishes=["Phở bò", "phở BÒ", "Bún chả"])
    assert r.status_code == 201
    assert r.json()["comment"] is None
    assert r.json()["recommended_dishes"] == ["Phở bò", "Bún chả"]


async def test_second_review_of_same_place_is_409(db_client, places):
    await _as(db_client, "ha_nguyen")
    first = (await _post(db_client, places[0])).json()
    again = await _post(db_client, places[0], comment="viết lại")
    assert again.status_code == 409 and again.json()["error"]["code"] == "review_exists"
    # the same user may review another place, and another user may review this one
    assert (await _post(db_client, places[1])).status_code == 201
    await _as(db_client, "minh_tran")
    assert (await _post(db_client, places[0])).status_code == 201
    assert first["id"]


async def test_mine_is_404_before_the_first_review(db_client, places):
    await _as(db_client, "ha_nguyen")
    assert (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).status_code == 404


# --------------------------------------------------------------------------- edit and delete


async def test_update_own_review(db_client, places):
    await _as(db_client, "ha_nguyen")
    created = (await _post(db_client, places[0])).json()
    r = await db_client.put(
        f"/api/reviews/{created['id']}",
        json={**BODY, "score_food": 2, "comment": "Hôm nay hơi dở", "recommended_dishes": []},
    )
    assert r.status_code == 200
    updated = r.json()
    assert updated["id"] == created["id"] and updated["place_id"] == places[0]
    assert updated["score_food"] == 2 and updated["comment"] == "Hôm nay hơi dở"
    assert updated["recommended_dishes"] == []
    assert updated["created_at"] == created["created_at"]
    assert updated["updated_at"] >= created["updated_at"]
    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 1


async def test_update_unknown_review_is_404(db_client, places):
    await _as(db_client, "ha_nguyen")
    assert (await db_client.put(f"/api/reviews/{uuid.uuid4()}", json=BODY)).status_code == 404
    assert (await db_client.delete(f"/api/reviews/{uuid.uuid4()}")).status_code == 404


async def test_only_the_author_can_edit_or_delete(db_client, places):
    await _as(db_client, "ha_nguyen")
    created = (await _post(db_client, places[0])).json()
    await _as(db_client, "minh_tran")
    put = await db_client.put(f"/api/reviews/{created['id']}", json={**BODY, "comment": "sửa lén"})
    assert put.status_code == 403 and put.json()["error"]["code"] == "forbidden"
    assert (await db_client.delete(f"/api/reviews/{created['id']}")).status_code == 403
    await _as(db_client, "ha_nguyen")
    mine = (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).json()
    assert mine["comment"] == BODY["comment"]  # untouched


async def test_imported_sheet_reviews_are_never_shown_reported_or_changed(db_client, places, engine):
    sheet_id = await _sheet_review(engine, places[0])
    await _as(db_client, "ha_nguyen")

    # not editable or deletable (no author)
    assert (await db_client.put(f"/api/reviews/{sheet_id}", json=BODY)).status_code == 403
    assert (await db_client.delete(f"/api/reviews/{sheet_id}")).status_code == 403

    # not listed: internal reviews are data for Match and Review Analysis, not website content
    listed = (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()
    assert listed["total"] == 0 and listed["items"] == []

    # not reportable (nobody can see it, so there is nothing to report)
    report = await db_client.post(f"/api/reviews/{sheet_id}/report", json={"reason": "spam"})
    assert report.status_code == 404

    # a website review next to it is the only one listed
    assert (await _post(db_client, places[0])).status_code == 201
    listed = (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()
    assert listed["total"] == 1
    assert [i["source"] for i in listed["items"]] == ["user"]

    # ... but both still count in the analysis
    a = (await db_client.get(f"/api/reviews/analysis/{places[0]}")).json()
    assert (a["review_count"], a["user_review_count"], a["sheet_review_count"]) == (2, 1, 1)


async def test_delete_then_review_again(db_client, places):
    await _as(db_client, "ha_nguyen")
    created = (await _post(db_client, places[0])).json()
    assert (await db_client.delete(f"/api/reviews/{created['id']}")).status_code == 204
    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 0
    assert (await _post(db_client, places[0])).status_code == 201


# --------------------------------------------------------------------------- rate limit


async def test_rate_limit_applies_to_new_reviews_only(db_client, places, monkeypatch):
    monkeypatch.setattr(service, "MAX_NEW_REVIEWS", 2)
    await _as(db_client, "ha_nguyen")
    first = (await _post(db_client, places[0])).json()
    assert (await _post(db_client, places[1])).status_code == 201
    blocked = await _post(db_client, places[2])
    assert blocked.status_code == 429 and blocked.json()["error"]["code"] == "rate_limited"
    # editing is never limited
    assert (await db_client.put(f"/api/reviews/{first['id']}", json=BODY)).status_code == 200
    # the limit is per user
    await _as(db_client, "minh_tran")
    assert (await _post(db_client, places[2])).status_code == 201


# --------------------------------------------------------------------------- text filter


async def test_review_with_profanity_is_saved_as_flagged_and_hidden_from_others(db_client, places):
    await _as(db_client, "ha_nguyen")
    r = await _post(db_client, places[0], comment="địt mẹ quán này")
    assert r.status_code == 201 and r.json()["status"] == "flagged"

    mine = (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).json()
    assert mine["status"] == "flagged"  # the author still sees it
    listed = (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()
    assert listed["total"] == 0  # nobody sees it in the public list
    analysis = (await db_client.get(f"/api/reviews/analysis/{places[0]}")).json()
    assert analysis["review_count"] == 0  # and it does not count


async def test_phone_number_in_a_tag_is_flagged(db_client, places):
    await _as(db_client, "ha_nguyen")
    r = await _post(db_client, places[0], suitable_for=["gọi 0912345678"])
    assert r.json()["status"] == "flagged"


async def test_editing_a_filter_flagged_review_clean_makes_it_visible_again(db_client, places):
    await _as(db_client, "ha_nguyen")
    created = (await _post(db_client, places[0], comment="vcl dở quá")).json()
    assert created["status"] == "flagged"
    fixed = await db_client.put(f"/api/reviews/{created['id']}", json={**BODY, "comment": "Hơi dở"})
    assert fixed.json()["status"] == "visible"
    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 1
    again = await db_client.put(f"/api/reviews/{created['id']}", json={**BODY, "comment": "xem www.a.vn"})
    assert again.json()["status"] == "flagged"  # editing in spam flags it again


# --------------------------------------------------------------------------- reports


async def test_report_flow_and_validation(db_client, places):
    await _as(db_client, "ha_nguyen")
    created = (await _post(db_client, places[0])).json()
    rid = created["id"]

    own = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "spam"})
    assert own.status_code == 422 and own.json()["error"]["code"] == "cannot_report_own"

    await _as(db_client, "minh_tran")
    bad = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "khong_hop_le"})
    assert bad.status_code == 422
    ok = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "spam", "note": "  quảng cáo  "})
    assert ok.status_code == 201 and ok.json()["review_id"] == rid and ok.json()["reason"] == "spam"
    twice = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "other"})
    assert twice.status_code == 409 and twice.json()["error"]["code"] == "already_reported"
    missing = await db_client.post(f"/api/reviews/{uuid.uuid4()}/report", json={"reason": "spam"})
    assert missing.status_code == 404

    # one report is not enough to hide it
    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 1


async def test_three_different_reporters_flag_a_review(db_client, places):
    await _as(db_client, "ha_nguyen")
    rid = (await _post(db_client, places[0])).json()["id"]
    for name in ("nguoi_b", "nguoi_c", "nguoi_d"):
        await _as(db_client, name)
        report = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "offensive"})
        assert report.status_code == 201

    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 0
    late = await db_client.post(f"/api/reviews/{rid}/report", json={"reason": "spam"})
    assert late.status_code == 404  # no longer public, so it cannot be reported again

    await _as(db_client, "ha_nguyen")
    mine = (await db_client.get("/api/reviews/mine", params={"place_id": places[0]})).json()
    assert mine["status"] == "flagged"
    # a clean edit does not clear a report-based flag
    edited = await db_client.put(f"/api/reviews/{rid}", json={**BODY, "comment": "đã sửa lại"})
    assert edited.json()["status"] == "flagged"


async def test_editing_never_unhides_a_hidden_review(db_client, places, engine):
    await _as(db_client, "ha_nguyen")
    rid = (await _post(db_client, places[0])).json()["id"]
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE reviews SET status = 'hidden' WHERE id = :id"), {"id": rid})
    edited = await db_client.put(f"/api/reviews/{rid}", json={**BODY, "comment": "sửa"})
    assert edited.status_code == 200 and edited.json()["status"] == "hidden"
    assert (await db_client.get("/api/reviews", params={"place_id": places[0]})).json()["total"] == 0


# --------------------------------------------------------------------------- review analysis


async def test_analysis_of_a_place_without_reviews(db_client, places):
    a = (await db_client.get(f"/api/reviews/analysis/{places[0]}")).json()
    assert a["review_count"] == 0 and a["overall"] is None
    assert a["aspects"] == {"food": None, "space": None, "price": None, "service": None}
    assert a["dishes"] == [] and a["typical_price"] is None


async def test_analysis_combines_sheet_and_website_reviews(db_client, places, engine):
    await _sheet_review(
        engine,
        places[0],
        pros=["Yên tĩnh"],
        cons=["Hơi đắt"],
        dishes=["pho bo", "Bún chả"],
        crowd="Vừa phải",
        price=40_000,
        food=4,
    )
    await _as(db_client, "ha_nguyen")
    await _post(db_client, places[0], score_food=5, recommended_dishes=["Phở bò"], price_per_person=60_000)
    await _as(db_client, "minh_tran")  # flagged: must not count
    await _post(db_client, places[0], comment="địt mẹ", score_food=1, recommended_dishes=["Cơm rang"])

    a = (await db_client.get(f"/api/reviews/analysis/{places[0]}")).json()
    assert (a["review_count"], a["user_review_count"], a["sheet_review_count"]) == (2, 1, 1)
    assert a["aspects"]["food"] == 4.5  # (4 + 5) / 2, the flagged 1-star is ignored
    assert a["dishes"][0]["mentions"] == 2 and a["dishes"][0]["name"] in {"Phở bò", "pho bo"}
    dish_names = {d["name"] for d in a["dishes"]}
    assert "Bún chả" in dish_names and "Cơm rang" not in dish_names
    assert a["pros"] == [{"name": "Yên tĩnh", "mentions": 1}]
    assert a["cons"] == [{"name": "Hơi đắt", "mentions": 1}]
    assert a["crowd_level"] == "Vừa phải"
    assert a["typical_price"] == 50_000  # median of 40k and 60k
