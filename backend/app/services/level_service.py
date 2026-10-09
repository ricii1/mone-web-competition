from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.class_ import Class, GenerationStatus
from app.models.level import Level, LevelChunk, LevelStatus
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.progress import Attempt, Progress
from app.models.question import Question, QuestionStatus
from app.schemas.level import (
    ChunkOptionResponse,
    LevelResponse,
    LevelSourceResponse,
    LevelUpdateRequest,
)

LEVELS_PER_BOSS = 4
QUESTIONS_PER_LEVEL = 5


def list_levels_for_class(db: Session, class_id: UUID) -> list[Level]:
    return db.query(Level).filter(Level.class_id == class_id).order_by(Level.order_index).all()


def build_level_responses(db: Session, levels: list[Level]) -> list[LevelResponse]:
    """Serialize levels with their source sections using one query for all of them."""
    sources: dict[UUID, list[LevelSourceResponse]] = {level.id: [] for level in levels}
    if levels:
        rows = (
            db.query(LevelChunk.level_id, MaterialChunk)
            .join(MaterialChunk, MaterialChunk.id == LevelChunk.chunk_id)
            .filter(LevelChunk.level_id.in_(list(sources)))
            .order_by(MaterialChunk.page_start, MaterialChunk.page_end)
            .all()
        )
        for level_id, chunk in rows:
            sources[level_id].append(
                LevelSourceResponse(
                    chunk_id=chunk.id,
                    section_title=chunk.section_title,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                )
            )
    responses = []
    for level in levels:
        response = LevelResponse.model_validate(level)
        response.sources = sources[level.id]
        responses.append(response)
    return responses


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
    if body.summary is not None:
        level.summary = body.summary
    if body.content is not None:
        # An empty string clears the article (stored as NULL).
        level.content = body.content or None
    if body.key_points is not None:
        level.key_points = body.key_points
    if body.source_chunk_ids is not None:
        _replace_sources(db, level, body.source_chunk_ids)
    if body.status is not None:
        if body.status == LevelStatus.approved and not _has_approved_question(db, level.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Level belum punya soal approved"
            )
        level.status = body.status
    db.commit()
    db.refresh(level)
    return level


def _replace_sources(db: Session, level: Level, chunk_ids: list[UUID]) -> None:
    valid = {
        row[0]
        for row in db.query(MaterialChunk.id)
        .filter(MaterialChunk.class_id == level.class_id, MaterialChunk.id.in_(chunk_ids))
        .all()
    }
    if len(valid) != len(chunk_ids):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sumber harus berasal dari materi class ini",
        )
    db.query(LevelChunk).filter(LevelChunk.level_id == level.id).delete()
    db.add_all(LevelChunk(level_id=level.id, chunk_id=chunk_id) for chunk_id in chunk_ids)
    db.flush()


def list_chunk_options(db: Session, class_id: UUID) -> list[ChunkOptionResponse]:
    rows = (
        db.query(MaterialChunk, Material.file_name)
        .join(Material, Material.id == MaterialChunk.material_id)
        .filter(MaterialChunk.class_id == class_id)
        .order_by(Material.file_name, MaterialChunk.page_start, MaterialChunk.page_end)
        .all()
    )
    return [
        ChunkOptionResponse(
            id=chunk.id,
            section_title=chunk.section_title,
            page_start=chunk.page_start,
            page_end=chunk.page_end,
            material_name=file_name,
        )
        for chunk, file_name in rows
    ]


def _has_approved_question(db: Session, level_id: UUID) -> bool:
    return (
        db.query(Question.id)
        .filter(Question.level_id == level_id, Question.status == QuestionStatus.approved)
        .first()
        is not None
    )


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
