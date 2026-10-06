"""Compute one embedding per place OFFLINE and store it in `place_embeddings`.

The web server never encodes places; it only encodes the user's query. Run this script again
whenever reviews or the model change. It is safe to re-run: existing rows are updated.

cd backend
uv sync --extra ai                                  # once: installs sentence-transformers (torch)
uv run python scripts/compute_embeddings.py --dry-run
uv run python scripts/compute_embeddings.py

--dry-run builds and prints the texts without loading the model or writing to the database,
so it also works without the `ai` extra.
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `app`

BATCH = 64
PREVIEW_COUNT = 3
PREVIEW_CHARS = 700


async def run(dry_run: bool) -> None:
    from sqlalchemy import func, select
    from sqlalchemy.dialects.postgresql import insert

    from app.core.db import SessionLocal, engine
    from app.modules.match.embedding import EMBED_DIM, EMBED_MODEL
    from app.modules.match.models import Place, PlaceEmbedding
    from app.modules.match.text_builder import build_place_text
    from app.modules.reviews.models import Review

    try:
        async with SessionLocal() as session:
            places = (await session.execute(select(Place).order_by(Place.place_code))).scalars().all()
            if not places:
                raise SystemExit("Bảng places đang trống: import places trước (scripts/import_places.py).")
            reviews = (
                (await session.execute(select(Review).where(Review.status == "visible"))).scalars().all()
            )

            by_place: dict[str, list[Review]] = defaultdict(list)
            for review in reviews:
                by_place[review.place_id].append(review)

            texts = [build_place_text(p.manual_name, p.category, by_place[p.place_id]) for p in places]

            n_reviewed = sum(1 for p in places if by_place[p.place_id])
            print(f"{len(places)} quán | {n_reviewed} có review")
            for p in places:
                if not by_place[p.place_id]:
                    print(
                        f"  ! {p.place_code} {p.manual_name}: chưa có review, vector chỉ dựa vào tên + loại"
                    )

            if dry_run:
                for p, text in list(zip(places, texts, strict=True))[:PREVIEW_COUNT]:
                    print(f"--- {p.place_code} ({len(text)} ký tự)\n{text[:PREVIEW_CHARS]}")
                print("Dry-run: không tải model, không ghi DB.")
                return

            try:
                from app.modules.match.embedding import encode_passages

                vectors: list[list[float]] = []
                for start in range(0, len(texts), BATCH):
                    vectors += encode_passages(texts[start : start + BATCH])
            except ImportError:
                raise SystemExit(
                    "Thiếu sentence-transformers. Chạy: cd backend && uv sync --extra ai"
                ) from None

            bad = [len(v) for v in vectors if len(v) != EMBED_DIM]
            if bad:
                raise SystemExit(
                    f"Model trả vector {bad[0]} chiều nhưng bảng cần {EMBED_DIM}: "
                    "đã đổi model mà chưa đổi migration?"
                )

            rows = [
                {"place_id": p.place_id, "source_text": t, "embedding": v, "model_name": EMBED_MODEL}
                for p, t, v in zip(places, texts, vectors, strict=True)
            ]
            stmt = insert(PlaceEmbedding).values(rows)
            stmt = stmt.on_conflict_do_update(
                index_elements=[PlaceEmbedding.place_id],
                set_={
                    "source_text": stmt.excluded.source_text,
                    "embedding": stmt.excluded.embedding,
                    "model_name": stmt.excluded.model_name,
                    "updated_at": func.now(),
                },
            )
            await session.execute(stmt)
            await session.commit()
            print(f"Đã ghi {len(rows)} embedding (model {EMBED_MODEL}, {EMBED_DIM} chiều).")
    finally:
        await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true", help="chỉ dựng và in văn bản, không tải model/ghi DB")
    args = ap.parse_args()
    asyncio.run(run(args.dry_run))


if __name__ == "__main__":
    main()
