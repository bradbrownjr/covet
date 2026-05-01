"""add webhooks and webhook_deliveries tables

Revision ID: 0018_webhooks
Revises: 0017_hierarchical_tags
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0018_webhooks"
down_revision: str | None = "0017_hierarchical_tags"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "webhooks",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("collection_id", sa.String(length=26), nullable=False),
        sa.Column("owner_id", sa.String(length=26), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("secret", sa.String(length=64), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("events", sa.String(length=256), nullable=False, server_default="item.created,item.updated,item.deleted"),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("retry_delay_seconds", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["collection_id"], ["collections.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("collection_id", "url", name="uq_webhook_collection_url"),
    )
    op.create_index("ix_webhooks_collection_id", "webhooks", ["collection_id"])
    op.create_index("ix_webhooks_owner_id", "webhooks", ["owner_id"])

    op.create_table(
        "webhook_deliveries",
        sa.Column("id", sa.String(length=26), nullable=False),
        sa.Column("webhook_id", sa.String(length=26), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("next_retry_at", sa.String(length=30), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["webhook_id"], ["webhooks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries", ["webhook_id"])


def downgrade() -> None:
    op.drop_index("ix_webhook_deliveries_webhook_id", "webhook_deliveries")
    op.drop_table("webhook_deliveries")
    op.drop_index("ix_webhooks_owner_id", "webhooks")
    op.drop_index("ix_webhooks_collection_id", "webhooks")
    op.drop_table("webhooks")
