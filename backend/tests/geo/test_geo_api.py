"""geo endpoints without a database or network: VietMap is replaced by `httpx.MockTransport`.

These run with plain `pytest` (no Docker). The mock sees the real request, so the query parameters and
the API key handling are checked too.
"""

from types import SimpleNamespace

import httpx
import pytest

from app.modules.geo import service

KEY = "test-key-123"

AUTOCOMPLETE_BODY = [
    {
        "ref_id": "geocode:AAA",
        "name": "Cầu Giấy Mall",
        "display": "Cầu Giấy Mall, Dịch Vọng, Cầu Giấy, Hà Nội",
        "address": "Dịch Vọng, Cầu Giấy, Hà Nội",
    },
    {"ref_id": "geocode:BBB", "name": "", "display": "12 Xuân Thủy, Dịch Vọng Hậu, Cầu Giấy, Hà Nội"},
    {"name": "no ref id: skipped"},
    {"ref_id": "geocode:CCC", "name": "", "display": ""},  # nothing to show: skipped
    "not even an object",
]


@pytest.fixture(autouse=True)
def _isolated(monkeypatch):
    """A key is configured and the cache is empty for every test; each test installs its own transport."""
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(vietmap_api_key=KEY))
    service._suggest_cache.clear()
    yield
    service._suggest_cache.clear()


def _mock_vietmap(monkeypatch, handler) -> list[httpx.Request]:
    """Route VietMap calls to `handler`; the returned list records every request that was made."""
    seen: list[httpx.Request] = []

    def recording(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    monkeypatch.setattr(service, "_transport", httpx.MockTransport(recording))
    return seen


async def test_suggest_returns_usable_items_and_asks_vietmap_with_the_right_parameters(client, monkeypatch):
    seen = _mock_vietmap(monkeypatch, lambda r: httpx.Response(200, json=AUTOCOMPLETE_BODY))

    res = await client.get("/api/geo/suggest", params={"q": "cầu giấy"})

    assert res.status_code == 200
    assert res.json() == [
        {"ref_id": "geocode:AAA", "name": "Cầu Giấy Mall", "address": "Dịch Vọng, Cầu Giấy, Hà Nội"},
        # no name: the display string becomes the title, and there is no second line
        {"ref_id": "geocode:BBB", "name": "12 Xuân Thủy, Dịch Vọng Hậu, Cầu Giấy, Hà Nội", "address": ""},
    ]
    params = dict(seen[0].url.params)
    assert seen[0].url.path == "/api/autocomplete/v4"
    assert params["apikey"] == KEY
    assert params["text"] == "cầu giấy"
    assert params["focus"] == "21.0285,105.8542"  # biased to Hanoi, not restricted to it
    assert params["display_type"] == "6"


async def test_suggest_below_two_characters_returns_nothing_and_calls_nobody(client, monkeypatch):
    seen = _mock_vietmap(monkeypatch, lambda r: httpx.Response(200, json=AUTOCOMPLETE_BODY))

    for q in ("", " ", "a", " a "):
        res = await client.get("/api/geo/suggest", params={"q": q})
        assert res.status_code == 200
        assert res.json() == []
    assert seen == []


async def test_same_text_is_answered_from_the_cache(client, monkeypatch):
    seen = _mock_vietmap(monkeypatch, lambda r: httpx.Response(200, json=AUTOCOMPLETE_BODY))

    first = await client.get("/api/geo/suggest", params={"q": "Cầu  Giấy"})
    again = await client.get("/api/geo/suggest", params={"q": "cầu giấy "})  # spaces and case do not matter

    assert first.json() == again.json()
    assert len(seen) == 1


async def test_suggest_without_a_key_is_503_and_calls_nobody(client, monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(vietmap_api_key=""))
    seen = _mock_vietmap(monkeypatch, lambda r: httpx.Response(200, json=[]))

    res = await client.get("/api/geo/suggest", params={"q": "hoàn kiếm"})

    assert res.status_code == 503
    assert res.json()["error"]["code"] == "geo_not_configured"
    assert seen == []


@pytest.mark.parametrize("failure", ["http_500", "network", "not_json"])
async def test_vietmap_failure_is_503_and_never_leaks_the_key(client, monkeypatch, failure):
    def handler(request: httpx.Request) -> httpx.Response:
        if failure == "network":
            raise httpx.ConnectError("boom", request=request)
        if failure == "not_json":
            return httpx.Response(200, content=b"<html>oops</html>")
        return httpx.Response(500)

    _mock_vietmap(monkeypatch, handler)

    res = await client.get("/api/geo/suggest", params={"q": "tây hồ"})

    assert res.status_code == 503
    assert res.json()["error"]["code"] == "geo_unavailable"
    assert KEY not in res.text


async def test_a_failed_search_is_not_cached(client, monkeypatch):
    answers = iter([httpx.Response(500), httpx.Response(200, json=AUTOCOMPLETE_BODY)])
    seen = _mock_vietmap(monkeypatch, lambda r: next(answers))

    assert (await client.get("/api/geo/suggest", params={"q": "tây hồ"})).status_code == 503
    assert (await client.get("/api/geo/suggest", params={"q": "tây hồ"})).status_code == 200
    assert len(seen) == 2


async def test_resolve_returns_the_coordinates_and_passes_the_ref_id_unchanged(client, monkeypatch):
    seen = _mock_vietmap(
        monkeypatch, lambda r: httpx.Response(200, json={"lat": 21.0333, "lng": 105.7914, "display": "x"})
    )

    res = await client.get("/api/geo/resolve", params={"ref_id": "auto:Zm9v/bar+baz=="})

    assert res.status_code == 200
    assert res.json() == {"lat": 21.0333, "lng": 105.7914}
    params = dict(seen[0].url.params)
    assert seen[0].url.path == "/api/place/v4"
    assert params["refid"] == "auto:Zm9v/bar+baz=="
    assert params["apikey"] == KEY


@pytest.mark.parametrize(
    "body",
    [{}, {"lat": None, "lng": None}, {"lat": "21.0", "lng": "105.8"}, {"lat": 95.0, "lng": 105.8}, []],
)
async def test_resolve_without_usable_coordinates_is_404(client, monkeypatch, body):
    _mock_vietmap(monkeypatch, lambda r: httpx.Response(200, json=body))

    res = await client.get("/api/geo/resolve", params={"ref_id": "auto:gone"})

    assert res.status_code == 404
    assert res.json()["error"]["code"] == "not_found"


async def test_resolve_needs_a_ref_id(client):
    res = await client.get("/api/geo/resolve")
    assert res.status_code == 422


async def test_resolve_without_a_key_is_503(client, monkeypatch):
    monkeypatch.setattr(service, "get_settings", lambda: SimpleNamespace(vietmap_api_key=""))

    res = await client.get("/api/geo/resolve", params={"ref_id": "auto:x"})

    assert res.status_code == 503
    assert res.json()["error"]["code"] == "geo_not_configured"
