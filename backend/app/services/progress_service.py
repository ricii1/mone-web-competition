from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
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
    db.execute(
        insert(Progress)
        .values(user_id=user_id, level_id=level_id, status=ProgressStatus.locked)
        .on_conflict_do_nothing(constraint="uq_progress_user_level")
    )
    return (
        db.query(Progress)
        .filter(Progress.user_id == user_id, Progress.level_id == level_id)
        .populate_existing()
        .with_for_update()
        .one()
    )


def unlock_dependents(db: Session, user_id: UUID, level_id: UUID) -> None:
    source = db.get(Level, level_id)
    dependents = (
        db.query(Level)
        .filter(Level.prerequisite_id == level_id, Level.class_id == source.class_id)
        .order_by(Level.id)
        .all()
    )
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
        db.flush()
        unlock_dependents(db, user_id, level_id)
    else:
        db.commit()
    db.refresh(progress)
    return progress
