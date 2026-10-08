import json
import time
from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import generate_invite_code
from app.models.class_ import Class
from app.models.level import Level
from app.models.live_session import LiveParticipant, LiveSession, LiveSessionStatus
from app.models.progress import Attempt
from app.models.question import Question, QuestionStatus
from app.realtime.channels import live_session_channel
from app.realtime.events import RealtimeEvent
from app.realtime.pubsub import get_redis, publish_event

QUESTION_TIME_LIMIT_SECONDS = 20
BASE_POINTS = 100
SPEED_BONUS_MAX = 50
REDIS_STATE_TTL = QUESTION_TIME_LIMIT_SECONDS + 30


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
    await publish_event(
        live_session_channel(session_id),
        RealtimeEvent(type="live_session_update", payload={"kind": kind, **extra}),
    )


async def _activate_question(
    session: LiveSession, question: Question, index: int, total: int
) -> None:
    redis = get_redis()
    deadline = time.time() + QUESTION_TIME_LIMIT_SECONDS
    await redis.set(
        _question_key(session.id),
        json.dumps({"question_id": str(question.id), "index": index, "deadline": deadline}),
        ex=REDIS_STATE_TTL,
    )
    await redis.delete(_answers_key(session.id))
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


async def start_session(db: Session, session: LiveSession) -> None:
    if session.status != LiveSessionStatus.waiting:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Sesi sudah dimulai")
    questions = ordered_questions(db, session.level_id)
    session.status = LiveSessionStatus.running
    session.current_question_index = 0
    db.commit()
    await _activate_question(session, questions[0], 0, len(questions))


async def submit_answer(
    db: Session, session: LiveSession, student_id: UUID, question_id: UUID, answer: str
) -> None:
    redis = get_redis()
    raw = await redis.get(_question_key(session.id))
    if raw is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada soal aktif")

    active = json.loads(raw)
    if active["question_id"] != str(question_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Soal sudah berganti")
    if time.time() > active["deadline"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Waktu sudah habis")

    already_answered = await redis.hexists(_answers_key(session.id), str(student_id))
    if already_answered:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Sudah menjawab soal ini"
        )

    await redis.hset(
        _answers_key(session.id),
        str(student_id),
        json.dumps({"answer": answer, "submitted_at": time.time()}),
    )
    await redis.expire(_answers_key(session.id), REDIS_STATE_TTL)


async def close_current_question(db: Session, session: LiveSession) -> None:
    redis = get_redis()
    raw = await redis.get(_question_key(session.id))
    if raw is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tidak ada soal aktif")

    active = json.loads(raw)
    question = db.get(Question, UUID(active["question_id"]))
    deadline = active["deadline"]

    raw_answers: dict[bytes | str, bytes | str] = await redis.hgetall(_answers_key(session.id))
    distribution: Counter[str] = Counter()

    for user_id_str, payload_raw in raw_answers.items():
        payload = json.loads(payload_raw)
        answer_text = payload["answer"]
        distribution[answer_text] += 1
        is_correct = answer_text == question.correct_answer
        submitted_at = payload["submitted_at"]
        speed_ratio = max(0.0, (deadline - submitted_at) / QUESTION_TIME_LIMIT_SECONDS)
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
    is_finished = next_index >= len(questions)

    if is_finished:
        session.status = LiveSessionStatus.finished
        session.ended_at = datetime.now(UTC)
    db.commit()

    await redis.delete(_question_key(session.id), _answers_key(session.id))

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
        session.current_question_index = next_index
        db.commit()
        await _activate_question(session, questions[next_index], next_index, len(questions))


async def end_session(db: Session, session: LiveSession) -> None:
    session.status = LiveSessionStatus.finished
    session.ended_at = datetime.now(UTC)
    db.commit()
    redis = get_redis()
    await redis.delete(_question_key(session.id), _answers_key(session.id))
    await _publish(session.id, "session_ended", {})
