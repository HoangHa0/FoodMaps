"""Generate the AI insights of every place OFFLINE with Groq and store them in `place_insights`.

Up to two Groq calls per place, with DIFFERENT inputs:

  main call     every visible review (website + internal sheet) -> pros/cons, answers to the preset
                questions, short highlight bullets (each gets an embedding, stored in `place_highlights`).
                The highlights are what "Why this place" uses.
  summary call  WEBSITE reviews only (`source = 'user'`) -> the AI summary. The internal sheet data is
                not public, so it never goes into this prompt. A place without website reviews has
                no summary (its other insights are still made).

The most mentioned dishes are counted by plain code, not by the LLM.
Nothing here runs while users browse the site.

    cd backend
    uv sync --extra ai                                     # once: sentence-transformers for the highlights
    # put GROQ_API_KEY=... in backend/.env
    uv run python scripts/generate_insights.py --dry-run   # what would run, no network, no model, no writes
    uv run python scripts/generate_insights.py --place Q001   # try ONE place first, read the result
    uv run python scripts/generate_insights.py --limit 5      # then a few
    uv run python scripts/generate_insights.py                # everything that is new or changed

Saving quota: a place whose reviews changed ("stale") is NOT redone straight away. It is redone only
when at least --min-changes (default 3) visible reviews were created or edited since its insight was
generated, or when the insight is at least --stale-days (default 14) old. Otherwise it is "deferred":
no Groq call, the old insight stays. A place with no insight yet is always made; --force ignores the
policy; `--min-changes 0` turns it off (see refresh_policy.py and DECISIONS D13).

Resuming: the database is the progress record. Each call has a fingerprint of its input reviews
(`input_hash` for the main call, `summary_hash` for the summary). A call is skipped when the stored
fingerprint equals the current one, so after the daily quota runs out (the script stops by itself,
finished places are already saved) just run it again the next day. A new, edited or deleted review
changes the fingerprint, so exactly the affected calls are redone: a new SHEET review redoes only the
main call, a new WEBSITE review redoes both. Use --force to redo everything (e.g. after --model).

Limits of the Groq free tier (DECISIONS D13): ~8K tokens per minute for one request, 200K per day.
The script waits between calls to respect the per-minute limit, so expect about one place per minute.
"""

import argparse
import asyncio
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # so `app` can be imported

from app.modules.match.insights import MAX_REVIEW_CHARS  # noqa: E402  (pure, no database / model)
from app.modules.match.refresh_policy import DEFAULT_MIN_CHANGES, DEFAULT_STALE_DAYS  # noqa: E402

MAX_OUTPUT_TOKENS = 2_000  # main call: JSON answer + the model's short hidden reasoning
SUMMARY_MAX_OUTPUT_TOKENS = 800  # summary call: one short paragraph
INVALID_ANSWER_ATTEMPTS = 2  # a malformed answer is retried once, then the place is skipped
PREVIEW_CHARS = 1_200
DEFAULT_MIN_REVIEWS = 1


async def ask(groq, system: str, user: str, *, estimated: int, max_tokens: int, parse):
    """One Groq call whose answer must pass `parse`. A malformed answer is retried once.

    Returns (parsed or None, tokens used). Quota/API errors propagate to the caller.
    """
    from app.modules.match.insights import InvalidInsights

    tokens = 0
    for attempt in range(1, INVALID_ANSWER_ATTEMPTS + 1):
        reply = await groq.chat_json(system, user, max_tokens=max_tokens, estimated_prompt=estimated)
        tokens += reply.total_tokens
        try:
            return parse(reply.content), tokens
        except InvalidInsights as e:
            print(f"      ! câu trả lời không dùng được ({e}), lần {attempt}")
    return None, tokens


async def run(args: argparse.Namespace) -> int:
    from datetime import UTC, datetime

    from sqlalchemy import select

    from app.core.config import get_settings
    from app.core.db import SessionLocal, engine
    from app.modules.match.embedding import EMBED_DIM, EMBED_MODEL
    from app.modules.match.groq_client import GroqClient, GroqError, GroqQuotaExhausted
    from app.modules.match.insights import (
        STATUS_FRESH,
        STATUS_TOO_FEW,
        TODO_STATUSES,
        build_messages,
        build_summary_messages,
        estimate_tokens,
        fingerprint,
        format_reviews,
        parse_insights,
        parse_summary,
        plan_status,
        top_dishes,
        web_reviews,
    )
    from app.modules.match.insights_store import (
        clear_summary,
        refresh_top_dishes,
        remove_insight,
        save_insights,
        save_summary,
    )
    from app.modules.match.models import Place, PlaceInsight
    from app.modules.match.refresh_policy import STATUS_DEFERRED, apply_policy
    from app.modules.reviews.models import Review

    settings = get_settings()
    model = args.model or settings.groq_model
    encode = None

    if not args.dry_run:
        if not settings.groq_api_key:
            raise SystemExit("Thiếu GROQ_API_KEY: thêm vào backend/.env (hoặc chạy với --dry-run).")
        try:  # fail now, before any quota is spent: the highlights need the embedding model
            from app.modules.match.embedding import encode_passages as encode

            if len(encode(["khởi động"])[0]) != EMBED_DIM:
                raise SystemExit(f"Model embedding không trả vector {EMBED_DIM} chiều: đã đổi model?")
        except ImportError:
            raise SystemExit("Thiếu sentence-transformers. Chạy: cd backend && uv sync --extra ai") from None

    try:
        async with SessionLocal() as session:
            query = select(Place).order_by(Place.place_code)
            if args.place:
                query = query.where(Place.place_code.in_(args.place))
            places = (await session.execute(query)).scalars().all()
            if not places:
                raise SystemExit("Không có quán nào khớp (kiểm tra --place hoặc import places trước).")

            visible = (
                (await session.execute(select(Review).where(Review.status == "visible"))).scalars().all()
            )
            by_place = defaultdict(list)
            for review in visible:
                by_place[review.place_id].append(review)

            stored = {row.place_id: row for row in (await session.execute(select(PlaceInsight))).scalars()}

            # ---- plan: what does each place need? --------------------------------------------
            now = datetime.now(UTC)
            policy = {"min_changes": args.min_changes, "stale_days": args.stale_days}
            work, main_counts, sum_counts = [], defaultdict(int), defaultdict(int)
            dishes_to_refresh, summaries_to_clear, to_remove = [], [], []
            for place in places:
                reviews = by_place[place.place_id]  # every source: input of the MAIN call
                web = web_reviews(reviews)  # input of the SUMMARY call only
                row = stored.get(place.place_id)
                main_hash = fingerprint(reviews)
                summary_hash = fingerprint(web, summary=True)
                main = plan_status(
                    web_review_count=len(reviews),
                    min_reviews=args.min_reviews,
                    current_hash=main_hash,
                    stored_hash=None if row is None else row.input_hash,
                    force=args.force,
                )
                generated_at = None if row is None else row.generated_at
                main = apply_policy(main, reviews=reviews, generated_at=generated_at, now=now, **policy)
                main_counts[main] += 1
                if main == STATUS_TOO_FEW:
                    if row is not None:
                        to_remove.append(place)  # all reviews were deleted: drop the stale insight
                    continue
                summary = plan_status(
                    web_review_count=len(web),
                    min_reviews=1,
                    current_hash=summary_hash,
                    stored_hash=None if row is None else row.summary_hash,
                    force=args.force,
                )
                if main not in TODO_STATUSES:
                    # the main call is not running: the summary follows the same policy (website reviews)
                    summary = apply_policy(summary, reviews=web, generated_at=generated_at, now=now, **policy)
                # else: the main call runs anyway, and the summary call is tiny: redo it if its input changed
                sum_counts[summary] += 1
                dishes = top_dishes(reviews)
                if main in (STATUS_FRESH, STATUS_DEFERRED) and row.top_dishes != dishes:
                    dishes_to_refresh.append((place, dishes))  # counted by code: no LLM needed
                if summary == STATUS_TOO_FEW and row is not None and row.summary is not None:
                    summaries_to_clear.append(place)  # website reviews were deleted
                if main in TODO_STATUSES or summary in TODO_STATUSES:
                    work.append((place, reviews, web, dishes, main, main_hash, summary, summary_hash))

            print(
                f"{len(places)} quán | gọi chính: cần tạo {main_counts['new']}, review đổi "
                f"{main_counts['stale']}, --force {main_counts['forced']}, đã mới {main_counts['fresh']}, "
                f"hoãn (đổi ít, còn mới) {main_counts[STATUS_DEFERRED]}, "
                f"chưa có review {main_counts[STATUS_TOO_FEW]}"
            )
            print(
                f"         | gọi summary (chỉ review web): cần tạo {sum_counts['new']}, review đổi "
                f"{sum_counts['stale']}, --force {sum_counts['forced']}, đã mới {sum_counts['fresh']}, "
                f"hoãn {sum_counts[STATUS_DEFERRED]}, quán không có review web {sum_counts[STATUS_TOO_FEW]}"
            )
            if dishes_to_refresh:
                print(f"{len(dishes_to_refresh)} quán chỉ cần cập nhật 'món nên thử' (không tốn Groq).")
            if to_remove:
                print(f"{len(to_remove)} quán không còn review nào: sẽ xoá insight cũ.")
            if summaries_to_clear:
                print(f"{len(summaries_to_clear)} quán không còn review web: sẽ xoá summary cũ.")

            if args.limit:
                work = work[: args.limit]

            # ---- build the prompts and estimate their size ----------------------------------
            jobs, total_tokens = [], 0
            for place, reviews, web, dishes, main, main_hash, summary, summary_hash in work:
                job = {"place": place, "dishes": dishes, "main": None, "summary": None}
                notes = []
                if main in TODO_STATUSES:
                    text, used = format_reviews(reviews, args.max_input_chars)
                    system, user = build_messages(place.manual_name, place.category, text, used)
                    est = estimate_tokens(system) + estimate_tokens(user)
                    job["main"] = (system, user, used, est, main_hash)
                    total_tokens += est + MAX_OUTPUT_TOKENS
                    notes.append(f"chính [{main}] {used}/{len(reviews)} review ~{est}tk")
                if summary in TODO_STATUSES:
                    text, used = format_reviews(web, args.max_input_chars)
                    system, user = build_summary_messages(place.manual_name, place.category, text, used)
                    est = estimate_tokens(system) + estimate_tokens(user)
                    job["summary"] = (system, user, used, est, summary_hash)
                    total_tokens += est + SUMMARY_MAX_OUTPUT_TOKENS
                    notes.append(f"summary [{summary}] {used}/{len(web)} review web ~{est}tk")
                jobs.append(job)
                print(f"  - {place.place_code} {place.manual_name}: " + " | ".join(notes))

            if args.dry_run:
                first = next((j for j in jobs if j["main"]), None)
                if first:
                    preview = first["main"][1][:PREVIEW_CHARS]
                    print(f"--- tin nhắn gọi chính cho quán đầu tiên ---\n{preview}")
                first = next((j for j in jobs if j["summary"]), None)
                if first:
                    preview = first["summary"][1][:PREVIEW_CHARS]
                    print(f"--- tin nhắn gọi summary (chỉ review web) ---\n{preview}")
                if jobs:
                    print(
                        f"--- ước tính tối đa {total_tokens} token cho {len(jobs)} quán (quota ngày 200K) ---"
                    )
                print("Dry-run: không gọi Groq, không tải model, không ghi DB.")
                return 0

            # ---- cheap, local-only writes ----------------------------------------------------
            for place, dishes in dishes_to_refresh:
                await refresh_top_dishes(session, place.place_id, dishes)
            for place in summaries_to_clear:
                await clear_summary(session, place.place_id)
            for place in to_remove:
                await remove_insight(session, place.place_id)
            await session.commit()

            # ---- the Groq calls --------------------------------------------------------------
            groq = GroqClient(
                settings.groq_api_key,
                model,
                on_wait=lambda seconds, why: print(f"      … {why}: chờ {seconds:.0f}s", flush=True),
            )
            done, failed, tokens_used, stopped_by_quota = 0, [], 0, False
            try:
                for n, job in enumerate(jobs, start=1):
                    place = job["place"]
                    print(f"[{n}/{len(jobs)}] {place.place_code} {place.manual_name}", flush=True)
                    try:
                        row_exists = place.place_id in stored
                        if job["main"]:
                            system, user, used, est, main_hash = job["main"]
                            insights, tokens = await ask(
                                groq, system, user, estimated=est, max_tokens=MAX_OUTPUT_TOKENS,
                                parse=lambda raw, used=used: parse_insights(raw, used),
                            )  # fmt: skip
                            tokens_used += tokens
                            if insights is None:
                                failed.append(place.place_code)
                            else:
                                vectors = (
                                    encode([h.text for h in insights.highlights])
                                    if insights.highlights
                                    else []
                                )
                                await save_insights(
                                    session,
                                    place_id=place.place_id,
                                    insights=insights,
                                    vectors=vectors,
                                    dishes=job["dishes"],
                                    review_count=used,
                                    input_hash=main_hash,
                                    llm_model=model,
                                    embedding_model=EMBED_MODEL,
                                )
                                await session.commit()  # saved now: a later failure or quota stop keeps it
                                row_exists = True
                                answered = sum(1 for a in insights.faq.values() if a)
                                print(
                                    f"      chính ok: {len(insights.highlights)} highlight, "
                                    f"{answered}/{len(insights.faq)} câu hỏi có đáp án, {tokens} token"
                                )
                        if job["summary"] and row_exists:
                            system, user, used, est, summary_hash = job["summary"]
                            summary, tokens = await ask(
                                groq, system, user, estimated=est, max_tokens=SUMMARY_MAX_OUTPUT_TOKENS,
                                parse=parse_summary,
                            )  # fmt: skip
                            tokens_used += tokens
                            if summary is None:
                                failed.append(place.place_code)
                            else:
                                await save_summary(
                                    session,
                                    place_id=place.place_id,
                                    summary=summary,
                                    summary_hash=summary_hash,
                                    web_review_count=used,
                                )
                                await session.commit()
                                print(f"      summary ok ({used} review web), {tokens} token")
                        done += 1
                    except GroqQuotaExhausted as e:
                        print(f"      Hết quota Groq ({e}). Dừng; chạy lại sau để làm tiếp.")
                        stopped_by_quota = True
                        break
                    except GroqError as e:
                        await session.rollback()
                        print(f"      ! lỗi Groq, bỏ qua quán này: {e}")
                        failed.append(place.place_code)
                    except Exception as e:  # keep the run going; the place is retried next time
                        await session.rollback()
                        print(f"      ! lỗi khi lưu, bỏ qua quán này: {type(e).__name__}: {e}")
                        failed.append(place.place_code)
            finally:
                await groq.aclose()

            failed = list(dict.fromkeys(failed))
            left = len(jobs) - done - len(failed)
            print(
                f"Xong: {done} quán xử lý, {len(failed)} lỗi, {tokens_used} token đã dùng"
                + (f", còn {left} quán chưa làm (hết quota)." if stopped_by_quota else ".")
            )
            if failed:
                print("Quán lỗi (chạy lại sẽ thử lại): " + ", ".join(failed))
            return 1 if failed else 0
    finally:
        await engine.dispose()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument(
        "--dry-run", action="store_true", help="chỉ in kế hoạch, không gọi Groq/model, không ghi DB"
    )
    ap.add_argument(
        "--place", action="append", metavar="CODE", help="chỉ quán này (place_code, vd Q001); lặp lại được"
    )
    ap.add_argument("--limit", type=int, default=0, metavar="N", help="tối đa N quán trong lần chạy này")
    ap.add_argument("--force", action="store_true", help="làm lại cả quán đã mới (vd sau khi đổi --model)")
    ap.add_argument("--model", help="ghi đè GROQ_MODEL, vd openai/gpt-oss-120b")
    ap.add_argument(
        "--min-changes",
        type=int,
        default=DEFAULT_MIN_CHANGES,
        metavar="N",
        help=(
            f"quán đã có insight chỉ làm lại khi có ≥ N review mới/sửa "
            f"(mặc định {DEFAULT_MIN_CHANGES}, 0 = tắt)"
        ),
    )
    ap.add_argument(
        "--stale-days",
        type=int,
        default=DEFAULT_STALE_DAYS,
        metavar="D",
        help=f"...hoặc khi insight đã cũ hơn D ngày (mặc định {DEFAULT_STALE_DAYS}; 0 = tắt)",
    )
    ap.add_argument(
        "--min-reviews",
        type=int,
        default=DEFAULT_MIN_REVIEWS,
        metavar="N",
        help=f"số review (mọi nguồn) tối thiểu để tạo insight (mặc định {DEFAULT_MIN_REVIEWS})",
    )
    ap.add_argument(
        "--max-input-chars",
        type=int,
        default=MAX_REVIEW_CHARS,
        metavar="N",
        help=f"giới hạn ký tự review gửi mỗi quán (mặc định {MAX_REVIEW_CHARS})",
    )
    sys.exit(asyncio.run(run(ap.parse_args())))


if __name__ == "__main__":
    main()
