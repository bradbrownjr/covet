"""Add collections.default_category_slug.

Revision ID: 0009_collection_default_category
Revises: 0008_categories
Create Date: 2026-04-30
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_collection_default_category"
down_revision: str | None = "0008_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "collections",
        sa.Column("default_category_slug", sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("collections", "default_category_slug")
