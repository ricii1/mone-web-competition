"""Delete owned teaching resources without losing files on a failed transaction."""

import asyncio
import logging
import shutil
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.class_ import Class, Enrollment, GenerationStatus
from app.models.level import Level, LevelChunk
from app.models.live_session import LiveParticipant, LiveSession, LiveSessionStatus
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.progress import Attempt, Progress
from app.models.question import Question
from app.models.user import User
from app.realtime.pubsub import get_redis
from app.services.class_service import require_owner

logger = logging.getLogger(__name__)


def lock_owned_class(db: Session, class_id: UUID, teacher: User) -> Class:
    cls = db.query(Class).filter(Class.id == class_id).populate_existing().with_for_update().first()
    if cls is None:
        raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
    require_owner(cls, teacher)
    if cls.generation_status == GenerationStatus.generating:
        raise HTTPException(
            status_code=409, detail="Tunggu pembuatan level selesai terlebih dahulu"
        )
    return cls


def material_is_referenced(db: Session, material_id: UUID) -> bool:
    chunks = select(MaterialChunk.id).where(MaterialChunk.material_id == material_id)
    return (
        db.query(LevelChunk.id).filter(LevelChunk.chunk_id.in_(chunks)).first() is not None
        or db.query(Question.id).filter(Question.source_chunk_id.in_(chunks)).first() is not None
    )


def lock_failed_material(db: Session, class_id: UUID, material_id: UUID, teacher: User) -> Material:
    lock_owned_class(db, class_id, teacher)
    material = (
        db.query(Material)
        .filter(Material.id == material_id, Material.class_id == class_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if material is None:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan")
    if material.vector_status != VectorStatus.failed:
        raise HTTPException(
            status_code=409, detail="Tindakan ini hanya untuk materi yang gagal diproses"
        )
    if material_is_referenced(db, material.id):
        raise HTTPException(
            status_code=409,
            detail="Materi sudah menjadi sumber level atau soal. Sumber harus tetap disimpan",
        )
    return material


def _stage_path(path: Path) -> Path | None:
    if not path.exists() and not path.is_symlink():
        return None
    staged = path.with_name(f".deleted-{uuid.uuid4()}-{path.name}")
    path.rename(staged)
    return staged


def _restore_path(path: Path, staged: Path | None) -> None:
    if staged is not None:
        staged.rename(path)


async def _remove_staged(staged: Path | None) -> None:
    if staged is None:
        return
    try:
        if staged.is_dir() and not staged.is_symlink():
            await asyncio.to_thread(shutil.rmtree, staged)
        else:
            await asyncio.to_thread(staged.unlink)
    except OSError:
        logger.exception("Could not remove staged resource files: %s", staged)


async def delete_failed_material(
    db: Session, class_id: UUID, material_id: UUID, teacher: User
) -> None:
    material = lock_failed_material(db, class_id, material_id, teacher)
    path = Path(material.file_path).absolute()
    root = Path(settings.upload_dir).resolve() / str(class_id)
    if (
        root.is_symlink()
        or not path.resolve().is_relative_to(root)
        or not path.parent.resolve().is_relative_to(root)
    ):
        raise HTTPException(status_code=409, detail="Lokasi file materi tidak valid")
    staged = _stage_path(path)
    try:
        db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).delete(
            synchronize_session=False
        )
        db.delete(material)
        db.commit()
    except BaseException:
        db.rollback()
        _restore_path(path, staged)
        raise
    await _remove_staged(staged)


async def delete_class(db: Session, class_id: UUID, teacher: User, confirm_title: str) -> None:
    cls = lock_owned_class(db, class_id, teacher)
    if confirm_title != cls.title:
        raise HTTPException(status_code=400, detail="Ketik nama kelas dengan tepat untuk menghapus")
    if (
        db.query(Material.id)
        .filter(
            Material.class_id == class_id,
            Material.vector_status.in_([VectorStatus.pending, VectorStatus.processing]),
        )
        .first()
    ):
        raise HTTPException(
            status_code=409, detail="Tunggu pemrosesan PDF selesai sebelum menghapus kelas"
        )
    if (
        db.query(LiveSession.id)
        .filter(LiveSession.class_id == class_id, LiveSession.status != LiveSessionStatus.finished)
        .first()
    ):
        raise HTTPException(
            status_code=409, detail="Akhiri kuis bersama terlebih dahulu sebelum menghapus kelas"
        )
    levels = select(Level.id).where(Level.class_id == class_id)
    chunks = select(MaterialChunk.id).where(MaterialChunk.class_id == class_id)
    questions = select(Question.id).where(Question.level_id.in_(levels))
    sessions = select(LiveSession.id).where(LiveSession.class_id == class_id)
    if (
        db.query(Level.id)
        .filter(Level.class_id != class_id, Level.prerequisite_id.in_(levels))
        .first()
        or db.query(LevelChunk.id)
        .join(Level)
        .filter(Level.class_id != class_id, LevelChunk.chunk_id.in_(chunks))
        .first()
        or db.query(Question.id)
        .join(Level)
        .filter(Level.class_id != class_id, Question.source_chunk_id.in_(chunks))
        .first()
    ):
        raise HTTPException(
            status_code=409,
            detail="Sumber atau prasyarat dipakai kelas lain. Periksa hubungan kelas dahulu",
        )
    session_ids = list(db.scalars(sessions))
    directory = Path(settings.upload_dir).resolve() / str(class_id)
    if directory.is_symlink():
        raise HTTPException(status_code=409, detail="Lokasi folder kelas tidak valid")
    staged = _stage_path(directory)
    try:
        db.query(Attempt).filter(
            or_(Attempt.question_id.in_(questions), Attempt.live_session_id.in_(sessions))
        ).delete(synchronize_session=False)
        db.query(LiveParticipant).filter(LiveParticipant.live_session_id.in_(sessions)).delete(
            synchronize_session=False
        )
        db.query(LiveSession).filter(LiveSession.class_id == class_id).delete(
            synchronize_session=False
        )
        db.query(Progress).filter(Progress.level_id.in_(levels)).delete(synchronize_session=False)
        db.query(Question).filter(Question.level_id.in_(levels)).delete(synchronize_session=False)
        db.query(LevelChunk).filter(LevelChunk.level_id.in_(levels)).delete(
            synchronize_session=False
        )
        db.query(Level).filter(Level.class_id == class_id).update(
            {Level.prerequisite_id: None}, synchronize_session=False
        )
        db.query(Level).filter(Level.class_id == class_id).delete(synchronize_session=False)
        db.query(MaterialChunk).filter(MaterialChunk.class_id == class_id).delete(
            synchronize_session=False
        )
        db.query(Material).filter(Material.class_id == class_id).delete(synchronize_session=False)
        db.query(Enrollment).filter(Enrollment.class_id == class_id).delete(
            synchronize_session=False
        )
        db.delete(cls)
        db.commit()
    except BaseException as exc:
        db.rollback()
        _restore_path(directory, staged)
        if isinstance(exc, IntegrityError):
            raise HTTPException(
                status_code=409, detail="Data kelas sedang berubah. Muat ulang dan coba lagi"
            ) from exc
        raise
    await _remove_staged(staged)
    try:
        redis = get_redis()
        keys = [
            f"leaderboard:{class_id}",
            f"leaderboard:{class_id}:version",
            f"leaderboard:{class_id}:format",
        ]
        for session_id in session_ids:
            keys.extend(
                [
                    f"live:{session_id}:question",
                    f"live:{session_id}:answers",
                    f"live:{session_id}:control",
                ]
            )
        await redis.delete(*keys)
    except Exception:
        logger.exception("Could not clear deleted class cache: %s", class_id)
