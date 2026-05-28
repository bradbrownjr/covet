"""Add retro interface brute-force / ban tracking tables.

Revision ID: 0004_retro_security
Revises: 0003_standalone_chores
Create Date: 2026-05-28
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_retro_security"
down_revision: str | None = "0003_standalone_chores"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retro_login_attempts",
        sa.Column("id", sa.String(26), primary_key=True, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("interface", sa.String(16), nullable=False),
        sa.Column(
            "attempted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column("success", sa.Boolean, nullable=False, server_default=sa.text("0")),
    )
    op.create_index("ix_retro_login_attempts_ip_address", "retro_login_attempts", ["ip_address"])
    op.create_index("ix_retro_login_attempts_attempted_at", "retro_login_attempts", ["attempted_at"])

    op.create_table(
        "retro_banned_ips",
        sa.Column("id", sa.String(26), primary_key=True, nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=False),
        sa.Column("interface", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("banned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ban_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("admin_note", sa.String(500), nullable=True),
        sa.Column("unbanned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "unbanned_by_user_id",
            sa.String(26),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_retro_banned_ips_ip_address", "retro_banned_ips", ["ip_address"])


def downgrade() -> None:
    op.drop_index("ix_retro_banned_ips_ip_address", table_name="retro_banned_ips")
    op.drop_table("retro_banned_ips")
    op.drop_index("ix_retro_login_attempts_attempted_at", table_name="retro_login_attempts")
    op.drop_index("ix_retro_login_attempts_ip_address", table_name="retro_login_attempts")
    op.drop_table("retro_login_attempts")
