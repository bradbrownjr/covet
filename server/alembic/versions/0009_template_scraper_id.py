"""Add scraper_id to item_templates.

Tracks which community registry entry a template was imported from, enabling
the UI to show "Linked to: <registry name>" and avoiding duplicate imports
without relying on a description marker.

Revision ID: 0009_template_scraper_id
Revises: 0008_item_lot_idempotency_key
Create Date: 2026-05-20

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0009_template_scraper_id"
down_revision = "0008_item_lot_idempotency_key"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("item_templates") as batch_op:
        batch_op.add_column(
            sa.Column("scraper_id", sa.String(128), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("item_templates") as batch_op:
        batch_op.drop_column("scraper_id")
