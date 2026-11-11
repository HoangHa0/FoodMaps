"""geo endpoints, mounted at /api/geo. Both are public: guests can search around another area."""

from typing import Annotated

from fastapi import APIRouter, Query

from app.modules.geo import service
from app.modules.geo.schemas import GeoSuggestionOut
from app.shared.contracts import GeoPoint

router = APIRouter(prefix="/geo", tags=["geo address search"])


@router.get("/suggest", response_model=list[GeoSuggestionOut], responses={503: {}})
async def suggest(q: Annotated[str, Query(max_length=100, description="what the user has typed")]):
    """Up to 10 suggestions for the text typed so far; `[]` below 2 characters (no VietMap call is made).

    503 `geo_not_configured` when the server has no VietMap key, `geo_unavailable` when VietMap fails.
    """
    return await service.suggest(q)


@router.get("/resolve", response_model=GeoPoint, responses={404: {}, 503: {}})
async def resolve(ref_id: Annotated[str, Query(min_length=1, max_length=2048)]):
    """Coordinates of the suggestion the user picked (404 `not_found` when the id is unknown)."""
    return await service.resolve(ref_id)
