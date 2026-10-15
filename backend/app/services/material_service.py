import asyncio
import uuid
from pathlib import Path
from uuid import UUID

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.class_ import Class
from app.models.material import Material, MaterialChunk, VectorStatus
from app.models.user import User
from app.schemas.material import MaterialSection, MaterialSectionsResponse
from app.services import class_service


async def save_uploaded_pdf(db: Session, cls: Class, file: UploadFile) -> Material:
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File harus berformat PDF"
        )
    max_bytes = settings.max_upload_mb * 1024 * 1024
    upload_dir = Path(settings.upload_dir) / str(cls.id)
    await asyncio.to_thread(upload_dir.mkdir, parents=True, exist_ok=True)
    file_path = upload_dir / f"{uuid.uuid4()}.pdf"
    size = 0
    try:
        output = await asyncio.to_thread(file_path.open, "xb")
        try:
            while chunk := await file.read(min(64 * 1024, max_bytes - size + 1)):
                if size == 0 and not chunk.startswith(b"%PDF-"):
                    raise HTTPException(status_code=400, detail="File harus berformat PDF")
                size += len(chunk)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Ukuran file melebihi batas {settings.max_upload_mb}MB",
                    )
                await asyncio.to_thread(output.write, chunk)
            if not size:
                raise HTTPException(status_code=400, detail="File PDF kosong")
        finally:
            await asyncio.to_thread(output.close)
        # Do not hold a database lock while awaiting the upload stream.
        locked = (
            db.query(Class).filter(Class.id == cls.id).populate_existing().with_for_update().first()
        )
        if locked is None:
            raise HTTPException(status_code=404, detail="Kelas tidak ditemukan")
        material = Material(
            class_id=cls.id,
            file_name=file.filename or "materi.pdf",
            file_path=str(file_path),
            processing_job_id=str(uuid.uuid4()),
            vector_status=VectorStatus.pending,
        )
        db.add(material)
        db.commit()
        db.refresh(material)
        return material
    except BaseException:
        db.rollback()
        await asyncio.to_thread(file_path.unlink, missing_ok=True)
        raise


def get_material_pdf_path(db: Session, class_id: UUID, material_id: UUID) -> tuple[Path, str]:
    material = db.get(Material, material_id)
    if material is None or material.class_id != class_id:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan")
    path = Path(material.file_path).resolve()
    upload_root = Path(settings.upload_dir).resolve() / str(class_id)
    if not path.is_relative_to(upload_root) or not path.is_file():
        raise HTTPException(status_code=404, detail="File PDF tidak ditemukan")
    return path, Path(material.file_name).name


def prepare_material_retry(
    db: Session, class_id: UUID, material_id: UUID, teacher: User
) -> Material:
    from app.services.resource_deletion import lock_failed_material

    material = lock_failed_material(db, class_id, material_id, teacher)
    get_material_pdf_path(db, class_id, material_id)
    material.processing_job_id = str(uuid.uuid4())
    material.vector_status = VectorStatus.pending
    material.error_message = None
    db.commit()
    db.refresh(material)
    return material


async def enqueue_material(db: Session, material: Material) -> None:
    from app.worker.queue import get_arq_pool

    job_id = material.processing_job_id
    try:
        pool = await get_arq_pool()
        queued = await pool.enqueue_job(
            "process_material", str(material.id), job_id, _job_id=job_id
        )
        if queued is None:
            raise RuntimeError("Material job was not queued")
    except Exception as exc:
        message = "Materi belum bisa masuk antrean. Klik Coba proses lagi"
        db.query(Material).filter(
            Material.id == material.id,
            Material.processing_job_id == job_id,
            Material.vector_status == VectorStatus.pending,
        ).update(
            {Material.vector_status: VectorStatus.failed, Material.error_message: message},
            synchronize_session=False,
        )
        db.commit()
        raise HTTPException(status_code=503, detail=message) from exc


def _ready_material(db: Session, class_id: UUID, material_id: UUID, teacher: User) -> Material:
    cls = class_service.get_class_or_404(db, class_id)
    class_service.require_owner(cls, teacher)
    material = db.get(Material, material_id)
    if material is None or material.class_id != class_id:
        raise HTTPException(status_code=404, detail="Materi tidak ditemukan")
    if material.vector_status != VectorStatus.ready:
        raise HTTPException(
            status_code=409, detail="Tunggu materi selesai dibaca untuk melihat pembagiannya"
        )
    return material


def list_material_sections(
    db: Session, class_id: UUID, material_id: UUID, teacher: User, offset: int, limit: int
) -> MaterialSectionsResponse:
    _ready_material(db, class_id, material_id, teacher)
    query = db.query(MaterialChunk).filter(
        MaterialChunk.material_id == material_id, MaterialChunk.class_id == class_id
    )
    total = query.count()
    rows = (
        query.with_entities(
            MaterialChunk.id,
            MaterialChunk.section_title,
            MaterialChunk.order_index,
            MaterialChunk.page_start,
            MaterialChunk.page_end,
            func.substr(MaterialChunk.content, 1, 400).label("excerpt"),
            func.length(MaterialChunk.content).label("character_count"),
        )
        .order_by(MaterialChunk.order_index, MaterialChunk.page_start, MaterialChunk.id)
        .offset(offset)
        .limit(limit)
        .all()
    )
    return MaterialSectionsResponse(
        sections=[MaterialSection(**row._asdict()) for row in rows],
        total=total,
        offset=offset,
        limit=limit,
    )


def get_material_section(
    db: Session, class_id: UUID, material_id: UUID, chunk_id: UUID, teacher: User
) -> MaterialChunk:
    _ready_material(db, class_id, material_id, teacher)
    chunk = (
        db.query(MaterialChunk)
        .filter(
            MaterialChunk.id == chunk_id,
            MaterialChunk.material_id == material_id,
            MaterialChunk.class_id == class_id,
        )
        .first()
    )
    if chunk is None:
        raise HTTPException(status_code=404, detail="Bagian materi tidak ditemukan")
    return chunk
