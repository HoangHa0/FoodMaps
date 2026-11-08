"""geo business logic: VietMap Autocomplete v4 (suggestions) and Place v4 (coordinates of one suggestion).

Why a proxy: VietMap asks integrators to call these APIs from the server, so the key never reaches the
browser, and the answers can be cached here. Nothing is stored in the database.

- Suggestions are biased towards the centre of Hanoi (`focus`): the place data is Hanoi only, but a
  search is never restricted to it, so a typed address elsewhere still resolves.
- Suggestions are cached for a few minutes by their text (the same text gives the same list).
  Coordinates are not cached: VietMap counts every Place call, but it is made only when the user
  picks a suggestion, and its `ref_id` must not be kept.
- The API key is sent only to VietMap. Errors raised from here never contain the request URL.
"""

import time
from collections import OrderedDict

import httpx

from app.core.config import get_settings
from app.core.errors import AppError, not_found
from app.modules.geo.schemas import GeoSuggestionOut
from app.shared.contracts import GeoPoint

AUTOCOMPLETE_URL = "https://maps.vietmap.vn/api/autocomplete/v4"
PLACE_URL = "https://maps.vietmap.vn/api/place/v4"

HANOI_CENTER = GeoPoint(lat=21.0285, lng=105.8542)
MIN_QUERY_LENGTH = 2  # VietMap's advice: no request below 2 characters
DISPLAY_TYPE = "6"  # VietMap's recommended value: the old address format first
REQUEST_TIMEOUT_S = 8.0

CACHE_TTL_S = 300.0
CACHE_MAX_ENTRIES = 500

# Tests replace this with `httpx.MockTransport(...)`; in production it stays None (real network).
_transport: httpx.AsyncBaseTransport | None = None
# normalised text -> (expires_at, suggestions); oldest entry first
_suggest_cache: OrderedDict[str, tuple[float, list[GeoSuggestionOut]]] = OrderedDict()


def _not_configured() -> AppError:
    return AppError(503, "geo_not_configured", "Tính năng tìm địa điểm chưa được bật")


def _unavailable() -> AppError:
    return AppError(503, "geo_unavailable", "Chưa tìm được địa điểm lúc này, thử lại sau nhé")


def _api_key() -> str:
    key = get_settings().vietmap_api_key
    if not key:
        raise _not_configured()
    return key


async def _get_json(url: str, params: dict[str, str]) -> object:
    """GET with the API key added. Any network or HTTP failure becomes `geo_unavailable`.

    `from None` on purpose: httpx's error text contains the URL, and the URL contains the key.
    """
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=_transport) as client:
            response = await client.get(url, params={**params, "apikey": _api_key()})
        response.raise_for_status()
        return response.json()
    except (httpx.HTTPError, ValueError):
        raise _unavailable() from None


def _parse_suggestions(data: object) -> list[GeoSuggestionOut]:
    """Keep the usable items; an item without a `ref_id` or a title is skipped, never an error."""
    if not isinstance(data, list):
        return []
    out: list[GeoSuggestionOut] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        ref_id = item.get("ref_id")
        display = str(item.get("display") or "").strip()
        name = str(item.get("name") or "").strip() or display
        if not isinstance(ref_id, str) or not ref_id or not name:
            continue
        address = str(item.get("address") or "").strip()
        if not address and display != name:
            address = display
        out.append(GeoSuggestionOut(ref_id=ref_id, name=name, address=address))
    return out


async def suggest(text: str) -> list[GeoSuggestionOut]:
    """Up to 10 places and addresses matching what the user has typed so far (empty below 2 characters)."""
    text = " ".join(text.split())
    if len(text) < MIN_QUERY_LENGTH:
        return []

    cache_key = text.casefold()
    now = time.monotonic()
    hit = _suggest_cache.get(cache_key)
    if hit is not None and hit[0] > now:
        return hit[1]

    data = await _get_json(
        AUTOCOMPLETE_URL,
        {"text": text, "focus": f"{HANOI_CENTER.lat},{HANOI_CENTER.lng}", "display_type": DISPLAY_TYPE},
    )
    suggestions = _parse_suggestions(data)

    _suggest_cache[cache_key] = (now + CACHE_TTL_S, suggestions)
    _suggest_cache.move_to_end(cache_key)
    while len(_suggest_cache) > CACHE_MAX_ENTRIES:
        _suggest_cache.popitem(last=False)
    return suggestions


async def resolve(ref_id: str) -> GeoPoint:
    """Coordinates of one suggestion. 404 `not_found` when VietMap returns none for the id."""
    data = await _get_json(PLACE_URL, {"refid": ref_id})
    lat = data.get("lat") if isinstance(data, dict) else None
    lng = data.get("lng") if isinstance(data, dict) else None
    if not isinstance(lat, int | float) or not isinstance(lng, int | float):
        raise not_found("Địa điểm")
    try:
        return GeoPoint(lat=lat, lng=lng)
    except ValueError:  # coordinates outside the valid range: treat as unknown
        raise not_found("Địa điểm") from None
