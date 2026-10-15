"""Track generation requests for safe stale-job recovery."""

import sqlalchemy as sa

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("classes", sa.Column("generation_job_id", sa.String(64), nullable=True))
    op.add_column(
        "classes", sa.Column("generation_requested_at", sa.DateTime(timezone=True), nullable=True)
    )

    # Legacy jobs get a migration-time grace period before stale recovery is considered.
    op.execute(
        sa.text(
            "UPDATE classes SET generation_requested_at = now() "
            "WHERE generation_status = 'generating'"
        )
    )


def downgrade() -> None:
    op.drop_column("classes", "generation_requested_at")
    op.drop_column("classes", "generation_job_id")
