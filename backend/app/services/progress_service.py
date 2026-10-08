from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.level import Level
from app.models.progress import Progress, ProgressStatus

PASSING_SCORE = 70


def initialize_progress_for_enrollment(db: Session, user_id: UUID, class_id: UUID) -> None:
    levels = db.query(Level).filter(Level.class_id == class_id).all()
    for level in levels:
        existing = (
            db.query(Progress)
            .filter(Progress.user_id == user_id, Progress.level_id == level.id)
            .first()
        )
        if existing is not None:
            continue
        status_ = (
            ProgressStatus.unlocked if level.prerequisite_id is None else ProgressStatus.locked
        )
        db.add(Progress(user_id=user_id, level_id=level.id, status=status_))
    db.commit()


def get_or_create_progress(db: Session, user_id: UUID, level_id: UUID) -> Progress:
    progress = (
        db.query(Progress)
        .filter(Progress.user_id == user_id, Progress.level_id == level_id)
        .first()
    )
    if progress is None:
        progress = Progress(user_id=user_id, level_id=level_id, status=ProgressStatus.locked)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    return progress


def unlock_dependents(db: Session, user_id: UUID, level_id: UUID) -> None:
    dependents = db.query(Level).filter(Level.prerequisite_id == level_id).all()
    for dependent in dependents:
        progress = get_or_create_progress(db, user_id, dependent.id)
        if progress.status == ProgressStatus.locked:
            progress.status = ProgressStatus.unlocked
    db.commit()


def record_quiz_result(db: Session, user_id: UUID, level_id: UUID, score_percent: int) -> Progress:
    progress = get_or_create_progress(db, user_id, level_id)
    progress.best_score = max(progress.best_score, score_percent)
    if score_percent >= PASSING_SCORE and progress.status != ProgressStatus.completed:
        progress.status = ProgressStatus.completed
        progress.completed_at = datetime.now(UTC)
        db.commit()
        unlock_dependents(db, user_id, level_id)
    else:
        db.commit()
    db.refresh(progress)
    return progress
