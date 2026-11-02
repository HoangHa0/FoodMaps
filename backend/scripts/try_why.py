"""Try "Why this place?" against your real database and print the raw numbers.

cd backend
uv sync --extra ai

uv run python scripts/try_why.py Q001 "quán yên tĩnh để học bài"
uv run python scripts/try_why.py Q001 "có chỗ gửi xe máy"

For ONE place it prints every stored bullet (`place_highlights`) with its cosine similarity to the
text, and marks the ones the API would show. Look at the `cos` column to tune WHY_MIN_SIMILARITY in
app/modules/match/why.py: bullets that really fit the text should be above the line, unrelated ones
below it. Run it with a few different searches before changing the constant (DECISIONS D14).
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `app` can be imported


async def main() -> None:
    from sqlalchemy import select

    from app.core.db import SessionLocal, engine
    from app.modules.match.embedding import encode_queries
    from app.modules.match.models import Place
    from app.modules.match.service import _highlights_for
    from app.modules.match.why import WHY_MIN_SIMILARITY, pick_points

    ap = argparse.ArgumentParser()
    ap.add_argument("place_code", help="place_code, e.g. Q001")
    ap.add_argument("text", help="what the user would type")
    args = ap.parse_args()

    try:
        async with SessionLocal() as db:
            place = (
                await db.execute(select(Place).where(Place.place_code == args.place_code))
            ).scalar_one_or_none()
            if place is None:
                raise SystemExit(f"Không có quán {args.place_code}")
            try:
                vector = encode_queries([args.text])[0]
            except ImportError:
                raise SystemExit(
                    "Thiếu sentence-transformers. Chạy: cd backend && uv sync --extra ai"
                ) from None
            rows = await _highlights_for(db, place.place_id, vector)
    finally:
        await engine.dispose()

    if not rows:
        raise SystemExit("Quán này chưa có highlight: chạy scripts/generate_insights.py trước.")
    shown = {p.text: p.matched for p in pick_points(rows)}
    print(f'{place.place_code} {place.manual_name} | "{args.text}" | ngưỡng {WHY_MIN_SIMILARITY}')
    print(f"{'cos':>6} {'support':>7}  {'hiển thị':<10} bullet")
    for r in sorted(rows, key=lambda r: -r.similarity):
        state = "-" if r.text not in shown else ("khớp" if shown[r.text] else "bổ sung")
        print(f"{r.similarity:6.3f} {r.support:7d}  {state:<10} {r.text}")


if __name__ == "__main__":
    asyncio.run(main())
