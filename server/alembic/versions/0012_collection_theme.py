"""Add theme column to collections.

Revision ID: 0012_collection_theme
Revises: 0011_task_assignment
Create Date: 2026-05-09
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0012_collection_theme"
down_revision = "0011_task_assignment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("collections") as batch_op:
        batch_op.add_column(
            sa.Column("theme", sa.String(32), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("collections") as batch_op:
        batch_op.drop_column("theme")
