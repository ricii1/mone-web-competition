from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.class_ import Class, GenerationStatus
from app.models.level import Level, LevelChunk, LevelStatus
from app.models.material import Material, VectorStatus
from app.models.progress import Attempt, Progress
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


def has_approved_level(db: Session, class_id: UUID) -> bool:
    return (
        db.query(Level.id)
        .filter(Level.class_id == class_id, Level.status == LevelStatus.approved)
        .first()
        is not None
    )


def request_generation(db: Session, cls: Class) -> None:
    """Validate a generate request and mark the class as generating (caller enqueues the job)."""
    if cls.is_example:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Class contoh tidak bisa digenerate"
        )
    has_ready_material = (
        db.query(Material.id)
        .filter(Material.class_id == cls.id, Material.vector_status == VectorStatus.ready)
        .first()
        is not None
    )
    if not has_ready_material:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Belum ada materi yang siap diproses untuk class ini",
        )
    if cls.generation_status == GenerationStatus.generating:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Generate level sedang berjalan"
        )
    if has_approved_level(db, cls.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Class sudah punya level yang disetujui; tidak bisa digenerate ulang",
        )
    cls.generation_status = GenerationStatus.generating
    cls.generation_error = None
    db.commit()


def delete_draft_levels(db: Session, class_id: UUID) -> None:
    """Remove every draft level of a class with its dependent rows (safe against FKs)."""
    level_ids = [
        row[0]
        for row in db.query(Level.id)
        .filter(Level.class_id == class_id, Level.status == LevelStatus.draft)
        .all()
    ]
    if not level_ids:
        return
    question_ids = db.query(Question.id).filter(Question.level_id.in_(level_ids))
    db.query(Attempt).filter(Attempt.question_id.in_(question_ids)).delete(
        synchronize_session=False
    )
    db.query(Progress).filter(Progress.level_id.in_(level_ids)).delete(synchronize_session=False)
    db.query(Question).filter(Question.level_id.in_(level_ids)).delete(synchronize_session=False)
    db.query(LevelChunk).filter(LevelChunk.level_id.in_(level_ids)).delete(
        synchronize_session=False
    )
    db.query(Level).filter(Level.id.in_(level_ids)).update(
        {Level.prerequisite_id: None}, synchronize_session=False
    )
    db.query(Level).filter(Level.id.in_(level_ids)).delete(synchronize_session=False)
    db.commit()
