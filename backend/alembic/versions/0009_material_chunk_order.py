"""Persist the order of PDF sections, including sections on the same page."""

import sqlalchemy as sa

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "material_chunks",
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
    )
    # Old chunks have no offsets; backfill a stable page order without replacing teacher content.
    op.execute(
        sa.text("""
        WITH ordered AS (
            SELECT id, row_number() OVER (
                PARTITION BY material_id ORDER BY page_start, page_end, id
            ) - 1 AS position
            FROM material_chunks
        )
        UPDATE material_chunks SET order_index = ordered.position
        FROM ordered WHERE material_chunks.id = ordered.id
    """)
    )
    op.create_index(
        "ix_material_chunks_material_order", "material_chunks", ["material_id", "order_index"]
    )


def downgrade() -> None:
    op.drop_index("ix_material_chunks_material_order", table_name="material_chunks")
    op.drop_column("material_chunks", "order_index")
