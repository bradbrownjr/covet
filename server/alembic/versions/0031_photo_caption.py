"""Add caption column to photos table.

Revision ID: 0031_photo_caption
Revises: 0030_notification_channels
Create Date: 2026-05-02
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0031_photo_caption"
down_revision = "0030_notification_channels"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("photos", sa.Column("caption", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("photos", "caption")
