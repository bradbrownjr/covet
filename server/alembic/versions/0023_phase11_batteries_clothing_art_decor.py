"""add Phase 11 batteries, clothing, and art/decor categories

Revision ID: 0023_phase11_batteries_clothing_art_decor
Revises: 0022_phase11_fuel_and_vehicle_categories
Create Date: 2026-05-01
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from covet.models.base import ulid_str

revision: str = "0023_phase11_batteries_clothing_art_decor"
down_revision: str | None = "0022_phase11_fuel_and_vehicle_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROWS: list[tuple[str, str | None, str, str | None, int]] = [
    (
        "batteries",
        None,
        "Batteries",
        "Rechargeable and disposable batteries, including specialized types.",
        103,
    ),
    (
        "batteries.rechargeable",
        "batteries",
        "Rechargeable Battery",
        None,
        0,
    ),
    (
        "batteries.disposable",
        "batteries",
        "Disposable Battery",
        None,
        1,
    ),
    (
        "batteries.smoke_detector",
        "batteries",
        "Smoke Detector Battery Program",
        None,
        2,
    ),
    (
        "clothing",
        None,
        "Clothing & Wardrobe",
        "Apparel, footwear, and fashion accessories.",
        104,
    ),
    (
        "clothing.clothing_item",
        "clothing",
        "Clothing Item",
        None,
        0,
    ),
    (
        "clothing.footwear",
        "clothing",
        "Footwear",
        None,
        1,
    ),
    (
        "clothing.accessories",
        "clothing",
        "Accessories",
        None,
        2,
    ),
    (
        "art_decor",
        None,
        "Art & Décor",
        "Artwork, framed prints, decorative objects.",
        105,
    ),
    (
        "art_decor.artwork",
        "art_decor",
        "Artwork",
        None,
        0,
    ),
    (
        "art_decor.framed_print",
        "art_decor",
        "Framed Print / Poster",
        None,
        1,
    ),
    (
        "art_decor.decorative_object",
        "art_decor",
        "Decorative Object",
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
