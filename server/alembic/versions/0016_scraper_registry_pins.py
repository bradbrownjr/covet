"""add scraper registry trust pins

Revision ID: 0016_scraper_registry_pins
Revises: 0015_item_archive_workflow
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016_scraper_registry_pins"
down_revision: str | None = "0015_item_archive_workflow"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scraper_registry_pins",
        sa.Column("entry_id", sa.String(length=128), nullable=False),
        sa.Column("trusted", sa.Boolean(), nullable=False),
        sa.Column("updated_by", sa.String(length=26), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("entry_id"),
    )


def downgrade() -> None:
    op.drop_table("scraper_registry_pins")
