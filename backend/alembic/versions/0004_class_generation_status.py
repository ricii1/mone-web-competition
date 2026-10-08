"""classes.generation_status and generation_error for level generation state

Revision ID: 0004
Revises: 0003
Create Date: 2026-10-08

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None

generation_status = postgresql.ENUM(
    "idle", "generating", "done", "failed", name="generation_status", create_type=False
)


def upgrade() -> None:
    generation_status.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "classes",
        sa.Column("generation_status", generation_status, nullable=False, server_default="idle"),
    )
    op.add_column("classes", sa.Column("generation_error", sa.Text, nullable=True))


def downgrade() -> None:
    op.drop_column("classes", "generation_error")
    op.drop_column("classes", "generation_status")
    generation_status.drop(op.get_bind(), checkfirst=True)
