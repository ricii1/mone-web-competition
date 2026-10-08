import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDPKMixin


class ProgressStatus(enum.StrEnum):
    locked = "locked"
    unlocked = "unlocked"
    completed = "completed"


class Progress(UUIDPKMixin, Base):
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "level_id", name="uq_progress_user_level"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("levels.id"))
    status: Mapped[ProgressStatus] = mapped_column(Enum(ProgressStatus, name="progress_status"))
    best_score: Mapped[int] = mapped_column(Integer, default=0)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class Attempt(UUIDPKMixin, Base):
    __tablename__ = "attempts"

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    question_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("questions.id"))
    user_answer: Mapped[str] = mapped_column(String(500))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    live_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("live_sessions.id"), nullable=True
    )
