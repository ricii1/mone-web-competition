import uuid

from app.models.class_ import Class, ClassVisibility
from app.models.level import Level, LevelType
from app.models.progress import ProgressStatus
from app.models.user import User, UserRole
from app.services.progress_service import (
    PASSING_SCORE,
    initialize_progress_for_enrollment,
    record_quiz_result,
)


def _make_user(db, role: UserRole) -> User:
    user = User(name="x", email=f"{uuid.uuid4()}@x.com", password_hash="h", role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _make_class(db, teacher_id) -> Class:
    cls = Class(teacher_id=teacher_id, title="Kelas", visibility=ClassVisibility.public)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


def _make_level(db, class_id, prerequisite_id=None, order_index=0) -> Level:
    level = Level(
        class_id=class_id,
        prerequisite_id=prerequisite_id,
        title="Level",
        type=LevelType.lesson_quiz,
        order_index=order_index,
    )
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def test_first_level_unlocked_others_locked_on_join(db):
    teacher = _make_user(db, UserRole.teacher)
    student = _make_user(db, UserRole.student)
    cls = _make_class(db, teacher.id)
    level1 = _make_level(db, cls.id, order_index=0)
    level2 = _make_level(db, cls.id, prerequisite_id=level1.id, order_index=1)

    initialize_progress_for_enrollment(db, student.id, cls.id)

    from app.models.progress import Progress

    p1 = db.query(Progress).filter_by(user_id=student.id, level_id=level1.id).first()
    p2 = db.query(Progress).filter_by(user_id=student.id, level_id=level2.id).first()
    assert p1.status == ProgressStatus.unlocked
    assert p2.status == ProgressStatus.locked


def test_passing_score_completes_and_unlocks_next(db):
    teacher = _make_user(db, UserRole.teacher)
    student = _make_user(db, UserRole.student)
    cls = _make_class(db, teacher.id)
    level1 = _make_level(db, cls.id, order_index=0)
    level2 = _make_level(db, cls.id, prerequisite_id=level1.id, order_index=1)
    initialize_progress_for_enrollment(db, student.id, cls.id)

    record_quiz_result(db, student.id, level1.id, PASSING_SCORE - 1)

    from app.models.progress import Progress

    p2 = db.query(Progress).filter_by(user_id=student.id, level_id=level2.id).first()
    assert p2.status == ProgressStatus.locked

    record_quiz_result(db, student.id, level1.id, PASSING_SCORE)

    p1 = db.query(Progress).filter_by(user_id=student.id, level_id=level1.id).first()
    p2 = db.query(Progress).filter_by(user_id=student.id, level_id=level2.id).first()
    assert p1.status == ProgressStatus.completed
    assert p2.status == ProgressStatus.unlocked


def test_best_score_keeps_highest(db):
    teacher = _make_user(db, UserRole.teacher)
    student = _make_user(db, UserRole.student)
    cls = _make_class(db, teacher.id)
    level1 = _make_level(db, cls.id, order_index=0)
    initialize_progress_for_enrollment(db, student.id, cls.id)

    record_quiz_result(db, student.id, level1.id, 80)
    record_quiz_result(db, student.id, level1.id, 60)

    from app.models.progress import Progress

    p1 = db.query(Progress).filter_by(user_id=student.id, level_id=level1.id).first()
    assert p1.best_score == 80
