import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class QuestionType(enum.StrEnum):
    multiple_choice = "multiple_choice"


class QuestionStatus(enum.StrEnum):
    draft = "draft"
    approved = "approved"


class Question(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "questions"

    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("levels.id"))
    question_text: Mapped[str] = mapped_column(Text)
    question_type: Mapped[QuestionType] = mapped_column(
        Enum(QuestionType, name="question_type"), default=QuestionType.multiple_choice
    )
    options: Mapped[list] = mapped_column(JSONB)
    correct_answer: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_chunk_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("material_chunks.id"), nullable=True
    )
    status: Mapped[QuestionStatus] = mapped_column(
        Enum(QuestionStatus, name="question_status"), default=QuestionStatus.draft
    )
