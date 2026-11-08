"""M2 saved places API against a real PostgreSQL (foodmaps_test).

`db_client` (tests/conftest.py) empties `users` before every test, which also removes their lists and
saved places. Test places are inserted here and removed afterwards.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from tests.conftest import TEST_DATABASE_URL

pytestmark = pytest.mark.db

PW = "matkhau123"
PLACE_A = "saved_test_place_a"
PLACE_B = "saved_test_place_b"
PLACE_IDS = [PLACE_A, PLACE_B]


async def _as(c, username: str) -> None:
    """Act as this user (registering the account the first time)."""
    c.cookies.clear()
    r = await c.post("/api/auth/login", json={"username": username, "password": PW})
    if r.status_code != 200:
        r = await c.post("/api/auth/register", json={"username": username, "password": PW})
        assert r.status_code == 201, r.text


@pytest.fixture
async def places(db_client):
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = any(:ids)"), {"ids": PLACE_IDS})
        for pid, code in ((PLACE_A, "S901"), (PLACE_B, "S902")):
            await conn.execute(
                text(
                    "insert into places (place_id, place_code, manual_name, category, lat, lng) "
                    "values (:pid, :code, 'Quán Test', 'cafe', 21.03, 105.85)"
                ),
                {"pid": pid, "code": code},
            )
    yield
    async with engine.begin() as conn:
        await conn.execute(text("delete from places where place_id = any(:ids)"), {"ids": PLACE_IDS})
    await engine.dispose()


async def _lists(c) -> list[dict]:
    r = await c.get("/api/saved-places/lists")
    assert r.status_code == 200, r.text
    return r.json()


async def test_login_is_required(db_client):
    db_client.cookies.clear()
    assert (await db_client.get("/api/saved-places/lists")).status_code == 401
    assert (await db_client.get("/api/saved-places")).status_code == 401
    assert (await db_client.post("/api/saved-places", json={"place_id": PLACE_A})).status_code == 401


async def test_default_list_is_created_on_first_use(db_client):
    await _as(db_client, "saver1")
    lists = await _lists(db_client)
    assert len(lists) == 1
    assert lists[0]["name"] == "Yêu thích"
    assert lists[0]["icon"] == "❤️"
    assert lists[0]["is_default"] is True
    assert lists[0]["place_count"] == 0
    assert len(await _lists(db_client)) == 1  # a second call does not create another


async def test_save_goes_to_default_list_and_saving_again_is_not_an_error(db_client, places):
    await _as(db_client, "saver2")
    first = await db_client.post("/api/saved-places", json={"place_id": PLACE_A})
    assert first.status_code == 201
    again = await db_client.post("/api/saved-places", json={"place_id": PLACE_A, "note": "ngon"})
    assert again.status_code == 200
    assert again.json()["id"] == first.json()["id"]
    assert again.json()["note"] == "ngon"
    assert again.json()["list_icon"] == "❤️"
    assert (await _lists(db_client))[0]["place_count"] == 1
    assert len((await db_client.get("/api/saved-places")).json()) == 1


async def test_saving_with_another_list_moves_the_place(db_client, places):
    await _as(db_client, "saver3")
    new = await db_client.post("/api/saved-places/lists", json={"name": "Cà phê", "icon": "☕"})
    assert new.status_code == 201
    list_id = new.json()["id"]
    await db_client.post("/api/saved-places", json={"place_id": PLACE_A})
    moved = await db_client.post("/api/saved-places", json={"place_id": PLACE_A, "list_id": list_id})
    assert moved.json()["list_id"] == list_id
    assert moved.json()["list_icon"] == "☕"
    counts = {item["name"]: item["place_count"] for item in await _lists(db_client)}
    assert counts == {"Yêu thích": 0, "Cà phê": 1}


async def test_update_note_and_move_with_patch(db_client, places):
    await _as(db_client, "saver4")
    saved = (await db_client.post("/api/saved-places", json={"place_id": PLACE_A})).json()
    other = (await db_client.post("/api/saved-places/lists", json={"name": "Ăn tối", "icon": "🍜"})).json()
    r = await db_client.patch(
        f"/api/saved-places/{saved['id']}", json={"list_id": other["id"], "note": "đi cùng nhóm"}
    )
    assert r.status_code == 200
    assert r.json()["list_id"] == other["id"]
    assert r.json()["note"] == "đi cùng nhóm"
    cleared = await db_client.patch(f"/api/saved-places/{saved['id']}", json={"note": None})
    assert cleared.json()["note"] is None


async def test_unknown_place_is_404(db_client, places):
    await _as(db_client, "saver5")
    r = await db_client.post("/api/saved-places", json={"place_id": "no_such_place"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


async def test_other_users_data_is_404(db_client, places):
    await _as(db_client, "owner")
    saved = (await db_client.post("/api/saved-places", json={"place_id": PLACE_A})).json()
    mine = (await db_client.post("/api/saved-places/lists", json={"name": "Riêng", "icon": "🔒"})).json()

    await _as(db_client, "intruder")
    assert (await db_client.patch(f"/api/saved-places/{saved['id']}", json={"note": "x"})).status_code == 404
    assert (await db_client.delete(f"/api/saved-places/{saved['id']}")).status_code == 404
    assert (await db_client.delete(f"/api/saved-places/lists/{mine['id']}")).status_code == 404
    assert (
        await db_client.post("/api/saved-places", json={"place_id": PLACE_B, "list_id": mine["id"]})
    ).status_code == 404
    assert (await db_client.get("/api/saved-places")).json() == []


async def test_duplicate_list_name_is_409(db_client):
    await _as(db_client, "saver6")
    body = {"name": "Quán nhậu", "icon": "🍺"}
    assert (await db_client.post("/api/saved-places/lists", json=body)).status_code == 201
    r = await db_client.post("/api/saved-places/lists", json=body)
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "list_name_taken"


async def test_default_list_can_be_renamed_but_not_deleted(db_client):
    await _as(db_client, "saver7")
    default = (await _lists(db_client))[0]
    renamed = await db_client.patch(
        f"/api/saved-places/lists/{default['id']}", json={"name": "Muốn thử", "icon": "⭐"}
    )
    assert renamed.status_code == 200
    assert renamed.json()["is_default"] is True
    gone = await db_client.delete(f"/api/saved-places/lists/{default['id']}")
    assert gone.status_code == 400
    assert gone.json()["error"]["code"] == "cannot_delete_default_list"


async def test_deleting_a_list_removes_its_saved_places_but_not_the_place(db_client, places):
    await _as(db_client, "saver8")
    extra = (await db_client.post("/api/saved-places/lists", json={"name": "Tạm", "icon": "📌"})).json()
    await db_client.post("/api/saved-places", json={"place_id": PLACE_A, "list_id": extra["id"]})
    assert (await db_client.delete(f"/api/saved-places/lists/{extra['id']}")).status_code == 204
    assert (await db_client.get("/api/saved-places")).json() == []
    # the place itself is untouched and can be saved again
    assert (await db_client.get(f"/api/places/{PLACE_A}/summary")).status_code == 200
    assert (await db_client.post("/api/saved-places", json={"place_id": PLACE_A})).status_code == 201


async def test_delete_saved_place(db_client, places):
    await _as(db_client, "saver9")
    saved = (await db_client.post("/api/saved-places", json={"place_id": PLACE_A})).json()
    assert (await db_client.delete(f"/api/saved-places/{saved['id']}")).status_code == 204
    assert (await db_client.delete(f"/api/saved-places/{saved['id']}")).status_code == 404
