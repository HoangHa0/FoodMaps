"""MatchCandidateProvider.find_candidates (the CandidateProvider contract used by M5 and M6)."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.match import service
from app.shared.contracts import GeoPoint, MatchCriteria, PlaceCandidate
from tests.match.conftest import ORIGIN, query_vector

pytestmark = pytest.mark.db


@pytest.fixture(autouse=True)
def _no_model(monkeypatch):
    async def fake_encode(_mood: str) -> list[float]:
        return query_vector()

    monkeypatch.setattr(service, "_encode_mood", fake_encode)


async def test_find_candidates_keeps_the_team_name_of_each_place(engine, seed_place):
    best = await seed_place("Quan Tot", cosine=0.9, meters_north=50)
    other = await seed_place("Quan Kha", cosine=0.6, meters_north=80)
    criteria = MatchCriteria(mood="yên tĩnh", origin=GeoPoint(lat=ORIGIN[0], lng=ORIGIN[1]), radius_m=500)

    async with AsyncSession(engine) as db:
        cands = await service.MatchCandidateProvider(db).find_candidates(criteria, k=2)

    assert all(type(c) is PlaceCandidate for c in cands)  # the contract type, not MatchResult
    assert [(c.place_id, c.name) for c in cands] == [(best, "Quan Tot"), (other, "Quan Kha")]
