"""Try the places contract on the real data. cd backend && uv run python scripts/try_places.py"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `app`


async def main() -> None:
    from app.core.db import SessionLocal, engine
    from app.shared import places

    async with SessionLocal() as db:
        every = await places.get_all_places(db)
        print("so quan:", len(every))
        first = every[0]
        print("quan dau:", first.place_code, first.name, first.lat, first.lng)

        one = await places.get_place(db, first.place_id)
        print("get_place:", one.name if one else None)
        print(
            "exists:",
            await places.place_exists(db, first.place_id),
            await places.place_exists(db, "khong_co"),
        )

        got = await places.get_places(db, [first.place_id, "khong_co"])
        print("get_places:", list(got))  # chi co 1 id, id la bi bo qua

        near = await places.get_places_near(db, first.lat, first.lng, 2000)
        print(f"trong 2 km quanh {first.name}: {len(near)} quan")
        for n in near[:5]:
            print(f"  {n.distance_m:>5} m  {n.name}")

    await engine.dispose()


asyncio.run(main())
