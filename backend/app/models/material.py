import enum
import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.db.base import Base, TimestampMixin, UUIDPKMixin


class VectorStatus(enum.StrEnum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"


class Material(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "materials"

    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"))
    file_name: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    vector_status: Mapped[VectorStatus] = mapped_column(
        Enum(VectorStatus, name="vector_status"), default=VectorStatus.pending
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_job_id: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MaterialChunk(UUIDPKMixin, Base):
    __tablename__ = "material_chunks"
    __table_args__ = (Index("ix_material_chunks_material_order", "material_id", "order_index"),)

    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.id"))
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"))
    section_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    content: Mapped[str] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    page_start: Mapped[int] = mapped_column(Integer)
    page_end: Mapped[int] = mapped_column(Integer)
    embedding: Mapped[list[float]] = mapped_column(Vector(settings.embedding_dim))
