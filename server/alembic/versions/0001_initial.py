"""Initial schema.

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("username", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("email", sa.String(255), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "oidc_identities",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("raw_claims", sa.String(), nullable=True),
        sa.UniqueConstraint("provider", "subject", name="uq_oidc_provider_subject"),
    )

    op.create_table(
        "api_tokens",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("token_hash", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("ip_address", sa.String(64), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "collections",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("description", sa.String(2048), nullable=True),
        sa.Column("icon", sa.String(64), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "collection_memberships",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_id", sa.String(26), sa.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("user_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("role", sa.String(16), nullable=False),
        sa.UniqueConstraint("collection_id", "user_id", name="uq_membership_collection_user"),
    )

    op.create_table(
        "automerge_docs",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_id", sa.String(26), sa.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("snapshot", sa.LargeBinary(), nullable=True),
        sa.Column("head_hash", sa.String(64), nullable=True),
    )

    op.create_table(
        "automerge_changes",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("doc_id", sa.String(26), sa.ForeignKey("automerge_docs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("server_seq", sa.Integer(), nullable=False, index=True),
        sa.Column("change_hash", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.String(64), nullable=False),
        sa.Column("blob", sa.LargeBinary(), nullable=False),
        sa.UniqueConstraint("doc_id", "change_hash", name="uq_change_doc_hash"),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_id", sa.String(26), sa.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(32), nullable=False, index=True),
        sa.Column("title", sa.String(512), nullable=False, index=True),
        sa.Column("subtitle", sa.String(512), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("condition", sa.String(32), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("purchase_price", sa.Numeric(12, 2), nullable=True),
        sa.Column("current_value", sa.Numeric(12, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=True),
        sa.Column("acquired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("location", sa.String(256), nullable=True),
        sa.Column("identifiers", sa.JSON(), nullable=False),
        sa.Column("attrs", sa.JSON(), nullable=False),
        sa.Column("doc_id", sa.String(26), sa.ForeignKey("automerge_docs.id", ondelete="SET NULL"), nullable=True),
    )

    op.create_table(
        "photos",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("item_id", sa.String(26), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("storage_key", sa.String(128), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False, index=True),
        sa.Column("mime_type", sa.String(64), nullable=False),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("byte_size", sa.Integer(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("color", sa.String(16), nullable=True),
        sa.UniqueConstraint("owner_id", "name", name="uq_tag_owner_name"),
    )

    op.create_table(
        "item_tags",
        sa.Column("item_id", sa.String(26), sa.ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tag_id", sa.String(26), sa.ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "contacts",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("owner_id", sa.String(26), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("name", sa.String(128), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(64), nullable=True),
        sa.Column("notes", sa.String(2048), nullable=True),
    )

    op.create_table(
        "loans",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("item_id", sa.String(26), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("contact_id", sa.String(26), sa.ForeignKey("contacts.id", ondelete="RESTRICT"), nullable=False, index=True),
        sa.Column("loaned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("returned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String(2048), nullable=True),
    )

    op.create_table(
        "share_links",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("collection_id", sa.String(26), sa.ForeignKey("collections.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("slug", sa.String(64), nullable=False, unique=True, index=True),
        sa.Column("label", sa.String(128), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked", sa.Boolean(), nullable=False),
    )

    op.create_table(
        "metadata_cache",
        sa.Column("id", sa.String(26), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider", sa.String(32), nullable=False, index=True),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("provider", "external_id", name="uq_metadata_provider_external"),
    )


def downgrade() -> None:
    for table in (
        "metadata_cache",
        "share_links",
        "loans",
        "contacts",
        "item_tags",
        "tags",
        "photos",
        "items",
        "automerge_changes",
        "automerge_docs",
        "collection_memberships",
        "collections",
        "sessions",
        "api_tokens",
        "oidc_identities",
        "users",
    ):
        op.drop_table(table)
