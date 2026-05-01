"""add buyer_id to items for disposition tracking

Revision ID: 0019_item_disposition_buyer
Revises: 0018_webhooks
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0019_item_disposition_buyer"
down_revision: str | None = "0018_webhooks"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add buyer_id column to items table
    op.add_column(
        "items",
        sa.Column(
            "buyer_id",
            sa.String(length=26),
            nullable=True,
        ),
    )

    # Use batch mode for SQLite compatibility
    with op.batch_alter_table("items", schema=None) as batch_op:
        # Add foreign key constraint for buyer_id
        batch_op.create_foreign_key(
            "fk_items_buyer_id",
            "contacts",
            ["buyer_id"],
            ["id"],
            ondelete="SET NULL",
        )

        # Create index for efficient queries
        batch_op.create_index("ix_items_buyer_id", ["buyer_id"])


def downgrade() -> None:
    with op.batch_alter_table("items", schema=None) as batch_op:
        batch_op.drop_index("ix_items_buyer_id")
        batch_op.drop_constraint("fk_items_buyer_id", type_="foreignkey")
    op.drop_column("items", "buyer_id")
