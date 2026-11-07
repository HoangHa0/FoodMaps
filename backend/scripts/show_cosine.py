"""Print the RAW cosine similarity between a query and every place (no weights, no filters).

Use it to set SIM_LOW / SIM_HIGH of the model profile in app/modules/match/embedding.py:
  SIM_LOW  ~ cosine of places that clearly do NOT fit    SIM_HIGH ~ cosine of places that clearly fit
If many places are above SIM_HIGH, the semantic score saturates at 1.0 and stops telling them apart.

cd backend
uv run python scripts/show_cosine.py "quán cà phê phù hợp để đi date" "quán ăn chay thanh đạm"
uv run python scripts/show_cosine.py --codes Q020,Q030 "quán ăn chay thanh đạm"   # + rank of Q020, Q030
"""

import argparse
import asyncio
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


async def main(queries: list[str], codes: list[str]) -> None:
    from sqlalchemy import select

    from app.core.db import SessionLocal, engine
    from app.modules.match.embedding import EMBED_MODEL, SIM_HIGH, SIM_LOW, encode_queries
    from app.modules.match.models import Place, PlaceEmbedding

    print(f"model {EMBED_MODEL} | SIM_LOW {SIM_LOW} | SIM_HIGH {SIM_HIGH}")
    try:
        async with SessionLocal() as db:
            for query, vec in zip(queries, encode_queries(queries), strict=True):
                sim = (1 - PlaceEmbedding.embedding.cosine_distance(vec)).label("sim")
                rows = (
                    await db.execute(
                        select(Place.place_code, Place.manual_name, sim)
                        .join(PlaceEmbedding, PlaceEmbedding.place_id == Place.place_id)
                        .where(PlaceEmbedding.model_name == EMBED_MODEL)
                        .order_by(sim.desc())
                    )
                ).all()
                values = [float(r.sim) for r in rows]
                above = sum(1 for v in values if v >= SIM_HIGH)
                print(f"\n== {query}")
                print(
                    f"min {min(values):.3f} | median {statistics.median(values):.3f} | "
                    f"max {max(values):.3f} | places >= SIM_HIGH: {above}/{len(values)}"
                )
                for r in rows[:8]:
                    print(f"  {float(r.sim):.3f} {r.place_code} {r.manual_name}")
                print("  ...")
                for r in rows[-3:]:
                    print(f"  {float(r.sim):.3f} {r.place_code} {r.manual_name}")
                for rank, r in enumerate(rows, 1):
                    if r.place_code in codes:
                        print(
                            f"  >> rank {rank}/{len(rows)}: {float(r.sim):.3f} {r.place_code} {r.manual_name}"
                        )
    finally:
        await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("queries", nargs="+")
    ap.add_argument("--codes", default="", help="comma separated place codes whose rank to print")
    a = ap.parse_args()
    asyncio.run(main(a.queries, [c.strip() for c in a.codes.split(",") if c.strip()]))
