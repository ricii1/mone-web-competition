from datetime import UTC, datetime, timedelta
from uuid import UUID

from arq import ArqRedis
from arq.jobs import Job, JobStatus
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models.class_ import Class, GenerationStatus

GENERATION_TIMEOUT_SECONDS = 1800


def mark_generation_failed(db: Session, class_id: UUID, job_id: str | None, message: str) -> None:
    db.query(Class).filter(
        Class.id == class_id,
        Class.generation_status == GenerationStatus.generating,
        Class.generation_job_id == job_id,
    ).update({Class.generation_status: GenerationStatus.failed, Class.generation_error: message})
    db.commit()


async def recover_generation(db: Session, cls: Class, redis: ArqRedis) -> None:
    if cls.generation_status != GenerationStatus.generating:
        return
    cutoff = datetime.now(UTC) - timedelta(seconds=GENERATION_TIMEOUT_SECONDS + 60)
    if cls.generation_requested_at is not None and cls.generation_requested_at > cutoff:
        return
    # Queued/deferred jobs are valid even if waiting longer than execution timeout.
    if cls.generation_job_id:
        job_status = await Job(cls.generation_job_id, redis).status()
        if job_status not in (JobStatus.not_found, JobStatus.complete):
            return
    mark_generation_failed(
        db,
        cls.id,
        cls.generation_job_id,
        "Pemrosesan terhenti. Silakan buat ulang level",
    )
    db.refresh(cls)


async def recover_stale_generations(ctx: dict) -> None:
    with SessionLocal() as db:
        classes = (
            db.query(Class).filter(Class.generation_status == GenerationStatus.generating).all()
        )
        for cls in classes:
            await recover_generation(db, cls, ctx["redis"])
