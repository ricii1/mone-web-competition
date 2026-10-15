from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.class_ import Class, GenerationStatus
from app.models.level import Level, LevelChunk, LevelStatus
from app.models.live_session import LiveSession
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.progress import Attempt, Progress
from app.models.question import Question, QuestionStatus
from app.schemas.level import LevelResponse, LevelSourceResponse, LevelUpdateRequest
from app.schemas.question import validate_question_options

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
            .join(Material, Material.id == MaterialChunk.material_id)
            .order_by(
                Material.created_at,
                Material.id,
                MaterialChunk.order_index,
                MaterialChunk.page_start,
                MaterialChunk.page_end,
                MaterialChunk.id,
            )
            .all()
        )
        for level_id, chunk in rows:
            sources[level_id].append(
                LevelSourceResponse(
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


def _lock_level(db: Session, level: Level) -> None:
    # One class lock serializes graph edits, including concurrent cycle creation.
    db.query(Class).filter(Class.id == level.class_id).with_for_update().one()
    db.refresh(level, with_for_update=True)


def _validate_prerequisite(db: Session, level: Level, prerequisite_id: UUID) -> None:
    parents = dict(
        db.query(Level.id, Level.prerequisite_id).filter(Level.class_id == level.class_id).all()
    )
    if prerequisite_id not in parents:
        raise HTTPException(status_code=422, detail="Prasyarat harus berasal dari kelas yang sama")
    visited = {level.id}
    current = prerequisite_id
    while current is not None:
        if current in visited:
            raise HTTPException(status_code=422, detail="Prasyarat tidak boleh membentuk lingkaran")
        visited.add(current)
        if current not in parents:
            raise HTTPException(status_code=422, detail="Rantai prasyarat kelas tidak valid")
        current = parents[current]


def update_level(db: Session, level: Level, body: LevelUpdateRequest) -> Level:
    _lock_level(db, level)
    if body.prerequisite_id is not None and not body.clear_prerequisite:
        _validate_prerequisite(db, level, body.prerequisite_id)
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
    if body.source_note is not None:
        # An empty string clears the note (stored as NULL).
        level.source_note = body.source_note or None
    if body.key_points is not None:
        level.key_points = body.key_points
    if body.status is not None:
        if body.status == LevelStatus.approved and not _has_approved_question(db, level.id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Level belum punya soal approved"
            )
        level.status = body.status
    db.commit()
    db.refresh(level)
    return level


def _has_approved_question(db: Session, level_id: UUID) -> bool:
    return (
        db.query(Question.id)
        .filter(Question.level_id == level_id, Question.status == QuestionStatus.approved)
        .first()
        is not None
    )


def delete_level(db: Session, level: Level) -> None:
    _lock_level(db, level)
    if level.prerequisite_id is not None:
        try:
            _validate_prerequisite(db, level, level.prerequisite_id)
        except HTTPException as exc:
            raise HTTPException(
                status_code=409, detail="Perbaiki rantai prasyarat sebelum menghapus level"
            ) from exc
    questions = db.query(Question).filter(Question.level_id == level.id).with_for_update().all()
    question_ids = [question.id for question in questions]
    used = (
        db.query(Progress.id).filter(Progress.level_id == level.id).first()
        or db.query(Attempt.id).filter(Attempt.question_id.in_(question_ids)).first()
        or db.query(LiveSession.id).filter(LiveSession.level_id == level.id).first()
    )
    if used:
        raise HTTPException(
            status_code=409, detail="Level sudah digunakan. Riwayat belajar tidak boleh dihapus"
        )
    dependents = db.query(Level).filter(Level.prerequisite_id == level.id).all()
    if any(dependent.class_id != level.class_id for dependent in dependents):
        raise HTTPException(
            status_code=409, detail="Ada prasyarat lintas kelas yang perlu diperbaiki"
        )
    try:
        for dependent in dependents:
            dependent.prerequisite_id = level.prerequisite_id
        db.flush()
        db.query(Question).filter(Question.level_id == level.id).delete()
        db.query(LevelChunk).filter(LevelChunk.level_id == level.id).delete()
        db.delete(level)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409, detail="Level sedang digunakan dan tidak bisa dihapus"
        ) from exc


def class_publish_blockers(db: Session, class_id: UUID) -> list[str]:
    """Report levels whose lessons or quiz questions have not been approved."""
    levels = list_levels_for_class(db, class_id)
    approved_questions = (
        db.query(Question)
        .join(Level, Level.id == Question.level_id)
        .filter(Level.class_id == class_id, Question.status == QuestionStatus.approved)
        .all()
    )
    approved_ids = set()
    invalid_ids = set()
    for question in approved_questions:
        approved_ids.add(question.level_id)
        try:
            validate_question_options(question.options, question.correct_answer)
        except ValueError:
            invalid_ids.add(question.level_id)
    blockers = []
    for level in levels:
        reasons = []
        if level.status != LevelStatus.approved:
            reasons.append("materi belum disetujui")
        if level.id not in approved_ids:
            reasons.append("belum punya soal yang disetujui")
        if level.id in invalid_ids:
            reasons.append("pilihan atau jawaban soal perlu diperbaiki")
        if reasons:
            blockers.append(f"{level.title} ({'; '.join(reasons)})")
    return blockers


def has_approved_level(db: Session, class_id: UUID) -> bool:
    return (
        db.query(Level.id)
        .filter(Level.class_id == class_id, Level.status == LevelStatus.approved)
        .first()
        is not None
    )


def request_generation(db: Session, cls: Class) -> str:
    """Validate a generate request and mark the class as generating (caller enqueues the job)."""
    cls = db.query(Class).filter(Class.id == cls.id).populate_existing().with_for_update().one()
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
    cls.generation_job_id = str(uuid4())
    cls.generation_requested_at = datetime.now(UTC)
    job_id = cls.generation_job_id
    db.commit()
    return job_id


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
