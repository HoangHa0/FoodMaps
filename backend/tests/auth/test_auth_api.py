"""M1 integration tests against a real PostgreSQL (foodmaps_test)."""

import pytest

pytestmark = pytest.mark.db

PW = "matkhau123"


async def _register(c, username="ha_nguyen", password=PW):
    return await c.post("/api/auth/register", json={"username": username, "password": password})


async def test_register_sets_cookie_and_logs_in(db_client):
    r = await _register(db_client)
    assert r.status_code == 201
    assert r.json()["username"] == "ha_nguyen"
    assert "password_hash" not in r.json()
    assert "fm_session=" in r.headers["set-cookie"] and "HttpOnly" in r.headers["set-cookie"]
    me = await db_client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["username"] == "ha_nguyen"


async def test_duplicate_username_ignores_case(db_client):
    await _register(db_client, "Ha_Nguyen")
    r = await _register(db_client, "ha_nguyen")
    assert r.status_code == 409
    assert r.json()["error"]["code"] == "username_taken"


async def test_login_is_case_insensitive(db_client):
    await _register(db_client, "Ha_Nguyen")
    db_client.cookies.clear()
    r = await db_client.post("/api/auth/login", json={"username": "HA_NGUYEN", "password": PW})
    assert r.status_code == 200 and r.json()["username"] == "Ha_Nguyen"


async def test_wrong_password_and_unknown_user_look_identical(db_client):
    await _register(db_client)
    db_client.cookies.clear()
    login = "/api/auth/login"
    wrong_pw = await db_client.post(login, json={"username": "ha_nguyen", "password": "sai-mat-khau"})
    no_user = await db_client.post(login, json={"username": "khong_ton_tai", "password": PW})
    assert wrong_pw.status_code == no_user.status_code == 401
    assert wrong_pw.json() == no_user.json()


async def test_me_without_cookie_is_401(db_client):
    r = await db_client.get("/api/auth/me")
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthenticated"


async def test_logout_clears_session(db_client):
    await _register(db_client)
    assert (await db_client.post("/api/auth/logout")).status_code == 204
    assert (await db_client.get("/api/auth/me")).status_code == 401


async def test_bearer_header_also_works(db_client):
    await _register(db_client)
    token = db_client.cookies["fm_session"]
    db_client.cookies.clear()
    r = await db_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


async def test_garbage_cookie_counts_as_guest(db_client):
    db_client.cookies.set("fm_session", "khong.phai.jwt")
    assert (await db_client.get("/api/auth/me")).status_code == 401


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("ha_nguyen", "1234567"),  # 7 characters
        ("ha", PW),  # username too short
        ("hà_nguyễn", PW),  # accents not allowed in usernames
        ("ha_nguyen", "ầ" * 30),  # 30 characters but 90 bytes: over bcrypt's limit
    ],
)
async def test_invalid_input_is_422_not_500(db_client, username, password):
    assert (await _register(db_client, username, password)).status_code == 422
