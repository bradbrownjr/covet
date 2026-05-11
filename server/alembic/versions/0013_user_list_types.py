"""Add user_list_types table for custom shopping list types.

Revision ID: 0013_user_list_types
Revises: 0012_collection_theme
Create Date: 2026-05-11
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0013_user_list_types"
down_revision = "0012_collection_theme"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_tables = inspector.get_table_names()
    if "user_list_types" not in existing_tables:
        op.create_table(
            "user_list_types",
            sa.Column("id", sa.String(26), primary_key=True),
            sa.Column(
                "user_id",
                sa.String(26),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            ),
            sa.Column("slug", sa.String(64), nullable=False),
            sa.Column("label", sa.String(120), nullable=False),
            sa.Column("icon", sa.String(64), nullable=True),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index(
            "ix_user_list_types_user_id",
            "user_list_types",
            ["user_id"],
        )
        op.create_index(
            "ix_user_list_types_user_slug",
            "user_list_types",
            ["user_id", "slug"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("ix_user_list_types_user_slug", table_name="user_list_types")
    op.drop_index("ix_user_list_types_user_id", table_name="user_list_types")
    op.drop_table("user_list_types")
