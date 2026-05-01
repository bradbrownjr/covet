"""add searchable text index to documents

Revision ID: 0020_document_search_text
Revises: 0019_item_disposition_buyer
Create Date: 2026-05-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0020_document_search_text"
down_revision: str | None = "0019_item_disposition_buyer"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("search_text", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("documents", "search_text")
