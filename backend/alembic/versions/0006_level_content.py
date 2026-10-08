"""levels.content (detailed lesson article, Markdown subset)

Revision ID: 0006
Revises: 0005
Create Date: 2026-10-09

"""

import sqlalchemy as sa

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("levels", sa.Column("content", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("levels", "content")
