"""levels.source_note (free-text source written by the teacher)

Revision ID: 0007
Revises: 0006
Create Date: 2026-10-09

"""

import sqlalchemy as sa

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("levels", sa.Column("source_note", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("levels", "source_note")
