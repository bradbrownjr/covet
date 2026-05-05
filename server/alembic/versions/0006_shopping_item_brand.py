"""Add brand column to grocery_items.

Revision ID: 0006_shopping_item_brand
Revises: 0005_barcode_category_hints
Create Date: 2026-05-05

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0006_shopping_item_brand"
down_revision = "0005_barcode_category_hints"
branch_labels = None
depends_on = None


def upgrade() -> None:
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    columns = [c["name"] for c in sa_inspect(bind).get_columns("grocery_items")]
    if "brand" not in columns:
        op.add_column("grocery_items", sa.Column("brand", sa.String(255), nullable=True))


def downgrade() -> None:
    op.drop_column("grocery_items", "brand")
