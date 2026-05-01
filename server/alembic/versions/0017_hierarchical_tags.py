"""add parent_id to tags for hierarchical structure

Revision ID: 0017_hierarchical_tags
Revises: 0016_scraper_registry_pins
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0017_hierarchical_tags"
down_revision: str | None = "0016_scraper_registry_pins"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # Add parent_id column to tags table
    op.add_column(
        "tags",
        sa.Column(
            "parent_id",
            sa.String(length=26),
            nullable=True,
        ),
    )

    # Use batch mode for SQLite compatibility when altering constraints
    with op.batch_alter_table("tags", schema=None) as batch_op:
        # Add foreign key constraint for parent_id
        batch_op.create_foreign_key(
            "fk_tags_parent_id",
            "tags",
            ["parent_id"],
            ["id"],
            ondelete="SET NULL",
        )

        # Drop the old unique constraint
        batch_op.drop_constraint("uq_tag_owner_name", type_="unique")

        # Create new unique constraint that allows same name under different parents
        batch_op.create_unique_constraint(
            "uq_tag_owner_parent_name",
            ["owner_id", "parent_id", "name"],
        )

        # Create index for efficient queries
        batch_op.create_index("ix_tags_parent_id", ["parent_id"])


def downgrade() -> None:
    with op.batch_alter_table("tags", schema=None) as batch_op:
        batch_op.drop_index("ix_tags_parent_id")
        batch_op.drop_constraint("uq_tag_owner_parent_name", type_="unique")
        batch_op.create_unique_constraint("uq_tag_owner_name", ["owner_id", "name"])
        batch_op.drop_constraint("fk_tags_parent_id", type_="foreignkey")
    op.drop_column("tags", "parent_id")
