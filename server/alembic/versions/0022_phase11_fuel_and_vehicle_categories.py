"""add Phase 11 fuel/chemicals and vehicle categories

Revision ID: 0022_phase11_fuel_and_vehicle_categories
Revises: 0021_phase11_home_equipment_categories
Create Date: 2026-05-01
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op

from covet.models.base import ulid_str

revision: str = "0022_phase11_fuel_and_vehicle_categories"
down_revision: str | None = "0021_phase11_home_equipment_categories"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ROWS: list[tuple[str, str | None, str, str | None, int]] = [
    (
        "fuel_chemicals",
        None,
        "Fuel & Chemicals",
        "Stored fuels, lubricants, and household/shop chemicals.",
        101,
    ),
    (
        "fuel_chemicals.stored_fuel",
        "fuel_chemicals",
        "Stored Fuel",
        None,
        0,
    ),
    (
        "fuel_chemicals.lubricants_fluids",
        "fuel_chemicals",
        "Lubricants & Fluids",
        None,
        1,
    ),
    (
        "fuel_chemicals.chemicals_cleaning",
        "fuel_chemicals",
        "Chemicals & Cleaning",
        None,
        2,
    ),
    (
        "vehicles",
        None,
        "Vehicles",
        "Road, outdoor, and recreational vehicles/equipment.",
        102,
    ),
    (
        "vehicles.car_truck_suv",
        "vehicles",
        "Car / Truck / SUV",
        None,
        0,
    ),
    (
        "vehicles.motorcycle_atv_utv",
        "vehicles",
        "Motorcycle / ATV / UTV",
        None,
        1,
    ),
    (
        "vehicles.lawn_garden_equipment",
        "vehicles",
        "Lawn & Garden Equipment",
        None,
        2,
    ),
    ("vehicles.boat_pwc", "vehicles", "Boat / PWC", None, 3),
    ("vehicles.trailer", "vehicles", "Trailer", None, 4),
    ("vehicles.bicycle_ebike", "vehicles", "Bicycle / E-Bike", None, 5),
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
