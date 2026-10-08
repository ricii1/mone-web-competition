from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.level import Level, LevelChunk
from app.models.question import Question, QuestionStatus
from app.schemas.level import LevelUpdateRequest

LEVELS_PER_BOSS = 4
QUESTIONS_PER_LEVEL = 5


def list_levels_for_class(db: Session, class_id: UUID) -> list[Level]:
    return db.query(Level).filter(Level.class_id == class_id).order_by(Level.order_index).all()


def get_level_or_404(db: Session, level_id: UUID) -> Level:
    level = db.get(Level, level_id)
    if level is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Level tidak ditemukan")
    return level


def update_level(db: Session, level: Level, body: LevelUpdateRequest) -> Level:
    if body.title is not None:
        level.title = body.title
    if body.order_index is not None:
        level.order_index = body.order_index
    if body.prerequisite_id is not None or body.clear_prerequisite:
        level.prerequisite_id = None if body.clear_prerequisite else body.prerequisite_id
    if body.status is not None:
        level.status = body.status
    db.commit()
    db.refresh(level)
    return level


def delete_level(db: Session, level: Level) -> None:
    db.query(Question).filter(Question.level_id == level.id).delete()
    db.query(LevelChunk).filter(LevelChunk.level_id == level.id).delete()
    db.delete(level)
    db.commit()


def class_publish_blockers(db: Session, class_id: UUID) -> list[str]:
    """Kembalikan daftar judul level yang belum punya soal approved (memblokir publish)."""
    levels = list_levels_for_class(db, class_id)
    blockers = []
    for level in levels:
        has_approved = (
            db.query(Question)
            .filter(Question.level_id == level.id, Question.status == QuestionStatus.approved)
            .first()
            is not None
        )
        if not has_approved:
            blockers.append(level.title)
    return blockers
