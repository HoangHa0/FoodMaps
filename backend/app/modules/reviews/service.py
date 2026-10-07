"""reviews business logic. Routers call only these functions.

Other modules must not import this file; expose what they need through app/shared/.

Rules (see DECISIONS D11):
- One live review per (user, place): reviewing again means editing (PUT), never a second row.
- Only the author may edit or delete a review. Reviews imported from the team's form have no
  author (`user_id` NULL), so nobody can change them through the API.
- Reviews imported from the team's form (`source = 'sheet'`) are internal data: they feed Match and
  Review Analysis, but are never listed or reportable through the API.
- The text filter and the report counter only ever set `status = 'flagged'` (soft hide). Setting
  `hidden` is a manual admin decision, and editing a review never un-hides it.
- Rate limit: at most MAX_NEW_REVIEWS new reviews per user per RATE_WINDOW. Editing is not limited.
  Known limit: it counts existing rows, so delete + re-create resets it; that only lets a spammer
  repeat the same places, which the unique constraint already blocks.
- Transactions: `get_db` never commits by itself, so every write path ends with `commit()`.
"""

import uuid
from datetime import timedelta

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError, not_found
from app.modules.auth.models import User
from app.modules.match.models import Place
from app.modules.reviews import analysis, moderation
from app.modules.reviews.models import Review, ReviewReport
from app.modules.reviews.schemas import (
    ReportIn,
    ReportOut,
    ReviewAnalysisOut,
    ReviewBody,
    ReviewIn,
    ReviewListOut,
    ReviewOut,
    ReviewUpdateIn,
)
from app.shared.auth import AuthUser

MAX_NEW_REVIEWS = 5  # new reviews per user ...
RATE_WINDOW = timedelta(minutes=10)  # ... within this window
AUTO_FLAG_REPORTS = 3  # distinct reporters needed to hide a review pending admin decision


# --------------------------------------------------------------------------- helpers


def _out(review: Review, author: str | None, viewer_id: uuid.UUID | None) -> ReviewOut:
    return ReviewOut(
        id=review.id,
        place_id=review.place_id,
        author=author,
        source=review.source,  # type: ignore[arg-type]  # CHECK constraint guarantees user|sheet
        score_food=review.score_food,
        score_space=review.score_space,
        score_price=review.score_price,
        score_service=review.score_service,
        comment=review.comment,
        recommended_dishes=review.recommended_dishes,
        suitable_for=review.suitable_for,
        price_per_person=review.price_per_person,
        status=review.status,  # type: ignore[arg-type]
        is_mine=viewer_id is not None and review.user_id == viewer_id,
        created_at=review.created_at,
        updated_at=review.updated_at,
    )


def _texts_to_check(data: ReviewBody) -> list[str | None]:
    return [data.comment, *data.recommended_dishes, *data.suitable_for]


def _editable_fields(data: ReviewBody) -> dict:
    return {
        "score_food": data.score_food,
        "score_space": data.score_space,
        "score_price": data.score_price,
        "score_service": data.score_service,
        "comment": data.comment,
        "recommended_dishes": data.recommended_dishes,
        "suitable_for": data.suitable_for,
        "price_per_person": data.price_per_person,
    }


def _account_gone() -> AppError:
    # The JWT is only decoded, never checked against the database (D4), so a deleted account can
    # still hold a valid token; the foreign key then fails.
    return AppError(401, "unauthenticated", "Tài khoản không còn tồn tại, hãy đăng nhập lại")


async def _require_place(db: AsyncSession, place_id: str) -> None:
    if await db.scalar(select(Place.place_id).where(Place.place_id == place_id)) is None:
        raise not_found("Quán")


async def _own_review(db: AsyncSession, user: AuthUser, review_id: uuid.UUID) -> Review:
    review = await db.scalar(select(Review).where(Review.id == review_id).with_for_update())
    if review is None:
        raise not_found("Review")
    if review.user_id != user.id:
        raise AppError(403, "forbidden", "Bạn chỉ được sửa hoặc xoá review của chính mình")
    return review


async def _enforce_rate_limit(db: AsyncSession, user: AuthUser) -> None:
    recent = await db.scalar(
        select(func.count())
        .select_from(Review)
        .where(Review.user_id == user.id, Review.created_at >= func.now() - RATE_WINDOW)
    )
    if (recent or 0) >= MAX_NEW_REVIEWS:
        raise AppError(429, "rate_limited", "Bạn đăng review hơi nhanh, hãy thử lại sau ít phút")


# --------------------------------------------------------------------------- reading


async def list_reviews(
    db: AsyncSession, place_id: str, viewer: AuthUser | None, limit: int, offset: int
) -> ReviewListOut:
    """Visible reviews written on the website, newest first. Guests may call this.

    Internal reviews (`source = 'sheet'`) are never listed: they are data for Match and Analysis.
    """
    await _require_place(db, place_id)
    where = (
        Review.place_id == place_id,
        Review.status == "visible",
        Review.source == "user",
    )
    total = await db.scalar(select(func.count()).select_from(Review).where(*where)) or 0
    rows = await db.execute(
        select(Review, User.username)
        .outerjoin(User, User.id == Review.user_id)
        .where(*where)
        .order_by(Review.created_at.desc(), Review.id)
        .limit(limit)
        .offset(offset)
    )
    viewer_id = viewer.id if viewer else None
    items = [_out(review, username, viewer_id) for review, username in rows]
    return ReviewListOut(items=items, total=total, limit=limit, offset=offset)


async def my_review(db: AsyncSession, user: AuthUser, place_id: str) -> ReviewOut:
    """The caller's own review of a place, whatever its status, so the form can pre-fill."""
    review = await db.scalar(select(Review).where(Review.user_id == user.id, Review.place_id == place_id))
    if review is None:
        raise not_found("Review")
    return _out(review, user.username, user.id)


async def place_analysis(db: AsyncSession, place_id: str) -> ReviewAnalysisOut:
    await _require_place(db, place_id)
    reviews = (
        await db.scalars(select(Review).where(Review.place_id == place_id, Review.status == "visible"))
    ).all()
    return analysis.analyze(place_id, reviews)


# --------------------------------------------------------------------------- writing


async def create_review(db: AsyncSession, user: AuthUser, data: ReviewIn) -> ReviewOut:
    await _require_place(db, data.place_id)
    already = await db.scalar(
        select(Review.id).where(Review.user_id == user.id, Review.place_id == data.place_id)
    )
    if already is not None:
        raise AppError(409, "review_exists", "Bạn đã review quán này rồi, hãy sửa review cũ")
    await _enforce_rate_limit(db, user)

    verdict = moderation.check_texts(_texts_to_check(data))
    review = Review(
        place_id=data.place_id,
        user_id=user.id,
        source="user",
        status="flagged" if verdict.flagged else "visible",
        **_editable_fields(data),
    )
    db.add(review)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        if "uq_reviews_user_place" in str(exc.orig):  # two requests raced past the check above
            raise AppError(409, "review_exists", "Bạn đã review quán này rồi, hãy sửa review cũ") from None
        raise _account_gone() from None
    await db.refresh(review)
    return _out(review, user.username, user.id)


async def update_review(
    db: AsyncSession, user: AuthUser, review_id: uuid.UUID, data: ReviewUpdateIn
) -> ReviewOut:
    review = await _own_review(db, user, review_id)
    for field, value in _editable_fields(data).items():
        setattr(review, field, value)

    if review.status != "hidden":  # an admin's decision is never undone by editing
        if moderation.check_texts(_texts_to_check(data)).flagged:
            review.status = "flagged"
        elif review.status == "flagged":
            # Flagged by the text filter (now clean) or by reports (still reported)?
            reports = await db.scalar(
                select(func.count()).select_from(ReviewReport).where(ReviewReport.review_id == review.id)
            )
            if (reports or 0) < AUTO_FLAG_REPORTS:
                review.status = "visible"

    await db.commit()
    await db.refresh(review)
    return _out(review, user.username, user.id)


async def delete_review(db: AsyncSession, user: AuthUser, review_id: uuid.UUID) -> None:
    review = await _own_review(db, user, review_id)
    await db.delete(review)
    await db.commit()


async def report_review(db: AsyncSession, user: AuthUser, review_id: uuid.UUID, data: ReportIn) -> ReportOut:
    """'Báo cáo': record it; AUTO_FLAG_REPORTS different reporters flag the review automatically."""
    review = await db.scalar(select(Review).where(Review.id == review_id).with_for_update())
    # flagged/hidden reviews are not public anyway, and internal (sheet) reviews are never shown
    if review is None or review.status != "visible" or review.source != "user":
        raise not_found("Review")
    if review.user_id == user.id:
        raise AppError(422, "cannot_report_own", "Bạn không thể báo cáo review của chính mình")

    report = ReviewReport(review_id=review.id, reporter_id=user.id, reason=data.reason, note=data.note)
    db.add(report)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        if "uq_reports_review_reporter" in str(exc.orig):
            raise AppError(409, "already_reported", "Bạn đã báo cáo review này rồi") from None
        raise _account_gone() from None

    reporters = await db.scalar(
        select(func.count()).select_from(ReviewReport).where(ReviewReport.review_id == review.id)
    )
    if (reporters or 0) >= AUTO_FLAG_REPORTS:
        review.status = "flagged"
    await db.commit()
    await db.refresh(report)
    return ReportOut(review_id=review.id, reason=data.reason, created_at=report.created_at)
