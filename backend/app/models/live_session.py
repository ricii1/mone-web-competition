import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class LiveSessionStatus(enum.StrEnum):
    waiting = "waiting"
    running = "running"
    finished = "finished"


class LiveSession(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "live_sessions"

    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"))
    level_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("levels.id"))
    host_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    join_code: Mapped[str] = mapped_column(String(16), unique=True)
    status: Mapped[LiveSessionStatus] = mapped_column(
        Enum(LiveSessionStatus, name="live_session_status"), default=LiveSessionStatus.waiting
    )
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LiveParticipant(UUIDPKMixin, Base):
    __tablename__ = "live_participants"
    __table_args__ = (
        UniqueConstraint("live_session_id", "user_id", name="uq_live_participant_session_user"),
    )

    live_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("live_sessions.id")
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    score: Mapped[int] = mapped_column(Integer, default=0)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
