"""add item review flags

Revision ID: 0013_item_flags
Revises: 0012_item_lots
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013_item_flags"
down_revision: str | None = "0012_item_lots"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("items", sa.Column("flagged_note", sa.String(length=256), nullable=True))
    op.add_column("items", sa.Column("flagged_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_items_flagged_at"), "items", ["flagged_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_items_flagged_at"), table_name="items")
    op.drop_column("items", "flagged_at")
    op.drop_column("items", "flagged_note")
