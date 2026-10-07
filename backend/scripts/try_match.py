"""Try the Match pipeline against your real database and print the raw numbers.

cd backend
uv sync --extra ai

uv run python scripts/try_match.py "quán yên tĩnh để học bài"

uv run python scripts/try_match.py "đi date lãng mạn" \
    --lat 21.0285 --lng 105.8522 \
    --radius 3000 --max 200000

Look at the `cos` column to tune SIM_LOW / SIM_HIGH in
app/modules/match/scoring.py.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main() -> None:
    from sqlalchemy import select

    from app.core.db import SessionLocal, engine
    from app.modules.match.models import Place
    from app.modules.match.service import MatchCandidateProvider
    from app.shared.contracts import GeoPoint, MatchCriteria

    ap = argparse.ArgumentParser()
    ap.add_argument("mood")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lng", type=float)
    ap.add_argument("--radius", type=int, default=2000)
    ap.add_argument("--min", type=int, dest="price_min")
    ap.add_argument("--max", type=int, dest="price_max")
    ap.add_argument("-k", type=int, default=6)
    a = ap.parse_args()

    origin = GeoPoint(lat=a.lat, lng=a.lng) if a.lat is not None and a.lng is not None else None
    criteria = MatchCriteria(
        mood=a.mood, origin=origin, radius_m=a.radius, price_min=a.price_min, price_max=a.price_max
    )
    try:
        results = await MatchCandidateProvider().search(criteria, a.k)
        async with SessionLocal() as db:
            rows = await db.execute(
                select(Place.place_id, Place.manual_name).where(
                    Place.place_id.in_([r.place_id for r in results])
                )
            )
            names = {pid: name for pid, name in rows}

        if not results:
            print("(không có quán nào khớp)")
        for i, r in enumerate(results, 1):
            dist = "" if r.distance_m is None else f"  ~{r.distance_m} m"
            print(f"{i}. {r.match_score:.3f}  {names.get(r.place_id, '?')}{dist}")
            print(f"   tags: {', '.join(r.tags)}")
            for line in r.reasons:
                print(f"   {line}")
            print(f"   id: {r.place_id}")
    finally:
        await engine.dispose()


asyncio.run(main())
