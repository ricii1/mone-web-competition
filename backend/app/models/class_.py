import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDPKMixin


class ClassVisibility(enum.StrEnum):
    public = "public"
    private = "private"


class ClassStatus(enum.StrEnum):
    draft = "draft"
    published = "published"


class Class(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "classes"

    teacher_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[ClassVisibility] = mapped_column(
        Enum(ClassVisibility, name="class_visibility")
    )
    invite_code: Mapped[str | None] = mapped_column(String(16), nullable=True, unique=True)
    status: Mapped[ClassStatus] = mapped_column(
        Enum(ClassStatus, name="class_status"), default=ClassStatus.draft
    )


class Enrollment(UUIDPKMixin, Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("user_id", "class_id", name="uq_enrollment_user_class"),)

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    class_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("classes.id"))
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
