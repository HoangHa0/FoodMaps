"""Fill places.price_per_person with the MEDIAN of price_per_person across a place's visible reviews.

Run AFTER import_places.py and import_reviews.py (re-run whenever more reviews are imported).

cd backend
uv run python scripts/backfill_place_prices.py --dry-run
uv run python scripts/backfill_place_prices.py

Notes:
- Median (not average), so one mistyped review (e.g. 5,000,000đ) cannot skew a place.
- Places with no review that has a price are left untouched (NULL stays NULL).
- Re-importing places does not erase these values.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `app`

MEDIAN_SQL = """
SELECT r.place_id,
       p.place_code,
       p.price_per_person AS old_price,
       percentile_cont(0.5) WITHIN GROUP (ORDER BY r.price_per_person)::int AS new_price,
       count(*) AS n_prices
FROM reviews r
JOIN places p ON p.place_id = r.place_id
WHERE r.status = 'visible' AND r.price_per_person IS NOT NULL
GROUP BY r.place_id, p.place_code, p.price_per_person
ORDER BY p.place_code
"""

UPDATE_SQL = """
UPDATE places SET price_per_person = :price, updated_at = now() WHERE place_id = :place_id
"""

COVERAGE_SQL = "SELECT count(*) AS total, count(price_per_person) AS with_price FROM places"


async def run(dry_run: bool) -> None:
    from sqlalchemy import text

    from app.core.db import SessionLocal, engine

    try:
        async with SessionLocal() as session:
            rows = (await session.execute(text(MEDIAN_SQL))).mappings().all()
            changed = [r for r in rows if r["old_price"] != r["new_price"]]

            print(f"{len(rows)} quán có ít nhất 1 review kèm giá | {len(changed)} quán sẽ được cập nhật")
            for r in changed:
                old = f"{r['old_price']:,}đ" if r["old_price"] is not None else "(trống)"
                print(
                    f"  {r['place_code']}: {old} -> {r['new_price']:,}đ (median của {r['n_prices']} review)"
                )

            if dry_run:
                print("Dry-run: không ghi DB.")
            else:
                for r in changed:
                    await session.execute(
                        text(UPDATE_SQL), {"price": r["new_price"], "place_id": r["place_id"]}
                    )
                await session.commit()
                print(f"Đã cập nhật {len(changed)} quán.")

            cov = (await session.execute(text(COVERAGE_SQL))).mappings().one()
            print(f"Hiện có giá: {cov['with_price']}/{cov['total']} quán")
    finally:
        await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="chỉ in kết quả, không ghi DB")
    args = ap.parse_args()
    asyncio.run(run(args.dry_run))


if __name__ == "__main__":
    main()
