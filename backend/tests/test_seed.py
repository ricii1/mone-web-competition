from unittest.mock import AsyncMock

from app.db.seed import TEACHER_EMAIL, seed
from app.models.class_ import Class, ClassStatus
from app.models.level import Level, LevelType
from app.models.question import Question, QuestionStatus
from app.models.user import User
from app.services.example_content import LESSONS


def test_seed_uses_elementary_lessons_and_preserves_existing_accounts(db, monkeypatch):
    monkeypatch.setattr("app.db.seed.rebuild_leaderboard_cache", AsyncMock())
    assert seed(db)
    teacher = db.query(User).filter_by(email=TEACHER_EMAIL).one()
    classes = db.query(Class).filter_by(teacher_id=teacher.id).all()
    public = next(cls for cls in classes if cls.status == ClassStatus.published)
    assert public.title == "IPA Kelas 4 - Siklus Air"
    levels = db.query(Level).filter_by(class_id=public.id).order_by(Level.order_index).all()
    assert len(levels) == 4
    for level, spec in zip(levels, LESSONS, strict=False):
        assert level.title == spec["title"]
        assert level.content == spec["content"]
    assert levels[-1].type == LevelType.boss
    questions = db.query(Question).filter(Question.level_id.in_([lv.id for lv in levels])).all()
    assert len(questions) == 20
    assert all(
        q.status == QuestionStatus.approved and q.correct_answer in q.options for q in questions
    )
    assert all("Newton" not in lv.title and "Sel" not in lv.title for lv in levels)
    original_counts = (db.query(User).count(), db.query(Class).count(), db.query(Level).count())
    assert not seed(db)
    assert (
        db.query(User).count(),
        db.query(Class).count(),
        db.query(Level).count(),
    ) == original_counts
