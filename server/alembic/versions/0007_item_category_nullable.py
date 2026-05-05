"""Make items.category_id nullable.

Purchasing an ad-hoc shopping entry creates an inventory item even when no
category can be resolved (entry has no category_slug and the collection has
no default_category_slug). The NOT NULL constraint prevented this silently.

Revision ID: 0007_item_category_nullable
Revises: 0006_shopping_item_brand
Create Date: 2026-05-05

"""

from __future__ import annotations

from alembic import op

revision = "0007_item_category_nullable"
down_revision = "0006_shopping_item_brand"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("items") as batch_op:
        batch_op.alter_column("category_id", nullable=True)


def downgrade() -> None:
    # Re-applying NOT NULL would fail if any rows have category_id IS NULL.
    with op.batch_alter_table("items") as batch_op:
        batch_op.alter_column("category_id", nullable=False)
