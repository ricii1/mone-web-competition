"""materials, levels, questions, progress, live class tables

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-30

"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

vector_status = postgresql.ENUM(
    "pending", "processing", "ready", "failed", name="vector_status", create_type=False
)
level_type = postgresql.ENUM("lesson_quiz", "boss", name="level_type", create_type=False)
level_status = postgresql.ENUM("draft", "approved", name="level_status", create_type=False)
question_type = postgresql.ENUM("multiple_choice", name="question_type", create_type=False)
question_status = postgresql.ENUM("draft", "approved", name="question_status", create_type=False)
progress_status = postgresql.ENUM(
    "locked", "unlocked", "completed", name="progress_status", create_type=False
)
live_session_status = postgresql.ENUM(
    "waiting", "running", "finished", name="live_session_status", create_type=False
)

EMBEDDING_DIM = 384


def upgrade() -> None:
    bind = op.get_bind()
    for enum_type in (
        vector_status,
        level_type,
        level_status,
        question_type,
        question_status,
        progress_status,
        live_session_status,
    ):
        enum_type.create(bind, checkfirst=True)

    op.create_table(
        "materials",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False
        ),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("vector_status", vector_status, nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
    )

    op.create_table(
        "material_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "material_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("materials.id"),
            nullable=False,
        ),
        sa.Column(
            "class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False
        ),
        sa.Column("section_title", sa.String(300), nullable=True),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("page_start", sa.Integer, nullable=False),
        sa.Column("page_end", sa.Integer, nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=False),
    )
    op.create_index("ix_material_chunks_class_id", "material_chunks", ["class_id"])

    op.create_table(
        "levels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False
        ),
        sa.Column(
            "prerequisite_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("levels.id"),
            nullable=True,
        ),
        sa.Column("title", sa.Text, nullable=False),
        sa.Column("type", level_type, nullable=False),
        sa.Column("order_index", sa.Integer, nullable=False),
        sa.Column("summary", sa.Text, nullable=True),
        sa.Column("status", level_status, nullable=False, server_default="draft"),
    )
    op.create_index("ix_levels_class_id", "levels", ["class_id"])

    op.create_table(
        "level_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "level_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("levels.id"), nullable=False
        ),
        sa.Column(
            "chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("material_chunks.id"),
            nullable=False,
        ),
    )

    op.create_table(
        "questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "level_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("levels.id"), nullable=False
        ),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("question_type", question_type, nullable=False, server_default="multiple_choice"),
        sa.Column("options", postgresql.JSONB, nullable=False),
        sa.Column("correct_answer", sa.String(500), nullable=False),
        sa.Column("explanation", sa.Text, nullable=True),
        sa.Column(
            "source_chunk_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("material_chunks.id"),
            nullable=True,
        ),
        sa.Column("status", question_status, nullable=False, server_default="draft"),
    )
    op.create_index("ix_questions_level_id", "questions", ["level_id"])

    op.create_table(
        "progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "level_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("levels.id"), nullable=False
        ),
        sa.Column("status", progress_status, nullable=False),
        sa.Column("best_score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("user_id", "level_id", name="uq_progress_user_level"),
    )

    op.create_table(
        "live_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False
        ),
        sa.Column(
            "level_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("levels.id"), nullable=False
        ),
        sa.Column(
            "host_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("join_code", sa.String(16), nullable=False, unique=True),
        sa.Column("status", live_session_status, nullable=False, server_default="waiting"),
        sa.Column("current_question_index", sa.Integer, nullable=False, server_default="0"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "attempts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "question_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("questions.id"),
            nullable=False,
        ),
        sa.Column("user_answer", sa.String(500), nullable=False),
        sa.Column("is_correct", sa.Boolean, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "live_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("live_sessions.id"),
            nullable=True,
        ),
    )

    op.create_table(
        "live_participants",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "live_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("live_sessions.id"),
            nullable=False,
        ),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("score", sa.Integer, nullable=False, server_default="0"),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("live_session_id", "user_id", name="uq_live_participant_session_user"),
    )


def downgrade() -> None:
    op.drop_table("live_participants")
    op.drop_table("attempts")
    op.drop_table("live_sessions")
    op.drop_table("progress")
    op.drop_table("questions")
    op.drop_table("level_chunks")
    op.drop_table("levels")
    op.drop_table("material_chunks")
    op.drop_table("materials")
    for enum_type in (
        live_session_status,
        progress_status,
        question_status,
        question_type,
        level_status,
        level_type,
        vector_status,
    ):
        enum_type.drop(op.get_bind(), checkfirst=True)
