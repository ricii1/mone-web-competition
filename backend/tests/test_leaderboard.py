import uuid
from datetime import UTC, datetime, timedelta

from app.models.class_ import Class, ClassVisibility
from app.models.level import Level, LevelType
from app.models.progress import Progress, ProgressStatus
from app.models.user import User, UserRole
from app.services import leaderboard_service


def _user(db, name):
    u = User(name=name, email=f"{uuid.uuid4()}@x.com", password_hash="h", role=UserRole.student)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def _class(db):
    teacher = User(
        name="t", email=f"{uuid.uuid4()}@x.com", password_hash="h", role=UserRole.teacher
    )
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    cls = Class(teacher_id=teacher.id, title="K", visibility=ClassVisibility.public)
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


def _level(db, class_id, order_index=0):
    level = Level(class_id=class_id, title="L", type=LevelType.lesson_quiz, order_index=order_index)
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


def _progress(db, user_id, level_id, best_score, completed_at):
    p = Progress(
        user_id=user_id,
        level_id=level_id,
        status=ProgressStatus.completed,
        best_score=best_score,
        completed_at=completed_at,
    )
    db.add(p)
    db.commit()


def test_leaderboard_orders_by_score_desc(db):
    cls = _class(db)
    level = _level(db, cls.id)
    alice = _user(db, "Alice")
    bob = _user(db, "Bob")
    now = datetime.now(UTC)
    _progress(db, alice.id, level.id, 90, now)
    _progress(db, bob.id, level.id, 70, now)

    results = leaderboard_service.compute_leaderboard_from_postgres(db, cls.id)

    assert [r[1] for r in results] == ["Alice", "Bob"]


def test_leaderboard_tie_break_by_earlier_completion(db):
    cls = _class(db)
    level = _level(db, cls.id)
    alice = _user(db, "Alice")
    bob = _user(db, "Bob")
    now = datetime.now(UTC)
    _progress(db, alice.id, level.id, 80, now)
    _progress(db, bob.id, level.id, 80, now - timedelta(minutes=5))

    results = leaderboard_service.compute_leaderboard_from_postgres(db, cls.id)

    assert [r[1] for r in results] == ["Bob", "Alice"]


async def test_leaderboard_cache_rebuilds_and_matches_postgres(db):
    cls = _class(db)
    level = _level(db, cls.id)
    alice = _user(db, "Alice")
    bob = _user(db, "Bob")
    now = datetime.now(UTC)
    _progress(db, alice.id, level.id, 90, now)
    _progress(db, bob.id, level.id, 70, now)

    entries = await leaderboard_service.get_leaderboard(db, cls.id)
    postgres_order = [
        name for _, name, _, _ in leaderboard_service.compute_leaderboard_from_postgres(db, cls.id)
    ]

    assert [e.name for e in entries] == postgres_order
    assert entries[0].score == 90
    assert entries[0].rank == 1
