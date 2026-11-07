"""Check search quality on the REAL database with a small golden list.

cd backend
uv sync --extra ai
uv run python scripts/eval_search.py
uv run python scripts/eval_search.py --label minilm_insight   # also append a summary row to eval_results.csv

A query passes when
  - at least one `ok` place is in the top 3, and
  - no `bad_first` place is ranked #1.
Add a line to GOLDEN whenever a search looks wrong. Codes are `places.place_code` (Q001 ...).
Numbers printed at the end (compare RANKS, never `match_score`: each model has its own calibration):
  hit@1  share of queries whose #1 is an ok place        hit@3  same for the top 3
  MRR    mean of 1/rank of the first ok place (top 5)    bad#1  queries where a bad_first place is #1
Exit code 1 when a query fails, so it can be used in a script.
"""

import argparse
import asyncio
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# (query, ok codes, codes that must not be #1)
GOLDEN: list[tuple[str, set[str], set[str]]] = [
    # Every café below has "Học bài, làm việc" in all or most of its reviews (checked in reviews.csv).
    ("quán yên tĩnh học bài", {"Q039", "Q008", "Q038", "Q030", "Q001", "Q018"}, set()),
    ("quán cà phê yên tĩnh học bài", {"Q039", "Q038", "Q008", "Q030", "Q001", "Q018"}, {"Q017"}),
    # Date: Q030 has the Date tag in 4/4 reviews, Q031 in 2/3. LaBoong / Kàffe Cay Xang have none.
    ("quán cà phê phù hợp để đi date", {"Q030", "Q031"}, {"Q017", "Q037"}),
    ("quán ăn chay thanh đạm", {"Q020"}, {"Q010"}),  # Đi Ăn Chay Đi, not Phở 52
    # ---- Added from the tag shares in reviews.csv (places where >= 60% of >= 3 reviews carry the tag).
    # Sanity-check them against the data before trusting a result; widely ticked tags prove little.
    ("quán cà phê đi nhóm đông người", {"Q018", "Q001"}, set()),
    ("quán ăn cho gia đình", {"Q026", "Q027", "Q028", "Q012", "Q014", "Q021"}, set()),
    ("quán ăn nhanh gọn", {"Q002", "Q033", "Q015", "Q029", "Q010"}, set()),  # Q010: Ăn nhanh 2/2 reviews
    (
        "quán ăn bình dân đi một mình",
        {"Q023", "Q019", "Q032", "Q020"},
        set(),
    ),  # Q020: Bình dân 3/3, Ăn một mình 3/3
    ("tiệm bánh mua nhanh", {"Q022", "Q034"}, set()),
    ("quán nướng lẩu", {"Q026"}, set()),
]


async def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", help="append a summary row to eval_results.csv under this name")
    args = ap.parse_args()

    from sqlalchemy import select

    from app.core.db import SessionLocal, engine
    from app.modules.match import service
    from app.modules.match.models import Place
    from app.shared.contracts import MatchCriteria

    failed = 0
    first_ranks: list[int | None] = []
    bad_first_count = 0
    try:
        async with SessionLocal() as db:
            rows = await db.execute(select(Place.place_id, Place.place_code, Place.manual_name))
            info = {pid: (code, name) for pid, code, name in rows}
        for query, ok, bad_first in GOLDEN:
            results = await service.MatchCandidateProvider().search(MatchCriteria(mood=query), 5)
            top = [info.get(r.place_id, ("?", "?")) for r in results]
            codes = [code for code, _ in top]
            rank = next((i for i, c in enumerate(codes, 1) if c in ok), None)
            first_ranks.append(rank)
            is_bad = bool(codes) and codes[0] in bad_first
            bad_first_count += is_bad
            passed = rank is not None and rank <= 3 and not is_bad
            failed += not passed
            print(f"{'OK ' if passed else 'BAD'} {query}")
            for i, (r, (code, name)) in enumerate(zip(results, top, strict=True), 1):
                print(f"      {i}. {r.match_score:.3f} {code} {name}")
        total = len(GOLDEN)
        hit1 = sum(1 for r in first_ranks if r == 1) / total
        hit3 = sum(1 for r in first_ranks if r is not None and r <= 3) / total
        mrr = sum(1 / r for r in first_ranks if r) / total
        print(
            f"\n{total - failed}/{total} passed | hit@1 {hit1:.2f} | hit@3 {hit3:.2f} "
            f"| MRR {mrr:.2f} | bad#1 {bad_first_count}"
        )
        if args.label:
            from app.modules.match.embedding import EMBED_MODEL

            path = Path("eval_results.csv")
            new = not path.exists()
            with path.open("a", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                if new:
                    w.writerow(
                        [
                            "label",
                            "model",
                            "passed",
                            "total",
                            "hit@1",
                            "hit@3",
                            "MRR",
                            "bad#1",
                        ]
                    )
                w.writerow(
                    [
                        args.label,
                        EMBED_MODEL,
                        total - failed,
                        total,
                        f"{hit1:.2f}",
                        f"{hit3:.2f}",
                        f"{mrr:.2f}",
                        bad_first_count,
                    ]
                )
            print(f"-> appended to {path}")
    finally:
        await engine.dispose()
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
