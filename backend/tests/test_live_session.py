import time
import uuid

import pytest
from fastapi import HTTPException

from app.models.class_ import Class, ClassVisibility
from app.models.level import Level, LevelType
from app.models.live_session import LiveParticipant, LiveSession, LiveSessionStatus
from app.models.question import Question, QuestionStatus
from app.models.user import User, UserRole
from app.services import live_session_service


def _user(db, role):
    u = User(name="x", email=f"{uuid.uuid4()}@x.com", password_hash="h", role=role)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _setup(db):
    teacher = _user(db, UserRole.teacher)
    student = _user(db, UserRole.student)
    cls = Class(teacher_id=teacher.id, title="K", visibility=ClassVisibility.public)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    level = Level(class_id=cls.id, title="Boss", type=LevelType.boss, order_index=0)
    db.add(level)
    db.commit()
    db.refresh(level)
    question = Question(
        level_id=level.id,
        question_text="2+2?",
        options=["3", "4", "5", "6"],
        correct_answer="4",
        status=QuestionStatus.approved,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    session = LiveSession(
        class_id=cls.id, level_id=level.id, host_id=teacher.id, join_code="ABC123"
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    participant = LiveParticipant(live_session_id=session.id, user_id=student.id)
    db.add(participant)
    db.commit()
    return teacher, student, session, question


async def test_start_session_activates_first_question(db):
    _, _, session, question = _setup(db)

    await live_session_service.start_session(db, session)

    db.refresh(session)
    assert session.status == LiveSessionStatus.running
    raw = await live_session_service.get_redis().get(live_session_service._question_key(session.id))
    assert raw is not None


async def test_duplicate_answer_rejected(db):
    _, student, session, question = _setup(db)
    await live_session_service.start_session(db, session)

    await live_session_service.submit_answer(db, session, student.id, question.id, "4")
    with pytest.raises(HTTPException):
        await live_session_service.submit_answer(db, session, student.id, question.id, "3")


async def test_late_answer_rejected(db, monkeypatch):
    _, student, session, question = _setup(db)
    await live_session_service.start_session(db, session)
    original_time = time.time
    monkeypatch.setattr(time, "time", lambda: original_time() + 1000)

    with pytest.raises(HTTPException):
        await live_session_service.submit_answer(db, session, student.id, question.id, "4")


async def test_correct_answer_not_leaked_before_close(db):
    _, student, session, question = _setup(db)
    await live_session_service.start_session(db, session)

    raw = await live_session_service.get_redis().get(live_session_service._question_key(session.id))
    assert "correct_answer" not in raw


async def test_close_question_scores_correct_answer_and_advances(db):
    teacher, student, session, question = _setup(db)
    await live_session_service.start_session(db, session)
    await live_session_service.submit_answer(db, session, student.id, question.id, "4")

    await live_session_service.close_current_question(db, session)

    db.refresh(session)
    participant = (
        db.query(LiveParticipant).filter_by(live_session_id=session.id, user_id=student.id).first()
    )
    assert participant.score > 0
    assert session.status == LiveSessionStatus.finished
