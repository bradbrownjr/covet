"""add Phase 11 home equipment categories

Revision ID: 0021_phase11_home_equipment_categories
Revises: 0020_document_search_text
Create Date: 2026-05-01
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from covet.models.base import ulid_str

revision: str = "0021_phase11_home_equipment_categories"
down_revision: str | None = "0020_document_search_text"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROOT_SLUG = "home_equipment"
ROWS: list[tuple[str, str | None, str, str | None, int]] = [
    (
        "home_equipment",
        None,
        "Home Equipment",
        "Appliances and household infrastructure.",
        100,
    ),
    ("home_equipment.appliance", ROOT_SLUG, "Appliance", None, 0),
    ("home_equipment.generator", ROOT_SLUG, "Generator", None, 1),
    ("home_equipment.hvac", ROOT_SLUG, "HVAC / Furnace / Air Handler", None, 2),
    ("home_equipment.water_heater", ROOT_SLUG, "Water Heater", None, 3),
    ("home_equipment.refrigerator", ROOT_SLUG, "Refrigerator", None, 4),
    (
        "home_equipment.water_filtration",
        ROOT_SLUG,
        "Water Service Filtration",
        None,
        5,
    ),
    ("home_equipment.sump_pump", ROOT_SLUG, "Sump Pump", None, 6),
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
