import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class LevelType(enum.StrEnum):
    lesson_quiz = "lesson_quiz"
    boss = "boss"


class LevelStatus(enum.StrEnum):
    draft = "draft"
    approved = "approved"


class Level(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "levels"

    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"))
    prerequisite_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("levels.id"), nullable=True
    )
    title: Mapped[str] = mapped_column(Text)
    type: Mapped[LevelType] = mapped_column(Enum(LevelType, name="level_type"))
    order_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    key_points: Mapped[list[str]] = mapped_column(JSONB, default=list, server_default="[]")
    status: Mapped[LevelStatus] = mapped_column(
        Enum(LevelStatus, name="level_status"), default=LevelStatus.draft
    )


class LevelChunk(UUIDPKMixin, Base):
    __tablename__ = "level_chunks"

    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("levels.id"))
    chunk_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_chunks.id")
    )
