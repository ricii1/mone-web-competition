from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.models.class_ import Class, ClassVisibility
from app.models.level import Level, LevelStatus, LevelType
from app.models.live_session import LiveSession, LiveSessionStatus
from app.models.progress import Attempt, Progress, ProgressStatus
from app.models.user import UserRole
from app.schemas.level import LevelUpdateRequest
from app.services import level_service, progress_service
from tests.conftest import TestSessionLocal
from tests.test_level_lesson import _auth, _enroll, _question, _setup, _user


def _level(db, cls, parent=None):
    level = Level(
        class_id=cls.id,
        title="Berikutnya",
        type=LevelType.lesson_quiz,
        order_index=1,
        prerequisite_id=parent,
    )
    db.add(level)
    db.commit()
    return level


@pytest.mark.parametrize("kind", ["self", "cycle", "other_class", "missing"])
def test_prerequisite_invalid_rejected(client, db, kind):
    teacher, cls, first = _setup(db)
    second = _level(db, cls, first.id)
    target = first.id
    if kind == "cycle":
        target = second.id
    elif kind == "other_class":
        other = Class(teacher_id=teacher.id, title="Lain", visibility=ClassVisibility.public)
        db.add(other)
        db.commit()
        target = _level(db, other).id
    elif kind == "missing":
        target = uuid4()
    response = client.patch(
        f"/api/v1/levels/{first.id}",
        json={"prerequisite_id": str(target)},
        headers=_auth(teacher),
    )
    assert response.status_code == 422
    db.refresh(first)
    assert first.prerequisite_id is None


def test_concurrent_graph_edits_cannot_create_cycle(db):
    _, cls, first = _setup(db)
    second = _level(db, cls)
    ids = first.id, second.id
    barrier = Barrier(2)

    def edit(index):
        with TestSessionLocal() as session:
            current = session.get(Level, ids[index])
            barrier.wait(timeout=10)
            try:
                level_service.update_level(
                    session, current, LevelUpdateRequest(prerequisite_id=ids[1 - index])
                )
                return 200
            except HTTPException as exc:
                session.rollback()
                return exc.status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(edit, [0, 1]))
    assert sorted(results) == [200, 422]


def test_unlock_does_not_cross_class_even_with_legacy_invalid_prerequisite(db):
    teacher, cls, first = _setup(db)
    student = _enroll(db, cls, first)
    other = Class(teacher_id=teacher.id, title="Lain", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    invalid = _level(db, other, first.id)
    progress_service.record_quiz_result(db, student.id, first.id, 100)
    assert db.query(Progress).filter_by(user_id=student.id, level_id=invalid.id).first() is None


def test_concurrent_results_keep_highest_with_stale_orm_and_unlock_once(db):
    _, cls, first = _setup(db)
    next_level = _level(db, cls, first.id)
    student = _enroll(db, cls, first)
    progress_service.initialize_progress_for_enrollment(db, student.id, cls.id)
    user_id, level_id = student.id, first.id
    barrier = Barrier(2)

    def record(score):
        with TestSessionLocal() as session:
            stale = session.query(Progress).filter_by(user_id=user_id, level_id=level_id).one()
            assert stale.best_score == 0
            barrier.wait(timeout=10)
            progress_service.record_quiz_result(session, user_id, level_id, score)

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(record, [100, 80]))
    db.expire_all()
    progress = db.query(Progress).filter_by(user_id=user_id, level_id=level_id).one()
    assert progress.best_score == 100
    assert progress.status == ProgressStatus.completed
    assert progress.completed_at is not None
    dependents = db.query(Progress).filter_by(user_id=user_id, level_id=next_level.id).all()
    assert len(dependents) == 1
    assert dependents[0].status == ProgressStatus.unlocked


def test_stale_progress_instance_cannot_replace_committed_best_score(db):
    _, cls, first = _setup(db)
    student = _enroll(db, cls, first)
    with TestSessionLocal() as stale_session:
        stale = stale_session.query(Progress).filter_by(user_id=student.id, level_id=first.id).one()
        progress_service.record_quiz_result(db, student.id, first.id, 100)
        result = progress_service.record_quiz_result(stale_session, student.id, first.id, 80)
        assert result is stale
        assert result.best_score == 100


@pytest.mark.parametrize(
    "payload",
    [
        {"options": []},
        {"options": ["A", "B", "C", " "]},
        {"options": ["A", " a ", "C", "D"]},
        {"options": ["C", "D", "E", "F"]},
        {"correct_answer": "Z"},
    ],
)
def test_manual_question_effective_patch_and_create_validation(client, db, payload):
    teacher, _, level = _setup(db)
    question = _question(db, level)
    headers = _auth(teacher)
    response = client.patch(f"/api/v1/questions/{question.id}", json=payload, headers=headers)
    assert response.status_code == 422
    db.refresh(question)
    assert question.options == ["A", "B", "C", "D"]
    assert question.correct_answer == "B"
    body = {"question_text": "Baru?", "options": ["A", "B", "C", "D"], "correct_answer": "B"}
    body.update(payload)
    assert (
        client.post(f"/api/v1/levels/{level.id}/questions", json=body, headers=headers).status_code
        == 422
    )


def test_legacy_invalid_question_cannot_be_approved_or_published(client, db):
    teacher, cls, level = _setup(db, published=False)
    question = _question(db, level)
    question.correct_answer = "Z"
    level.status = LevelStatus.approved
    db.commit()
    headers = _auth(teacher)
    response = client.patch(
        f"/api/v1/questions/{question.id}", json={"status": "approved"}, headers=headers
    )
    assert response.status_code == 422
    response = client.post(f"/api/v1/classes/{cls.id}/publish", headers=headers)
    assert response.status_code == 400
    assert "jawaban" in response.json()["detail"]
    fixed = client.patch(
        f"/api/v1/questions/{question.id}", json={"correct_answer": "A"}, headers=headers
    )
    assert fixed.status_code == 200
    assert client.post(f"/api/v1/classes/{cls.id}/publish", headers=headers).status_code == 200


def test_deleting_question_with_attempt_returns_conflict_preserving_history(client, db):
    teacher, _, level = _setup(db)
    question = _question(db, level)
    student = _user(db, UserRole.student)
    db.add(Attempt(user_id=student.id, question_id=question.id, user_answer="B", is_correct=True))
    db.commit()
    response = client.delete(f"/api/v1/questions/{question.id}", headers=_auth(teacher))
    assert response.status_code == 409
    assert db.query(Attempt).filter_by(question_id=question.id).count() == 1


@pytest.mark.parametrize("history", ["progress", "attempt", "live"])
def test_deleting_used_level_returns_conflict(client, db, history):
    teacher, cls, level = _setup(db)
    question = _question(db, level)
    student = _user(db, UserRole.student)
    if history == "progress":
        db.add(Progress(user_id=student.id, level_id=level.id, status=ProgressStatus.unlocked))
    elif history == "attempt":
        db.add(
            Attempt(user_id=student.id, question_id=question.id, user_answer="B", is_correct=True)
        )
    else:
        db.add(
            LiveSession(
                class_id=cls.id,
                level_id=level.id,
                host_id=teacher.id,
                join_code="abc",
                status=LiveSessionStatus.finished,
            )
        )
    db.commit()
    response = client.delete(f"/api/v1/levels/{level.id}", headers=_auth(teacher))
    assert response.status_code == 409
    assert db.get(Level, level.id) is not None


def test_delete_unused_middle_draft_relinks_dependents(client, db):
    teacher, cls, first = _setup(db, published=False)
    middle = _level(db, cls, first.id)
    last = _level(db, cls, middle.id)
    middle_id, last_id = middle.id, last.id
    _question(db, middle)
    response = client.delete(f"/api/v1/levels/{middle_id}", headers=_auth(teacher))
    assert response.status_code == 204
    db.expire_all()
    assert db.get(Level, middle_id) is None
    assert db.get(Level, last_id).prerequisite_id == first.id


def test_delete_question_during_live_rejected_before_attempts_exist(client, db):
    teacher, cls, level = _setup(db)
    question = _question(db, level)
    live = LiveSession(
        class_id=cls.id,
        level_id=level.id,
        host_id=teacher.id,
        join_code="active",
        status=LiveSessionStatus.running,
    )
    db.add(live)
    db.commit()
    response = client.delete(f"/api/v1/questions/{question.id}", headers=_auth(teacher))
    assert response.status_code == 409
    live.status = LiveSessionStatus.finished
    db.commit()
    assert (
        client.delete(f"/api/v1/questions/{question.id}", headers=_auth(teacher)).status_code == 204
    )


def test_delete_first_unused_draft_preserves_reachable_start(client, db):
    teacher, cls, first = _setup(db, published=False)
    next_level = _level(db, cls, first.id)
    response = client.delete(f"/api/v1/levels/{first.id}", headers=_auth(teacher))
    assert response.status_code == 204
    db.refresh(next_level)
    assert next_level.prerequisite_id is None


def test_delete_does_not_propagate_legacy_cross_class_prerequisite(client, db):
    teacher, cls, first = _setup(db, published=False)
    other = Class(teacher_id=teacher.id, title="Lain", visibility=ClassVisibility.public)
    db.add(other)
    db.commit()
    foreign = _level(db, other)
    first.prerequisite_id = foreign.id
    next_level = _level(db, cls, first.id)
    db.commit()
    response = client.delete(f"/api/v1/levels/{first.id}", headers=_auth(teacher))
    assert response.status_code == 409
    db.refresh(next_level)
    assert next_level.prerequisite_id == first.id
