"""initial: users, classes, enrollments

Revision ID: 0001
Revises:
Create Date: 2026-09-30

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

user_role = postgresql.ENUM("teacher", "student", name="user_role", create_type=False)
class_visibility = postgresql.ENUM("public", "private", name="class_visibility", create_type=False)
class_status = postgresql.ENUM("draft", "published", name="class_status", create_type=False)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    user_role.create(op.get_bind(), checkfirst=True)
    class_visibility.create(op.get_bind(), checkfirst=True)
    class_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column(
            "teacher_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("visibility", class_visibility, nullable=False),
        sa.Column("invite_code", sa.String(16), nullable=True, unique=True),
        sa.Column("status", class_status, nullable=False, server_default="draft"),
    )

    op.create_table(
        "enrollments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "class_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("classes.id"), nullable=False
        ),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "class_id", name="uq_enrollment_user_class"),
    )


def downgrade() -> None:
    op.drop_table("enrollments")
    op.drop_table("classes")
    op.drop_table("users")
    class_status.drop(op.get_bind(), checkfirst=True)
    class_visibility.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
