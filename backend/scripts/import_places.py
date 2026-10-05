"""Import sheet places.csv

    cd backend
    uv run python scripts/import_places.py ../data/raw/places.csv --dry-run
    uv run python scripts/import_places.py ../data/raw/places.csv
"""

import argparse
import asyncio
import csv
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `app`

REQUIRED = [
    "place_code",
    "manual_name",
    "category",
    "place_id",
    "lat",
    "lng",
]

COLUMNS = [
    "place_code",
    "manual_name",
    "category",
    "address",
    "google_maps_url",
    "place_id",
    "lat",
    "lng",
    "tiktok_urls",
]


def parse_urls(raw: str) -> list[str]:
    """Ô có thể chứa nhiều link, ngăn bởi xuống dòng / dấu cách / , / ;"""
    return [
        u for u in re.split(r"[\s,;]+", raw.strip())
        if u.startswith("http")
    ]


def parse_row(row: dict[str, str]) -> dict:
    """Làm sạch 1 dòng CSV.
    Raise ValueError (kèm lý do dễ hiểu) nếu dòng không hợp lệ.
    """
    r = {k: (row.get(k) or "").strip() for k in COLUMNS}

    missing = [k for k in REQUIRED if not r[k]]
    if missing:
        raise ValueError(f"thiếu {', '.join(missing)}")

    try:
        lat = float(r["lat"].replace(",", "."))
        lng = float(r["lng"].replace(",", "."))
    except ValueError:
        raise ValueError(
            f"lat/lng không phải số: {r['lat']!r}, {r['lng']!r}"
        ) from None

    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        raise ValueError(f"lat/lng ngoài phạm vi: {lat}, {lng}")

    return {
        "place_code": r["place_code"],
        "manual_name": r["manual_name"],
        "category": r["category"],
        "address": r["address"] or None,
        "google_maps_url": r["google_maps_url"] or None,
        "place_id": r["place_id"],
        "lat": lat,
        "lng": lng,
        "tiktok_urls": parse_urls(r["tiktok_urls"]),
    }


def load_csv(path: Path) -> tuple[list[dict], list[str]]:
    rows, errors, seen_ids, seen_codes = [], [], set(), set()

    with path.open(
        encoding="utf-8-sig",
        newline="",
    ) as f:  # utf-8-sig: bỏ BOM của Google Sheets
        reader = csv.DictReader(f)

        absent = [
            c for c in COLUMNS
            if c not in (reader.fieldnames or [])
        ]

        if absent:
            raise SystemExit(
                f"CSV thiếu cột: {absent}. "
                f"Các cột hiện có: {reader.fieldnames}"
            )

        for line, raw in enumerate(reader, start=2):
            if not any((v or "").strip() for v in raw.values()):
                continue  # dòng trống

            try:
                row = parse_row(raw)
            except ValueError as e:
                errors.append(f"dòng {line}: {e}")
                continue

            if (
                row["place_id"] in seen_ids
                or row["place_code"] in seen_codes
            ):
                errors.append(
                    f"dòng {line}: trùng place_id hoặc "
                    f"place_code ({row['place_code']})"
                )
                continue

            seen_ids.add(row["place_id"])
            seen_codes.add(row["place_code"])
            rows.append(row)

    return rows, errors


async def upsert(rows: list[dict]) -> None:
    from sqlalchemy import func
    from sqlalchemy.dialects.postgresql import insert

    from app.core.db import SessionLocal, engine
    from app.modules.match.models import Place

    async with SessionLocal() as session:
        stmt = insert(Place).values(rows)

        update_cols = {
            c: stmt.excluded[c]
            for c in COLUMNS
            if c != "place_id"
        }

        stmt = stmt.on_conflict_do_update(
            index_elements=[Place.place_id],
            set_={
                **update_cols,
                "updated_at": func.now(),
            },
        )

        await session.execute(stmt)
        await session.commit()

    await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument(
        "--dry-run",
        action="store_true",
        help="chỉ kiểm tra, không ghi DB",
    )

    args = ap.parse_args()

    rows, errors = load_csv(args.csv_path)

    print(f"Hợp lệ: {len(rows)} quán | Lỗi: {len(errors)}")

    for e in errors:
        print("  ✗", e)

    no_tiktok = sum(
        1 for r in rows
        if not r["tiktok_urls"]
    )

    print(f"Chưa có tiktok_urls: {no_tiktok}")

    if errors:
        raise SystemExit(
            "Sửa lỗi trong sheet rồi export lại "
            "(không ghi gì vào DB)."
        )

    if args.dry_run:
        print("Dry-run: không ghi DB.")
        return

    asyncio.run(upsert(rows))

    print(f"Đã ghi {len(rows)} quán vào bảng places.")


if __name__ == "__main__":
    main()