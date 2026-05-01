"""add Phase 11 sports & recreation, tools, and pantry enhancements

Revision ID: 0024_phase11_sports_tools_pantry
Revises: 0023_phase11_batteries_clothing_art_decor
Create Date: 2026-05-01
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from covet.models.base import ulid_str

revision: str = "0024_phase11_sports_tools_pantry"
down_revision: str | None = "0023_phase11_batteries_clothing_art_decor"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROWS: list[tuple[str, str | None, str, str | None, int]] = [
    (
        "sports",
        None,
        "Sports & Recreation",
        "Fitness, outdoor, and recreational sports equipment.",
        106,
    ),
    (
        "sports.fitness",
        "sports",
        "Fitness Equipment",
        None,
        0,
    ),
    (
        "sports.outdoor",
        "sports",
        "Outdoor Gear",
        None,
        1,
    ),
    (
        "sports.sports_equipment",
        "sports",
        "Sports Equipment",
        None,
        2,
    ),
]


def _load_existing_ids(bind: sa.engine.Connection, slugs: list[str]) -> dict[str, str]:
    stmt = sa.text("SELECT id, slug FROM categories WHERE slug IN :slugs").bindparams(
        sa.bindparam("slugs", expanding=True)
    )
    rows = bind.execute(stmt, {"slugs": slugs}).all()
    return {slug: cid for cid, slug in rows}


def upgrade() -> None:
    bind = op.get_bind()
    now = datetime.now(UTC)
    slugs = [slug for slug, *_ in ROWS]
    existing_ids = _load_existing_ids(bind, slugs)

    for slug, parent_slug, name, description, position in ROWS:
        parent_id = existing_ids.get(parent_slug) if parent_slug else None
        existing_id = existing_ids.get(slug)

        if existing_id:
            bind.execute(
                sa.text(
                    "UPDATE categories SET "
                    "updated_at = :ts, "
                    "parent_id = :parent_id, "
                    "name = :name, "
                    "description = :description, "
                    "position = :position, "
                    "is_system = :is_system, "
                    "is_active = :is_active "
                    "WHERE id = :id"
                ),
                {
                    "id": existing_id,
                    "ts": now,
                    "parent_id": parent_id,
                    "name": name,
                    "description": description,
                    "position": position,
                    "is_system": True,
                    "is_active": True,
                },
            )
            continue

        cid = ulid_str()
        bind.execute(
            sa.text(
                "INSERT INTO categories "
                "(id, created_at, updated_at, parent_id, slug, name, description, "
                "position, is_system, is_active) "
                "VALUES (:id, :ts, :ts, :parent_id, :slug, :name, :description, "
                ":position, :is_system, :is_active)"
            ),
            {
                "id": cid,
                "ts": now,
                "parent_id": parent_id,
                "slug": slug,
                "name": name,
                "description": description,
                "position": position,
                "is_system": True,
                "is_active": True,
            },
        )
        existing_ids[slug] = cid


def downgrade() -> None:
    bind = op.get_bind()
    slugs = [slug for slug, *_ in ROWS]
    stmt = sa.text("UPDATE categories SET is_active = :active WHERE slug IN :slugs").bindparams(
        sa.bindparam("slugs", expanding=True)
    )
    bind.execute(stmt, {"active": False, "slugs": slugs})
