import asyncio
import logging
from uuid import UUID

from app.db.session import SessionLocal
from app.models.material import Material, MaterialChunk, VectorStatus
from app.rag.chunking import chunk_parsed_pdf
from app.rag.embedding import embed_passages
from app.rag.parsing import PdfParsingError, parse_pdf
from app.realtime.channels import material_channel
from app.realtime.events import MaterialProgressPayload, RealtimeEvent
from app.realtime.pubsub import publish_event
from app.services.resource_deletion import material_is_referenced

logger = logging.getLogger(__name__)


async def _publish_stage(
    material_id: str, stage: str, current: int = 0, total: int = 0, error: str | None = None
) -> None:
    payload = MaterialProgressPayload(
        material_id=material_id, stage=stage, current=current, total=total, error_message=error
    )
    event = RealtimeEvent(type="material_progress", payload=payload.model_dump())
    try:
        await publish_event(material_channel(UUID(material_id)), event)
    except Exception:
        logger.exception("Material progress notification failed: %s", material_id)


async def process_material(ctx: dict, material_id: str, job_id: str | None = None) -> None:
    """Job arq: ekstrak, chunk, dan embed satu material PDF. Idempoten."""
    db = SessionLocal()
    try:
        material = db.get(Material, UUID(material_id))
        if material is None or material.processing_job_id != job_id:
            return
        if job_id is not None:
            claimed = (
                db.query(Material)
                .filter(
                    Material.id == UUID(material_id),
                    Material.processing_job_id == job_id,
                    Material.vector_status.in_([VectorStatus.pending, VectorStatus.failed]),
                )
                .update(
                    {Material.vector_status: VectorStatus.processing, Material.error_message: None},
                    synchronize_session=False,
                )
            )
            db.commit()
            if not claimed:
                return
            db.refresh(material)
        else:
            if material.vector_status == VectorStatus.ready and material_is_referenced(
                db, material.id
            ):
                return
            material.vector_status = VectorStatus.processing
            material.error_message = None
            db.commit()
        if material_is_referenced(db, material.id):
            material.vector_status = VectorStatus.failed
            material.error_message = "Materi sudah dipakai sebagai sumber level atau soal"
            db.commit()
            await _publish_stage(material_id, "failed", error=material.error_message)
            return
        await _publish_stage(material_id, "reading")

        try:
            parsed = await asyncio.to_thread(parse_pdf, material.file_path)
        except PdfParsingError as exc:
            material.vector_status = VectorStatus.failed
            material.error_message = str(exc)
            db.commit()
            await _publish_stage(material_id, "failed", error=str(exc))
            return

        await _publish_stage(material_id, "chunking")
        chunks = await asyncio.to_thread(chunk_parsed_pdf, parsed)

        await _publish_stage(material_id, "embedding", current=0, total=len(chunks))
        embeddings = await asyncio.to_thread(embed_passages, [c.content for c in chunks])

        db.query(MaterialChunk).filter(MaterialChunk.material_id == material.id).delete()
        for order_index, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=True)):
            db.add(
                MaterialChunk(
                    material_id=material.id,
                    class_id=material.class_id,
                    section_title=chunk.section_title,
                    content=chunk.content,
                    order_index=order_index,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    embedding=embedding,
                )
            )
        material.vector_status = VectorStatus.ready
        db.commit()
        await _publish_stage(material_id, "done", current=len(chunks), total=len(chunks))
    except (Exception, asyncio.CancelledError):
        db.rollback()
        material = db.get(Material, UUID(material_id))
        if material is not None and material.processing_job_id == job_id:
            material.vector_status = VectorStatus.failed
            material.error_message = "Terjadi kesalahan saat memproses materi"
            db.commit()
        await _publish_stage(
            material_id, "failed", error="Terjadi kesalahan saat memproses materi. Coba proses lagi"
        )
        raise
    finally:
        db.close()
