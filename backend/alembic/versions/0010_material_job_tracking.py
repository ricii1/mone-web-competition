"""Identify material jobs so stale retries cannot overwrite newer work."""

import sqlalchemy as sa

from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("materials", sa.Column("processing_job_id", sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column("materials", "processing_job_id")
