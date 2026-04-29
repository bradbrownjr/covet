"""Maintenance tasks + items.parent_id.

Revision ID: 0006_maintenance_parent
Revises: 0005_documents
Create Date: 2026-04-29
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_maintenance_parent"
down_revision: str | None = "0005_documents"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "maintenance_tasks",
        sa.Column("id", sa.String(length=26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("item_id", sa.String(length=26), nullable=False),
        sa.Column("name", sa.String(length=128), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("interval_days", sa.Integer(), nullable=True),
        sa.Column("last_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("next_due_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["item_id"], ["items.id"],
            ondelete="CASCADE", name="fk_maintenance_tasks_item_id",
        ),
    )
    op.create_index(
        "ix_maintenance_tasks_item_id", "maintenance_tasks", ["item_id"]
    )
    op.create_index(
        "ix_maintenance_tasks_next_due_at", "maintenance_tasks", ["next_due_at"]
    )

    with op.batch_alter_table("items") as batch:
        batch.add_column(sa.Column("parent_id", sa.String(length=26), nullable=True))
        batch.create_foreign_key(
            "fk_items_parent_id", "items", ["parent_id"], ["id"],
            ondelete="SET NULL",
        )
        batch.create_index("ix_items_parent_id", ["parent_id"])


def downgrade() -> None:
    with op.batch_alter_table("items") as batch:
        batch.drop_index("ix_items_parent_id")
        batch.drop_constraint("fk_items_parent_id", type_="foreignkey")
        batch.drop_column("parent_id")
    op.drop_index("ix_maintenance_tasks_next_due_at", table_name="maintenance_tasks")
    op.drop_index("ix_maintenance_tasks_item_id", table_name="maintenance_tasks")
    op.drop_table("maintenance_tasks")
