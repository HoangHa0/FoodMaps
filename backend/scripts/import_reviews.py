"""Import reviews from the group's internal Google Form sheet into the reviews table.

Run this AFTER importing places (the place_code -> place_id mapping must already exist in the database)

cd backend
uv run python scripts/import_reviews.py ../data/raw/reviews.csv --dry-run
uv run python scripts/import_reviews.py ../data/raw/reviews.csv
"""

import argparse
import asyncio
import csv
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # để import được `app`

# ----------------------------------------------------------------------------------------------
# CONFIGURATION: Google Form sheet column names.
# ----------------------------------------------------------------------------------------------
TIMESTAMP_HEADERS = ["Timestamp", "Dấu thời gian"]

PLACE_HEADER = "Bạn muốn đánh giá địa điểm nào?"

TEXT_COLUMNS = {
    "Đánh giá độ đông giờ cao điểm": "crowd_level",
    "Nhận xét thêm về địa điểm (1 câu thôi cũng được)": "comment",
}
TAG_COLUMNS = {
    "Bạn thấy địa điểm này thuộc loại hình nào? (Tối đa 2 mục)": "categories",
    "Bạn thấy địa điểm này phù hợp với việc gì?": "suitable_for",
    "Bạn thấy không khí của địa điểm này thế nào?": "atmosphere",
    "Đánh giá tiện ích của địa điểm": "facilities",
    "Những điểm cộng của địa điểm": "pros",
    "Những điểm trừ của địa điểm": "cons",
    "Món ở địa điểm này thuộc kiểu nào? (Tối đa 8 mục)": "food_types",
}

IGNORED_TAGS = {"cons": {"không có"}}

LIST_COLUMNS = {
    "Món bạn nghĩ nên thử khi tới quán (cách nhau bằng dấu phẩy)": "recommended_dishes",
}
SCORE_COLUMNS = {
    "Điểm món ăn/đồ uống": "score_food",
    "Điểm không gian": "score_space",
    "Giá cả có xứng đáng với chất lượng không?": "score_price",
    "Điểm phục vụ": "score_service",
}
PRICE_HEADER = "Bạn chi khoảng bao nhiêu cho 1 người?"

SCORE_MIN, SCORE_MAX = 1, 5  


DATE_FORMATS = ["%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M"]
TZ = timezone(timedelta(hours=7))  # giờ Việt Nam

UPSERT_FIELDS = [
    "place_id",
    "created_at",
    "score_food",
    "score_space",
    "score_price",
    "score_service",
    "categories",
    "suitable_for",
    "atmosphere",
    "facilities",
    "food_types",
    "pros",
    "cons",
    "recommended_dishes",
    "crowd_level",
    "price_per_person",
    "comment",
]  


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", nfc(s).strip()).casefold()


def clean(s: str) -> str | None:
    s = nfc(s).strip()
    return s or None


def split_tags(raw: str, smart: bool = True) -> list[str]:
    """'Học bài, làm việc, Chụp ảnh' -> ['Học bài, làm việc', 'Chụp ảnh'] (bỏ trùng, giữ thứ tự)."""
    out: list[str] = []
    for part in nfc(raw).split(","):
        part = part.strip()
        if not part:
            continue
        if smart and out and part[0].islower():  
            out[-1] = f"{out[-1]}, {part}"
        elif part not in out:
            out.append(part)
    return out


def parse_place_code(cells: list[str]) -> str:
    """Lấy giá trị không rỗng trong 3 cột địa điểm: 'Q001 | Tiny Cafe - Revolution' -> 'Q001'."""
    values = {c.strip() for c in cells if c.strip()}
    if not values:
        raise ValueError("không chọn địa điểm nào")
    if len(values) > 1:
        raise ValueError(f"có {len(values)} địa điểm khác nhau trong cùng 1 dòng: {sorted(values)}")
    code = values.pop().split("|")[0].strip()
    if not code:
        raise ValueError("địa điểm không có mã quán (định dạng mong đợi: 'Q001 | Tên quán')")
    return code


def parse_timestamp(raw: str, formats: list[str]) -> datetime:
    raw = raw.strip()
    if not raw:
        raise ValueError("thiếu timestamp")
    for fmt in formats:
        try:
            return datetime.strptime(raw, fmt).replace(tzinfo=TZ)
        except ValueError:
            continue
    try:  # dự phòng: dạng ISO
        dt = datetime.fromisoformat(raw)
        return dt if dt.tzinfo else dt.replace(tzinfo=TZ)
    except ValueError:
        raise ValueError(f"timestamp {raw!r} không khớp định dạng {formats} (dùng --date-format)") from None


def parse_score(raw: str, field: str) -> int:
    try:
        v = int(float(raw.strip().replace(",", ".")))
    except ValueError:
        raise ValueError(f"{field} không phải số: {raw!r}") from None
    if not SCORE_MIN <= v <= SCORE_MAX:
        raise ValueError(f"{field}={v} ngoài khoảng {SCORE_MIN}..{SCORE_MAX}")
    return v


_PRICE_TOKEN = re.compile(r"(\d+(?:[.,]\d+)*)\s*(k|tr|triệu|nghìn|ngàn)?", re.IGNORECASE)
_MULT = {"k": 1_000, "nghìn": 1_000, "ngàn": 1_000, "tr": 1_000_000, "triệu": 1_000_000, "m": 1_000_000}


def parse_price(raw: str) -> int | None:
    """'55' -> 55000 (số trần < 1000 hiểu là nghìn đồng) | '50k' -> 50000 | '50.000đ' -> 50000
    | '50-70k' -> 60000 | '1,5tr' -> 1500000. Không đọc được -> None."""
    tokens = _PRICE_TOKEN.findall((raw or "").lower())
    if not tokens:
        return None
    last_mult = next((_MULT[s] for _, s in reversed(tokens) if s), None)
    values = []
    for num, suffix in tokens:
        if suffix:
            v = float(num.replace(",", ".")) * _MULT[suffix]
        else:
            v = float(re.sub(r"[.,]", "", num))
            if v < 1000:
                v *= last_mult or 1000
        values.append(v)
    return int(sum(values) / len(values))


def find_columns(header: list[str]) -> dict:
    index: dict[str, list[int]] = {}
    for i, h in enumerate(header):
        index.setdefault(norm(h), []).append(i)

    def first(name: str) -> int | None:
        hits = index.get(norm(name))
        return hits[0] if hits else None

    ts = next((first(n) for n in TIMESTAMP_HEADERS if first(n) is not None), None)
    place_idx = index.get(norm(PLACE_HEADER), [])

    wanted = [*TEXT_COLUMNS, *TAG_COLUMNS, *LIST_COLUMNS, *SCORE_COLUMNS, PRICE_HEADER]
    missing = [h for h in wanted if first(h) is None]
    if ts is None:
        missing.insert(0, " / ".join(TIMESTAMP_HEADERS))
    if not place_idx:
        missing.insert(0, PLACE_HEADER)
    if missing:
        shown = [re.sub(r"\s+", " ", h).strip() for h in header]
        raise SystemExit(f"CSV thiếu cột: {missing}\nCác cột hiện có: {shown}")

    return {
        "ts": ts,
        "places": place_idx,
        "text": {first(h): f for h, f in TEXT_COLUMNS.items()},
        "tags": {first(h): f for h, f in TAG_COLUMNS.items()},
        "list": {first(h): f for h, f in LIST_COLUMNS.items()},
        "score": {first(h): f for h, f in SCORE_COLUMNS.items()},
        "price": first(PRICE_HEADER),
    }


def parse_row(cells: list[str], cols: dict, formats: list[str]) -> tuple[dict, list[str]]:
    """Làm sạch 1 dòng. Raise ValueError nếu không hợp lệ; trả thêm danh sách cảnh báo (không chặn)."""

    def cell(i: int) -> str:
        return cells[i] if i < len(cells) else ""

    warnings: list[str] = []
    place_code = parse_place_code([cell(i) for i in cols["places"]])
    created_at = parse_timestamp(cell(cols["ts"]), formats)

    row: dict = {
        "place_code": place_code,  
        "import_key": f"{created_at.isoformat()}|{place_code}",
        "created_at": created_at,
        "source": "sheet",
        "user_id": None,
    }
    for i, field in cols["score"].items():
        row[field] = parse_score(cell(i), field)
    for i, field in cols["tags"].items():
        ignored = IGNORED_TAGS.get(field, set())
        row[field] = [t for t in split_tags(cell(i)) if norm(t) not in ignored]
    for i, field in cols["list"].items():
        row[field] = split_tags(cell(i), smart=False)
    for i, field in cols["text"].items():
        row[field] = clean(cell(i))

    raw_price = cell(cols["price"]).strip()
    row["price_per_person"] = parse_price(raw_price)
    if raw_price and row["price_per_person"] is None:
        warnings.append(f"không đọc được giá {raw_price!r} -> để trống")
    elif row["price_per_person"] is not None and not 5_000 <= row["price_per_person"] <= 2_000_000:
        warnings.append(f"giá {row['price_per_person']}đ (từ {raw_price!r}) bất thường, kiểm tra lại")
    return row, warnings


def load_csv(path: Path, formats: list[str]) -> tuple[list[dict], list[str], list[str]]:
    rows, errors, warnings = [], [], []
    seen: dict[str, list[tuple]] = {} 

    with path.open(encoding="utf-8-sig", newline="") as f:  
        reader = csv.reader(f)
        header = next(reader, None)
        if header is None:
            raise SystemExit("CSV rỗng")
        cols = find_columns(header)

        for line, cells in enumerate(reader, start=2):
            if not any(c.strip() for c in cells):
                continue  
            try:
                row, warns = parse_row(cells, cols, formats)
            except ValueError as e:
                errors.append(f"dòng {line}: {e}")
                continue
            warnings += [f"dòng {line}: {w}" for w in warns]

            base, sig = row["import_key"], tuple(c.strip() for c in cells)
            if base in seen:
                if sig in seen[base]:
                    warnings.append(f"dòng {line}: trùng hệt một dòng trước ({base}) -> bỏ qua")
                    continue
                row["import_key"] = f"{base}#{len(seen[base]) + 1}"
                seen[base].append(sig)
            else:
                seen[base] = [sig]
            rows.append(row)

    return rows, errors, warnings


async def resolve_place_ids(codes: set[str]) -> dict[str, str]:
    """place_code -> place_id (đọc từ bảng places, chỉ đọc)."""
    from sqlalchemy import select

    from app.core.db import SessionLocal
    from app.modules.match.models import Place

    async with SessionLocal() as session:
        result = await session.execute(
            select(Place.place_code, Place.place_id).where(Place.place_code.in_(codes))
        )
        return {code: pid for code, pid in result.all()}


async def upsert(rows: list[dict]) -> None:
    from sqlalchemy import func
    from sqlalchemy.dialects.postgresql import insert

    from app.core.db import SessionLocal
    from app.modules.reviews.models import Review

    async with SessionLocal() as session:
        for start in range(0, len(rows), 500):  
            stmt = insert(Review).values(rows[start : start + 500])
            stmt = stmt.on_conflict_do_update(
                index_elements=[Review.import_key],
                set_={**{c: stmt.excluded[c] for c in UPSERT_FIELDS}, "updated_at": func.now()},
            )
            await session.execute(stmt)
        await session.commit()


async def run(rows: list[dict], dry_run: bool) -> list[str]:
    from app.core.db import engine

    try:
        code_to_id = await resolve_place_ids({r["place_code"] for r in rows})
        errors = []
        for r in rows:
            pid = code_to_id.get(r["place_code"])
            if pid is None:
                errors.append(f"không có quán {r['place_code']} trong bảng places ({r['import_key']})")
            else:
                r["place_id"] = pid
        if errors or dry_run:
            return errors
        db_rows = [{k: v for k, v in r.items() if k != "place_code"} for r in rows]
        await upsert(db_rows)
        return []
    finally:
        await engine.dispose()


def print_summary(rows: list[dict]) -> None:
    per_place = Counter(r["place_code"] for r in rows)
    print(
        f"Số quán có review: {len(per_place)} | ít nhất {min(per_place.values())}, "
        f"nhiều nhất {max(per_place.values())} review/quán"
    )

    for field in [*TAG_COLUMNS.values(), *LIST_COLUMNS.values()]:
        counts = Counter(v for r in rows for v in r[field])
        top = " | ".join(f"{k} ({n})" for k, n in counts.most_common(12))
        print(f"  {field}: {top or '(trống)'}")
    prices = sorted(r["price_per_person"] for r in rows if r["price_per_person"])
    if prices:
        print(
            f"  price_per_person: {len(prices)}/{len(rows)} review có giá, {prices[0]:,}đ .. {prices[-1]:,}đ"
        )
    no_text = sum(1 for r in rows if not (r["comment"] or r["pros"] or r["cons"]))
    print(f"Review không có chữ/tag nào (comment, pros, cons đều trống): {no_text}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("csv_path", type=Path)
    ap.add_argument("--dry-run", action="store_true", help="chỉ kiểm tra (có đọc DB), không ghi")
    ap.add_argument("--date-format", help="định dạng cột timestamp, mặc định thử m/d/Y H:M[:S]")
    args = ap.parse_args()

    rows, errors, warnings = load_csv(args.csv_path, [args.date_format] if args.date_format else DATE_FORMATS)
    print(f"Hợp lệ: {len(rows)} review | Lỗi: {len(errors)} | Cảnh báo: {len(warnings)}")
    for w in warnings:
        print("  !", w)
    for e in errors:
        print("  ✗", e)
    if errors:
        raise SystemExit("Sửa lỗi trong sheet rồi export lại (không ghi gì vào DB).")
    if not rows:
        raise SystemExit("Không có dòng nào để import.")

    print_summary(rows)

    db_errors = asyncio.run(run(rows, args.dry_run))
    if db_errors:
        for e in db_errors:
            print("  ✗", e)
        raise SystemExit("Có place_code chưa import vào bảng places. Chạy import_places.py trước.")

    print("Dry-run: không ghi DB." if args.dry_run else f"Đã ghi {len(rows)} review vào bảng reviews.")


if __name__ == "__main__":
    main()
