"""Add app_settings table for runtime admin-configurable overrides."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0034_app_settings"
down_revision = "0033_totp"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_settings",
        sa.Column("key", sa.String(128), primary_key=True),
        sa.Column("value", sa.Text, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("app_settings")
