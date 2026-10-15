import json
import logging
import time
import uuid
from collections import Counter
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from redis.exceptions import WatchError
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.core.security import generate_invite_code
from app.models.class_ import Class
from app.models.level import Level
from app.models.live_session import LiveParticipant, LiveSession, LiveSessionStatus
from app.models.progress import Attempt
from app.models.question import Question, QuestionStatus
from app.models.user import User
from app.realtime.channels import live_session_channel
from app.realtime.events import RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event

QUESTION_TIME_LIMIT_SECONDS = 20
BASE_POINTS = 100
SPEED_BONUS_MAX = 50
REDIS_STATE_TTL = 24 * 60 * 60
CONTROL_LOCK_TTL = 60
logger = logging.getLogger(__name__)


def _question_key(session_id: UUID) -> str:
    return f"live:{session_id}:question"


def _answers_key(session_id: UUID) -> str:
    return f"live:{session_id}:answers"


def ordered_questions(db: Session, level_id: UUID) -> list[Question]:
    return (
        db.query(Question)
        .filter(Question.level_id == level_id, Question.status == QuestionStatus.approved)
        .order_by(Question.created_at)
        .all()
    )


def get_session_by_join_code(db: Session, join_code: str) -> LiveSession:
    session = db.query(LiveSession).filter(LiveSession.join_code == join_code).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Kode join tidak ditemukan"
        )
    return session


def get_session_or_404(db: Session, session_id: UUID) -> LiveSession:
    session = db.get(LiveSession, session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesi tidak ditemukan")
    return session


def create_session(db: Session, cls: Class, level: Level, host_id: UUID) -> LiveSession:
    cls = db.query(Class).filter(Class.id == cls.id).populate_existing().with_for_update().first()
    if cls is None:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
    if level.class_id != cls.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Level bukan milik class ini"
        )
    if not ordered_questions(db, level.id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Level ini belum punya soal approved"
        )
    session = LiveSession(
        class_id=cls.id,
        level_id=level.id,
        host_id=host_id,
        join_code=generate_invite_code(6),
        status=LiveSessionStatus.waiting,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def join_session(
    db: Session, session: LiveSession, student_id: UUID, join_code: str
) -> LiveParticipant:
    if session.status == LiveSessionStatus.finished:
        raise HTTPException(status_code=400, detail="Sesi sudah selesai")
    if session.join_code != join_code:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Kode join salah")

    participant = (
        db.query(LiveParticipant)
        .filter(
            LiveParticipant.live_session_id == session.id, LiveParticipant.user_id == student_id
        )
        .first()
    )
    if participant is None:
        participant = LiveParticipant(live_session_id=session.id, user_id=student_id)
        db.add(participant)
        db.commit()
        db.refresh(participant)
    return participant


async def _publish(session_id: UUID, kind: str, extra: dict) -> None:
    try:
        await publish_event(
            live_session_channel(session_id),
            RealtimeEvent(type="live_session_update", payload={"kind": kind, **extra}),
        )
    except Exception:
        logger.exception("Live notification failed; clients can recover through REST")


async def _activate_question(
    session: LiveSession, question: Question, index: int, total: int
) -> None:
    redis = get_redis()
    deadline = time.time() + QUESTION_TIME_LIMIT_SECONDS
    while True:
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(_question_key(session.id))
                raw = await pipe.get(_question_key(session.id))
                current = json.loads(raw) if raw else None
                if current and current["index"] >= index and not current.get("closed"):
                    return
                pipe.multi()
                pipe.delete(_answers_key(session.id))
                pipe.set(
                    _question_key(session.id),
                    json.dumps(
                        {"question_id": str(question.id), "index": index, "deadline": deadline}
                    ),
                    ex=REDIS_STATE_TTL,
                )
                await pipe.execute()
                break
            except WatchError:
                continue
    await _publish(
        session.id,
        "question_started",
        {
            "question_id": str(question.id),
            "question_text": question.question_text,
            "options": question.options,
            "index": index,
            "total": total,
            "deadline": deadline,
            "time_limit_seconds": QUESTION_TIME_LIMIT_SECONDS,
        },
    )


@asynccontextmanager
async def _control_lock(session_id: UUID) -> AsyncIterator[None]:
    redis = get_redis()
    key = f"live:{session_id}:control"
    token = str(uuid.uuid4())
    # Control operations only perform short database/Redis writes, never LLM work.
    if not await redis.set(key, token, nx=True, ex=CONTROL_LOCK_TTL):
        raise HTTPException(status_code=409, detail="Sesi sedang diperbarui. Coba sebentar lagi")
    try:
        yield
    finally:
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(key)
                if await pipe.get(key) == token:
                    pipe.multi()
                    pipe.delete(key)
                    await pipe.execute()
            except WatchError:
                pass


def _refresh_control_session(db: Session, session: LiveSession) -> None:
    try:
        db.refresh(session, with_for_update={"nowait": True})
    except OperationalError as exc:
        db.rollback()
        if getattr(exc.orig, "sqlstate", None) == "55P03":
            raise HTTPException(status_code=409, detail="Sesi sedang diperbarui") from exc
        raise


async def start_session(db: Session, session: LiveSession) -> None:
    async with _control_lock(session.id):
        _refresh_control_session(db, session)
        if session.status != LiveSessionStatus.waiting:
            raise HTTPException(status_code=400, detail="Sesi sudah dimulai")
        questions = ordered_questions(db, session.level_id)
        if not questions:
            raise HTTPException(status_code=400, detail="Level belum punya soal yang disetujui")
        session.status = LiveSessionStatus.running
        session.started_at = datetime.now(UTC)
        session.current_question_index = 0
        db.commit()
        await _activate_question(session, questions[0], 0, len(questions))


async def submit_answer(
    db: Session, session: LiveSession, student_id: UUID, question_id: UUID, answer: str
) -> None:
    redis = get_redis()
    question_key = _question_key(session.id)
    answers_key = _answers_key(session.id)
    while True:
        async with redis.pipeline(transaction=True) as pipe:
            try:
                await pipe.watch(question_key)
                raw = await pipe.get(question_key)
                if raw is None:
                    raise HTTPException(status_code=400, detail="Tidak ada soal aktif")
                active = json.loads(raw)
                if active["question_id"] != str(question_id):
                    raise HTTPException(status_code=400, detail="Soal sudah berganti")
                submitted_at = time.time()
                if active.get("closed") or submitted_at >= active["deadline"]:
                    raise HTTPException(status_code=400, detail="Waktu sudah habis")
                question = db.get(Question, question_id)
                if question is None or answer not in question.options:
                    raise HTTPException(status_code=400, detail="Pilihan jawaban tidak sesuai")
                pipe.multi()
                pipe.hsetnx(
                    answers_key,
                    str(student_id),
                    json.dumps(
                        {
                            "answer": answer,
                            "submitted_at": submitted_at,
                        }
                    ),
                )
                pipe.expire(answers_key, REDIS_STATE_TTL)
                saved, _ = await pipe.execute()
                if not saved:
                    raise HTTPException(status_code=400, detail="Sudah menjawab soal ini")
                return
            except WatchError:
                continue


async def close_current_question(
    db: Session, session: LiveSession, question_id: UUID | None = None
) -> None:
    async with _control_lock(session.id):
        _refresh_control_session(db, session)
        if session.status != LiveSessionStatus.running:
            raise HTTPException(status_code=400, detail="Sesi tidak sedang berjalan")
        await _close_current_question(db, session, question_id=question_id)


async def _close_current_question(
    db: Session, session: LiveSession, *, advance: bool = True, question_id: UUID | None = None
) -> None:
    redis = get_redis()
    raw = await redis.get(_question_key(session.id))
    if raw is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada soal aktif")

    active = json.loads(raw)
    if question_id is not None and active["question_id"] != str(question_id):
        raise HTTPException(status_code=409, detail="Soal sudah berganti")
    if active["index"] < session.current_question_index:
        if not advance:
            session.current_question_index = active["index"]
            session.status = LiveSessionStatus.finished
            session.ended_at = datetime.now(UTC)
            db.commit()
            return
        questions = ordered_questions(db, session.level_id)
        await _activate_question(
            session,
            questions[session.current_question_index],
            session.current_question_index,
            len(questions),
        )
        return
    active["closed"] = True
    await redis.set(_question_key(session.id), json.dumps(active), ex=REDIS_STATE_TTL)
    question = db.get(Question, UUID(active["question_id"]))
    deadline = active["deadline"]

    raw_answers: dict[bytes | str, bytes | str] = await redis.hgetall(_answers_key(session.id))
    distribution: Counter[str] = Counter()

    already_saved = (
        db.query(Attempt.id).filter_by(live_session_id=session.id, question_id=question.id).first()
        is not None
    )
    for user_id_str, payload_raw in raw_answers.items():
        payload = json.loads(payload_raw)
        answer_text = payload["answer"]
        distribution[answer_text] += 1
        if already_saved:
            continue
        is_correct = answer_text == question.correct_answer
        submitted_at = payload["submitted_at"]
        speed_ratio = min(1.0, max(0.0, (deadline - submitted_at) / QUESTION_TIME_LIMIT_SECONDS))
        points = BASE_POINTS + round(SPEED_BONUS_MAX * speed_ratio) if is_correct else 0

        participant = (
            db.query(LiveParticipant)
            .filter(
                LiveParticipant.live_session_id == session.id,
                LiveParticipant.user_id == UUID(user_id_str),
            )
            .first()
        )
        if participant is not None:
            participant.score += points

        db.add(
            Attempt(
                user_id=UUID(user_id_str),
                question_id=question.id,
                user_answer=answer_text,
                is_correct=is_correct,
                live_session_id=session.id,
            )
        )

    questions = ordered_questions(db, session.level_id)
    next_index = active["index"] + 1
    is_finished = not advance or next_index >= len(questions)

    if is_finished:
        session.status = LiveSessionStatus.finished
        session.ended_at = datetime.now(UTC)
    else:
        session.current_question_index = next_index
    db.commit()

    await redis.delete(_answers_key(session.id))

    participants = (
        db.query(LiveParticipant)
        .filter(LiveParticipant.live_session_id == session.id)
        .order_by(LiveParticipant.score.desc())
        .all()
    )
    await _publish(
        session.id,
        "question_closed",
        {
            "question_id": str(question.id),
            "correct_answer": question.correct_answer,
            "distribution": dict(distribution),
            "leaderboard": [{"user_id": str(p.user_id), "score": p.score} for p in participants],
            "finished": is_finished,
        },
    )

    if not is_finished:
        await _activate_question(session, questions[next_index], next_index, len(questions))


async def end_session(db: Session, session: LiveSession) -> None:
    async with _control_lock(session.id):
        _refresh_control_session(db, session)
        if session.status == LiveSessionStatus.finished:
            return
        redis = get_redis()
        if await redis.exists(_question_key(session.id)):
            await _close_current_question(db, session, advance=False)
        else:
            session.status = LiveSessionStatus.finished
            session.ended_at = datetime.now(UTC)
            db.commit()
        await _publish(session.id, "session_ended", {})


async def session_snapshot(db: Session, session: LiveSession, user_id: UUID) -> dict:
    """REST recovery state; only closed questions may expose their correct answer."""
    redis = get_redis()
    raw = await redis.get(_question_key(session.id))
    active = json.loads(raw) if raw else None
    questions = ordered_questions(db, session.level_id)
    question_state = None
    my_answer = None
    if active:
        question = db.get(Question, UUID(active["question_id"]))
        if question is not None:
            question_state = {
                "question_id": str(question.id),
                "question_text": question.question_text,
                "options": question.options,
                "index": active["index"],
                "total": len(questions),
                "deadline": active["deadline"],
                "time_limit_seconds": QUESTION_TIME_LIMIT_SECONDS,
            }
        answer = await redis.hget(_answers_key(session.id), str(user_id))
        if answer:
            my_answer = json.loads(answer)["answer"]
    closed_question = None
    if session.status == LiveSessionStatus.finished and session.started_at and questions:
        index = min(session.current_question_index, len(questions) - 1)
        question = questions[index]
        attempts = (
            db.query(Attempt).filter_by(live_session_id=session.id, question_id=question.id).all()
        )
        closed_question = {
            "question_id": str(question.id),
            "correct_answer": question.correct_answer,
            "distribution": dict(Counter(a.user_answer for a in attempts)),
            "finished": True,
        }
        my_answer = next((a.user_answer for a in attempts if a.user_id == user_id), None)
        if question_state is None:
            question_state = {
                "question_id": str(question.id),
                "question_text": question.question_text,
                "options": question.options,
                "index": index,
                "total": len(questions),
                "deadline": 0,
                "time_limit_seconds": QUESTION_TIME_LIMIT_SECONDS,
            }
    participants = (
        db.query(LiveParticipant, User.name)
        .join(User, User.id == LiveParticipant.user_id)
        .filter(LiveParticipant.live_session_id == session.id)
        .order_by(LiveParticipant.score.desc(), LiveParticipant.joined_at)
        .all()
    )
    return {
        "question": question_state,
        "closed_question": closed_question,
        "my_answer": my_answer,
        "participants": [
            {"user_id": str(p.user_id), "name": name, "score": p.score} for p, name in participants
        ],
    }
