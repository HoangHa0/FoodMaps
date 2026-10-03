"""M5 business logic. Routers call only these functions.

Transactions: `get_db` opens one session per request and never commits by itself. A session
starts its transaction on the first query, so every write path here (join, start, vote,
finalize) makes its FIRST query lock the room row (`SELECT ... FOR UPDATE`) and ends with
`commit()`, which releases the lock. Two writes to the same room therefore queue up instead
of both working on stale counts. (`async with db.begin()` would fail here: the transaction has
already begun by then.)
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import AppError
from app.modules.groups import rules
from app.modules.groups.models import GroupCandidate, GroupParticipant, GroupRoom, GroupVote
from app.modules.groups.schemas import (
    CandidateOut,
    CreateRoomIn,
    JoinRoomIn,
    ParticipantOut,
    RoomStateOut,
    VoteIn,
)
from app.modules.groups.tokens import hash_token, new_participant_token, new_room_code
from app.shared.auth import AuthUser
from app.shared.contracts import CandidateProvider, MatchCriteria

_CODE_ATTEMPTS = 5


def _now() -> datetime:
    return datetime.now(UTC)


def _ttl() -> timedelta:
    return timedelta(minutes=get_settings().group_room_ttl_minutes)


# --------------------------------------------------------------------------- create / join


async def create_room(
    db: AsyncSession, data: CreateRoomIn, user: AuthUser | None
) -> tuple[GroupRoom, GroupParticipant, str]:
    """Create a room in the lobby state; the creator becomes the host. Returns the raw token once."""
    for _ in range(_CODE_ATTEMPTS):
        room = GroupRoom(
            code=new_room_code(),
            expires_at=_now() + _ttl(),
            created_by_user_id=user.id if user else None,
        )
        try:
            async with db.begin_nested():  # SAVEPOINT: a code collision only undoes this INSERT
                db.add(room)
        except IntegrityError:
            continue  # the UNIQUE constraint on code decided; try another code
        break
    else:
        raise AppError(503, "room_code_exhausted", "Không tạo được phòng, thử lại sau")

    token = new_participant_token()
    host = GroupParticipant(
        room_id=room.id,
        display_name=data.display_name,
        token_hash=hash_token(token),
        is_host=True,
        user_id=user.id if user else None,
    )
    db.add(host)
    await db.commit()
    return room, host, token


async def join_room(
    db: AsyncSession, code: str, data: JoinRoomIn, user: AuthUser | None
) -> tuple[GroupRoom, GroupParticipant, str]:
    """Join a room still in the lobby. The room row is locked so join and start cannot overlap."""
    room = await _lock_room_by_code(db, code)
    await expire_if_needed(db, room)
    if room.status == "expired":
        raise AppError(410, "room_expired", "Phòng đã hết hạn")
    if room.status != "lobby":
        raise AppError(409, "room_started", "Phòng đã bắt đầu bình chọn, không thể vào thêm")

    members = await db.scalar(
        select(func.count()).select_from(GroupParticipant).where(GroupParticipant.room_id == room.id)
    )
    if members >= get_settings().group_max_participants:
        raise AppError(409, "room_full", "Phòng đã đủ người")

    token = new_participant_token()
    me = GroupParticipant(
        room_id=room.id,
        display_name=data.display_name,
        token_hash=hash_token(token),
        user_id=user.id if user else None,
    )
    db.add(me)
    room.version += 1  # the lobby list changed -> pollers refresh
    try:
        await db.commit()
    except IntegrityError:  # UNIQUE INDEX (room_id, lower(display_name)) decides, not a prior SELECT
        await db.rollback()
        raise AppError(409, "name_taken", "Tên này đã có người dùng trong phòng") from None
    return room, me, token


# --------------------------------------------------------------------------- authentication


async def authenticate_participant(
    db: AsyncSession, code: str, token: str, *, for_update: bool = False
) -> tuple[GroupRoom, GroupParticipant]:
    """Find the caller in THIS room (a token from room A never works in room B).

    for_update=True locks the room row; write endpoints must use it.
    404 if the room does not exist, 401 if the token does not belong to it.
    """
    stmt = (
        select(GroupRoom, GroupParticipant)
        .join(GroupParticipant, GroupParticipant.room_id == GroupRoom.id)
        .where(GroupRoom.code == code.upper(), GroupParticipant.token_hash == hash_token(token))
    )
    if for_update:
        stmt = stmt.with_for_update(of=GroupRoom)  # lock only the room row, not the participant
    row = (await db.execute(stmt)).first()
    if row is None:
        exists = await db.scalar(select(GroupRoom.id).where(GroupRoom.code == code.upper()))
        if exists is None:
            raise AppError(404, "room_not_found", "Phòng không tồn tại")
        raise AppError(401, "invalid_participant_token", "Bạn chưa tham gia phòng này")
    room, me = row
    await expire_if_needed(db, room)
    return room, me


async def _lock_room_by_code(db: AsyncSession, code: str) -> GroupRoom:
    room = await db.scalar(select(GroupRoom).where(GroupRoom.code == code.upper()).with_for_update())
    if room is None:
        raise AppError(404, "room_not_found", "Phòng không tồn tại")
    return room


# --------------------------------------------------------------------------- expiry


async def expire_if_needed(db: AsyncSession, room: GroupRoom) -> None:
    """Lazy expiry, called at the start of every request: no cron or background job.

    Past expires_at: a voting room with at least one like is decided (decided_by="expired");
    otherwise the room becomes "expired".
    """
    if room.status not in ("lobby", "voting") or _now() < room.expires_at:
        return
    # Re-read under a lock: a vote may have decided the room since we loaded it without one.
    await db.refresh(room, with_for_update=True)
    if room.status not in ("lobby", "voting") or _now() < room.expires_at:
        return
    best = rules.most_liked(await _tallies(db, room.id)) if room.status == "voting" else None
    if best is not None:
        _mark_decided(room, best.candidate_key, "expired")
    else:
        room.status = "expired"
    room.version += 1
    await db.commit()


# --------------------------------------------------------------------------- start / vote / finalize


async def start_room(
    db: AsyncSession,
    room: GroupRoom,
    me: GroupParticipant,
    criteria: MatchCriteria,
    provider: CandidateProvider,
) -> None:
    """Host only. `room` must have been loaded with for_update=True."""
    _require_host(me)
    if room.status != "lobby":
        raise AppError(409, "room_not_in_lobby", "Phòng đã bắt đầu hoặc đã kết thúc")

    k = get_settings().group_candidate_count
    candidates = (await provider.find_candidates(criteria, k=k))[:k]
    if not candidates:
        raise AppError(409, "no_candidates", "Không tìm thấy quán phù hợp, thử tiêu chí khác")

    db.add_all(
        GroupCandidate(room_id=room.id, place_id=c.place_id, rank=i, match_score=c.match_score, tags=c.tags)
        for i, c in enumerate(candidates)
    )
    room.status = "voting"
    room.criteria = criteria.model_dump(mode="json")
    room.member_count_at_start = await db.scalar(
        select(func.count()).select_from(GroupParticipant).where(GroupParticipant.room_id == room.id)
    )
    room.started_at = _now()
    room.expires_at = room.started_at + _ttl()  # voting always gets the full time window
    room.version += 1
    await db.commit()


async def cast_vote(db: AsyncSession, room: GroupRoom, me: GroupParticipant, data: VoteIn) -> None:
    """Upsert one vote, then maybe decide the room. `room` must be locked (for_update=True)."""
    if room.status != "voting":
        raise AppError(409, "room_not_voting", "Phòng không ở trạng thái bình chọn")
    candidate_ok = await db.scalar(
        select(GroupCandidate.id).where(
            GroupCandidate.id == data.candidate_id, GroupCandidate.room_id == room.id
        )
    )
    if candidate_ok is None:
        raise AppError(404, "candidate_not_found", "Quán này không thuộc phòng")

    # Changing your mind (like -> skip) updates the row instead of adding a second one
    stmt = pg_insert(GroupVote).values(
        participant_id=me.id, candidate_id=data.candidate_id, room_id=room.id, liked=data.liked
    )
    await db.execute(
        stmt.on_conflict_do_update(
            index_elements=[GroupVote.participant_id, GroupVote.candidate_id],
            set_={"liked": stmt.excluded.liked, "voted_at": func.now()},
        )
    )

    tallies = await _tallies(db, room.id)
    total_votes = await db.scalar(
        select(func.count()).select_from(GroupVote).where(GroupVote.room_id == room.id)
    )
    members = room.member_count_at_start or 0
    decision = rules.decide(tallies, members, all_voted=total_votes >= members * len(tallies))
    if decision is not None:
        _mark_decided(room, decision.candidate_key, decision.reason)
    room.version += 1
    await db.commit()


async def finalize(db: AsyncSession, room: GroupRoom, me: GroupParticipant) -> None:
    """Host ends voting early ("Chốt luôn"): the most-liked place wins."""
    _require_host(me)
    if room.status != "voting":
        raise AppError(409, "room_not_voting", "Phòng không ở trạng thái bình chọn")
    best = rules.most_liked(await _tallies(db, room.id))
    if best is None:
        raise AppError(409, "no_likes_yet", "Chưa có quán nào được thích")
    _mark_decided(room, best.candidate_key, "host")
    room.version += 1
    await db.commit()


def _require_host(me: GroupParticipant) -> None:
    if not me.is_host:
        raise AppError(403, "not_host", "Chỉ chủ phòng mới làm được việc này")


def _mark_decided(room: GroupRoom, place_id: str, reason: str) -> None:
    room.status = "decided"
    room.winner_place_id = place_id
    room.decided_by = reason
    room.decided_at = _now()


async def _tallies(db: AsyncSession, room_id: uuid.UUID) -> list[rules.Tally]:
    """Likes per candidate in one query. place_id is unique per room, so it is the rules' key."""
    likes = func.count(GroupVote.candidate_id).filter(GroupVote.liked)
    rows = await db.execute(
        select(GroupCandidate.place_id, GroupCandidate.rank, likes)
        .outerjoin(GroupVote, GroupVote.candidate_id == GroupCandidate.id)
        .where(GroupCandidate.room_id == room_id)
        .group_by(GroupCandidate.id)
    )
    return [rules.Tally(place_id, rank, n) for place_id, rank, n in rows]


# --------------------------------------------------------------------------- read


async def get_state(
    db: AsyncSession, room: GroupRoom, me: GroupParticipant, since_version: int | None = None
) -> RoomStateOut:
    """Full room state, or a tiny `changed=False` answer when the client is already up to date."""
    s = get_settings()
    base = {
        "code": room.code,
        "status": room.status,
        "version": room.version,
        "me": me.id,
        "expires_at": room.expires_at,
        "server_time": _now(),
        "poll_interval_ms": s.group_poll_interval_ms,
    }
    if since_version is not None and since_version == room.version:
        return RoomStateOut(changed=False, **base)  # idle poll: no participant/candidate queries

    votes_cast = func.count(GroupVote.candidate_id)
    participants = await db.execute(
        select(GroupParticipant, votes_cast)
        .outerjoin(GroupVote, GroupVote.participant_id == GroupParticipant.id)
        .where(GroupParticipant.room_id == room.id)
        .group_by(GroupParticipant.id)
        .order_by(GroupParticipant.joined_at)
    )
    likes = func.count(GroupVote.candidate_id).filter(GroupVote.liked)
    # bool_or over MY vote only: True/False if I voted on this card, NULL (None) if not
    my_vote = func.bool_or(GroupVote.liked).filter(GroupVote.participant_id == me.id)
    candidates = await db.execute(
        select(GroupCandidate, likes, my_vote)
        .outerjoin(GroupVote, GroupVote.candidate_id == GroupCandidate.id)
        .where(GroupCandidate.room_id == room.id)
        .group_by(GroupCandidate.id)
        .order_by(GroupCandidate.rank)
    )
    member_count = room.member_count_at_start or 0
    return RoomStateOut(
        **base,
        participants=[
            ParticipantOut(id=p.id, display_name=p.display_name, is_host=p.is_host, votes_cast=n)
            for p, n in participants
        ],
        candidates=[
            CandidateOut(
                id=c.id,
                place_id=c.place_id,
                rank=c.rank,
                match_score=c.match_score,
                tags=c.tags,
                likes=n,
                my_vote=mine,
            )
            for c, n, mine in candidates
        ],
        majority_threshold=rules.majority_threshold(member_count) if member_count else None,
        winner_place_id=room.winner_place_id,
        decided_by=room.decided_by,
    )
