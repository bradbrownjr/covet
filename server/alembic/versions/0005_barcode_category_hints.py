"""Add barcode_category_hints table.

Revision ID: 0005_barcode_category_hints
Revises: 0004_shopping_list_type
Create Date: 2026-05-04
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005_barcode_category_hints"
down_revision: str | None = "0004_shopping_list_type"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    from sqlalchemy import inspect as sa_inspect

    bind = op.get_bind()
    existing_tables = sa_inspect(bind).get_table_names()
    if "barcode_category_hints" not in existing_tables:
        op.create_table(
            "barcode_category_hints",
            sa.Column("barcode", sa.String(18), primary_key=True),
            sa.Column("category_slug", sa.String(120), nullable=False),
            sa.Column(
                "list_type",
                sa.String(32),
                nullable=False,
                server_default="groceries",
            ),
            sa.Column("hit_count", sa.Integer, nullable=False, server_default="1"),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        )


def downgrade() -> None:
    op.drop_table("barcode_category_hints")
