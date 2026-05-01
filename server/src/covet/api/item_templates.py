"""ItemTemplate endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from covet.auth.deps import (
    AuthContext,
    collection_role,
    require_user,
)
from covet.db import get_session
from covet.models import Collection, Item, ItemTemplate
from covet.schemas import (
    ItemTemplateCreate,
    ItemTemplateRead,
    ItemTemplateUpdate,
    TemplateField,
)

router = APIRouter(tags=["item-templates"])

_EDITOR_ROLES = {"editor", "owner"}
_VIEWER_ROLES = {"viewer", "editor", "owner"}

# Seed templates offered per root category slug.
_SCAFFOLD: dict[str, list[dict]] = {
    "music": [
        {"name": "Vinyl", "category_slug": "music.vinyl", "fields": [
            {"key": "label", "label": "Label", "type": "text"},
            {"key": "catalog_no", "label": "Catalog #", "type": "text"},
            {"key": "pressing_year", "label": "Pressing year", "type": "number"},
            {"key": "matrix", "label": "Matrix / runout", "type": "text"},
        ]},
        {"name": "Compact Disc", "category_slug": "music.cd", "fields": [
            {"key": "label", "label": "Label", "type": "text"},
            {"key": "catalog_no", "label": "Catalog #", "type": "text"},
            {"key": "release_year", "label": "Release year", "type": "number"},
            {"key": "barcode", "label": "Barcode", "type": "text"},
        ]},
        {"name": "Cassette", "category_slug": "music.cassette", "fields": [
            {"key": "label", "label": "Label", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "tape_type", "label": "Tape type", "type": "select",
             "options": ["Type I", "Type II", "Type IV"]},
        ]},
        {"name": "8-Track", "category_slug": "music.eight_track", "fields": [
            {"key": "label", "label": "Label", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
        ]},
        {"name": "Reel-to-Reel", "category_slug": "music.reel", "fields": [
            {"key": "label", "label": "Label", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "speed", "label": "Speed (IPS)", "type": "select",
             "options": ["1⅞", "3¾", "7½", "15"]},
        ]},
    ],
    "movies": [
        {"name": "Blu-ray / 4K UHD", "category_slug": "movies.bluray", "fields": [
            {"key": "studio", "label": "Studio", "type": "text"},
            {"key": "release_year", "label": "Release year", "type": "number"},
            {"key": "region", "label": "Region", "type": "select",
             "options": ["A", "B", "C", "Free"]},
            {"key": "aspect_ratio", "label": "Aspect ratio", "type": "text"},
        ]},
        {"name": "DVD", "category_slug": "movies.dvd", "fields": [
            {"key": "studio", "label": "Studio", "type": "text"},
            {"key": "release_year", "label": "Release year", "type": "number"},
            {"key": "region", "label": "Region", "type": "select",
             "options": ["0", "1", "2", "3", "4", "5", "6"]},
        ]},
        {"name": "VHS", "category_slug": "movies.vhs", "fields": [
            {"key": "studio", "label": "Studio", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "format", "label": "Format", "type": "select",
             "options": ["NTSC", "PAL", "SECAM"]},
        ]},
    ],
    "books": [
        {"name": "Book", "category_slug": "books.print", "fields": [
            {"key": "publisher", "label": "Publisher", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "edition", "label": "Edition", "type": "text"},
            {"key": "format", "label": "Format", "type": "select",
             "options": ["Hardcover", "Paperback", "Trade"]},
            {"key": "isbn", "label": "ISBN", "type": "text"},
        ]},
        {"name": "Comic / Graphic Novel", "category_slug": "books.comic", "fields": [
            {"key": "publisher", "label": "Publisher", "type": "text"},
            {"key": "issue_no", "label": "Issue #", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "grade", "label": "Grade", "type": "text"},
        ]},
    ],
    "games": [
        {"name": "Game", "category_slug": "games.software", "fields": [
            {"key": "platform", "label": "Platform", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "region", "label": "Region", "type": "select",
             "options": ["NTSC", "PAL", "NTSC-J"]},
            {"key": "rating", "label": "Rating", "type": "select",
             "options": ["E", "E10+", "T", "M", "AO", "RP"]},
            {"key": "upc", "label": "UPC", "type": "text"},
        ]},
        {"name": "Console / Hardware", "category_slug": "games.console", "fields": [
            {"key": "manufacturer", "label": "Manufacturer", "type": "text"},
            {"key": "model", "label": "Model #", "type": "text"},
            {"key": "region", "label": "Region", "type": "select",
             "options": ["NTSC", "PAL", "NTSC-J"]},
        ]},
    ],
    "tabletop": [
        {"name": "Board Game", "category_slug": "tabletop.board_game", "fields": [
            {"key": "publisher", "label": "Publisher", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "players", "label": "Players", "type": "text"},
            {"key": "bgg_id", "label": "BGG ID", "type": "text"},
        ]},
        {"name": "RPG Book", "category_slug": "tabletop.rpg_book", "fields": [
            {"key": "publisher", "label": "Publisher", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "edition", "label": "Edition", "type": "text"},
        ]},
    ],
    "collectibles": [
        {"name": "Trading Card", "category_slug": "collectibles.trading_card", "fields": [
            {"key": "set", "label": "Set", "type": "text"},
            {"key": "card_number", "label": "Card #", "type": "text"},
            {"key": "grade", "label": "Grade", "type": "text"},
            {"key": "graded_by", "label": "Graded by", "type": "select",
             "options": ["PSA", "BGS", "CGC", "SGC", "Raw"]},
        ]},
        {"name": "Action Figure / Funko", "category_slug": "collectibles.action_figure", "fields": [
            {"key": "manufacturer", "label": "Manufacturer", "type": "text"},
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "box_condition", "label": "Box condition", "type": "text"},
        ]},
    ],
    "home_equipment": [
        {"name": "Appliance", "category_slug": "home_equipment.appliance", "fields": [
            {"key": "brand", "label": "Brand", "type": "text", "required": True},
            {"key": "model", "label": "Model", "type": "text", "required": True},
            {"key": "serial_number", "label": "Serial number", "type": "text"},
            {"key": "purchase_date", "label": "Purchase date", "type": "date"},
            {"key": "purchase_price", "label": "Purchase price", "type": "number"},
            {"key": "warranty_expiry", "label": "Warranty expiry", "type": "date"},
            {"key": "room", "label": "Room / location", "type": "text"},
            {"key": "last_service_date", "label": "Last service date", "type": "date"},
            {"key": "service_interval_days", "label": "Service interval (days)", "type": "number"},
        ]},
        {"name": "Generator", "category_slug": "home_equipment.generator", "fields": [
            {"key": "fuel_type", "label": "Fuel type", "type": "select", "options": ["gasoline", "propane", "dual-fuel", "diesel"]},
            {"key": "tank_capacity_gal", "label": "Tank capacity (gal)", "type": "number"},
            {"key": "last_run_date", "label": "Last run date", "type": "date"},
            {"key": "run_interval_days", "label": "Run interval (days)", "type": "number", "default": 30},
            {"key": "last_oil_change_date", "label": "Last oil change", "type": "date"},
            {"key": "oil_type", "label": "Oil type", "type": "text"},
        ]},
        {"name": "HVAC / Furnace / Air Handler", "category_slug": "home_equipment.hvac", "fields": [
            {"key": "system_type", "label": "System type", "type": "select", "options": ["central_air", "mini_split", "boiler", "heat_pump", "furnace"]},
            {"key": "filter_size", "label": "Filter size", "type": "text"},
            {"key": "filter_merv", "label": "Filter MERV", "type": "text"},
            {"key": "last_filter_change", "label": "Last filter change", "type": "date"},
            {"key": "filter_change_interval_days", "label": "Filter interval (days)", "type": "number", "default": 90},
            {"key": "last_professional_service", "label": "Last professional service", "type": "date"},
        ]},
    ],
    "fuel_chemicals": [
        {"name": "Stored Fuel", "category_slug": "fuel_chemicals.stored_fuel", "fields": [
            {"key": "fuel_type", "label": "Fuel type", "type": "select", "options": ["regular_gasoline", "ethanol_free", "premium", "diesel", "chainsaw_premix", "propane", "kerosene"]},
            {"key": "container_capacity_gal", "label": "Container capacity (gal)", "type": "number"},
            {"key": "quantity_on_hand_gal", "label": "Quantity on hand (gal)", "type": "number"},
            {"key": "purchase_date", "label": "Purchase date", "type": "date"},
            {"key": "stabilizer_added", "label": "Stabilizer added", "type": "boolean", "default": False},
            {"key": "stabilizer_added_date", "label": "Stabilizer added date", "type": "date"},
            {"key": "treat_by_date", "label": "Treat-by / expiry", "type": "date"},
            {"key": "intended_equipment", "label": "Intended equipment", "type": "text"},
        ]},
        {"name": "Lubricants & Fluids", "category_slug": "fuel_chemicals.lubricants_fluids", "fields": [
            {"key": "fluid_type", "label": "Fluid type", "type": "text", "required": True},
            {"key": "grade", "label": "Viscosity/grade", "type": "text"},
            {"key": "container_volume", "label": "Container volume", "type": "text"},
            {"key": "quantity_on_hand", "label": "Quantity on hand", "type": "number"},
            {"key": "purchase_date", "label": "Purchase date", "type": "date"},
            {"key": "expiry", "label": "Expiry", "type": "date"},
        ]},
        {"name": "Chemicals & Cleaning", "category_slug": "fuel_chemicals.chemicals_cleaning", "fields": [
            {"key": "purpose", "label": "Purpose", "type": "text"},
            {"key": "hazard_class", "label": "Hazard class", "type": "text"},
            {"key": "sds_url", "label": "SDS URL", "type": "url"},
            {"key": "purchase_date", "label": "Purchase date", "type": "date"},
            {"key": "expiry_date", "label": "Expiry date", "type": "date"},
        ]},
    ],
    "vehicles": [
        {"name": "Car / Truck / SUV", "category_slug": "vehicles.car_truck_suv", "fields": [
            {"key": "year", "label": "Year", "type": "number"},
            {"key": "make", "label": "Make", "type": "text", "required": True},
            {"key": "model", "label": "Model", "type": "text", "required": True},
            {"key": "vin", "label": "VIN", "type": "text"},
            {"key": "odometer", "label": "Odometer", "type": "number"},
            {"key": "fuel_type", "label": "Fuel type", "type": "text"},
            {"key": "last_oil_change_date", "label": "Last oil change date", "type": "date"},
            {"key": "last_oil_change_miles", "label": "Last oil change miles", "type": "number"},
            {"key": "oil_change_interval_miles", "label": "Oil interval miles", "type": "number", "default": 5000},
            {"key": "registration_expiry_date", "label": "Registration expiry", "type": "date"},
            {"key": "insurance_expiry_date", "label": "Insurance expiry", "type": "date"},
        ]},
        {"name": "Motorcycle / ATV / UTV", "category_slug": "vehicles.motorcycle_atv_utv", "fields": [
            {"key": "make", "label": "Make", "type": "text", "required": True},
            {"key": "model", "label": "Model", "type": "text", "required": True},
            {"key": "vin", "label": "VIN", "type": "text"},
            {"key": "last_chain_lubed", "label": "Last chain/belt lubed", "type": "date"},
            {"key": "last_air_filter_replaced", "label": "Last air filter replaced", "type": "date"},
        ]},
        {"name": "Lawn & Garden Equipment", "category_slug": "vehicles.lawn_garden_equipment", "fields": [
            {"key": "equipment_type", "label": "Equipment type", "type": "text"},
            {"key": "engine_spec", "label": "Engine cc/hp", "type": "text"},
            {"key": "fuel_type", "label": "Fuel type", "type": "text"},
            {"key": "last_oil_change_date", "label": "Last oil change date", "type": "date"},
            {"key": "last_oil_change_hours", "label": "Last oil change hours", "type": "number"},
            {"key": "oil_change_interval_hours", "label": "Oil interval hours", "type": "number", "default": 50},
            {"key": "last_blade_sharpen", "label": "Last blade sharpen", "type": "date"},
        ]},
    ],
}


def _require_role(
    db: DBSession, auth: AuthContext, collection_id: str, allowed: set[str]
) -> None:
    role = collection_role(db, auth.user, collection_id)
    if role is None or role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get(
    "/collections/{collection_id}/templates",
    response_model=list[ItemTemplateRead],
)
def list_templates(
    collection_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[ItemTemplateRead]:
    _require_role(db, auth, collection_id, _VIEWER_ROLES)
    rows = db.scalars(
        select(ItemTemplate)
        .where(ItemTemplate.collection_id == collection_id)
        .order_by(ItemTemplate.name)
    ).all()
    return [ItemTemplateRead.model_validate(r) for r in rows]


@router.post(
    "/collections/{collection_id}/templates",
    response_model=ItemTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def create_template(
    collection_id: str,
    payload: ItemTemplateCreate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> ItemTemplateRead:
    _require_role(db, auth, collection_id, _EDITOR_ROLES)
    tmpl = ItemTemplate(
        collection_id=collection_id,
        name=payload.name,
        category_slug=payload.category_slug,
        description=payload.description,
        fields=[f.model_dump() for f in payload.fields],
        created_by=auth.user.id,
    )
    db.add(tmpl)
    db.commit()
    db.refresh(tmpl)
    return ItemTemplateRead.model_validate(tmpl)


@router.get("/templates/{template_id}", response_model=ItemTemplateRead)
def get_template(
    template_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> ItemTemplateRead:
    tmpl = db.get(ItemTemplate, template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, tmpl.collection_id, _VIEWER_ROLES)
    return ItemTemplateRead.model_validate(tmpl)


@router.patch("/templates/{template_id}", response_model=ItemTemplateRead)
def update_template(
    template_id: str,
    payload: ItemTemplateUpdate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> ItemTemplateRead:
    tmpl = db.get(ItemTemplate, template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, tmpl.collection_id, _EDITOR_ROLES)
    data = payload.model_dump(exclude_unset=True)
    if "fields" in data and data["fields"] is not None:
        data["fields"] = [f if isinstance(f, dict) else f.model_dump() for f in data["fields"]]
    for k, v in data.items():
        setattr(tmpl, k, v)
    db.commit()
    db.refresh(tmpl)
    return ItemTemplateRead.model_validate(tmpl)


@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> None:
    tmpl = db.get(ItemTemplate, template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, tmpl.collection_id, _EDITOR_ROLES)
    db.delete(tmpl)
    db.commit()


@router.post(
    "/templates/{template_id}/clone",
    response_model=ItemTemplateRead,
    status_code=status.HTTP_201_CREATED,
)
def clone_template(
    template_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> ItemTemplateRead:
    """Duplicate a template within the same collection."""
    tmpl = db.get(ItemTemplate, template_id)
    if tmpl is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, tmpl.collection_id, _EDITOR_ROLES)
    clone = ItemTemplate(
        collection_id=tmpl.collection_id,
        name=f"{tmpl.name} (copy)",
        category_slug=tmpl.category_slug,
        description=tmpl.description,
        fields=list(tmpl.fields),
        created_by=auth.user.id,
    )
    db.add(clone)
    db.commit()
    db.refresh(clone)
    return ItemTemplateRead.model_validate(clone)


# ---------------------------------------------------------------------------
# Scaffold helper (also called by create_collection)
# ---------------------------------------------------------------------------


def _do_scaffold(
    db: DBSession,
    collection_id: str,
    default_category_slug: str | None,
    created_by: str,
) -> None:
    """Seed default templates for *collection_id*.

    Idempotent: skips names that already exist. Does NOT commit — caller is
    responsible for committing the surrounding transaction.
    """
    root = (default_category_slug or "").split(".")[0]
    seeds = _SCAFFOLD.get(root, [])
    if not seeds:
        return

    existing_names = set(
        db.scalars(
            select(ItemTemplate.name).where(ItemTemplate.collection_id == collection_id)
        ).all()
    )

    for seed in seeds:
        if seed["name"] in existing_names:
            continue
        db.add(ItemTemplate(
            collection_id=collection_id,
            name=seed["name"],
            category_slug=seed["category_slug"],
            fields=seed["fields"],
            created_by=created_by,
        ))


@router.get(
    "/collections/{collection_id}/scaffold-templates",
    response_model=list[str],
)
def scaffold_template_names(
    collection_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[str]:
    """Return the names of default templates available for this collection's type."""
    _require_role(db, auth, collection_id, _VIEWER_ROLES)
    coll = db.get(Collection, collection_id)
    if coll is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    root = (coll.default_category_slug or "").split(".")[0]
    return [s["name"] for s in _SCAFFOLD.get(root, [])]


@router.post(
    "/collections/{collection_id}/scaffold-templates",
    response_model=list[ItemTemplateRead],
    status_code=status.HTTP_201_CREATED,
)
def scaffold_templates(
    collection_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[ItemTemplateRead]:
    """Create sensible default templates for the collection's root category.

    Skips any template whose name already exists in the collection, so the
    endpoint is safe to call multiple times.
    """
    _require_role(db, auth, collection_id, _EDITOR_ROLES)
    coll = db.get(Collection, collection_id)
    if coll is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    _do_scaffold(db, collection_id, coll.default_category_slug, auth.user.id)
    db.commit()

    rows = db.scalars(
        select(ItemTemplate)
        .where(ItemTemplate.collection_id == collection_id)
        .order_by(ItemTemplate.name)
    ).all()
    return [ItemTemplateRead.model_validate(t) for t in rows]


@router.get(
    "/collections/{collection_id}/template-field-options/{field_key}",
    response_model=list[str],
)
def template_field_options(
    collection_id: str,
    field_key: str,
    template_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[str]:
    """Return dropdown options for a template select field.

    - Static fields return their declared options.
    - Dynamic fields return distinct values already used in item attrs.
    """
    _require_role(db, auth, collection_id, _VIEWER_ROLES)
    tmpl = db.get(ItemTemplate, template_id)
    if tmpl is None or tmpl.collection_id != collection_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")

    fields = [TemplateField.model_validate(f) for f in tmpl.fields]
    spec = next((f for f in fields if f.key == field_key), None)
    if spec is None or spec.type != "select":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Field is not a select field in this template",
        )

    if spec.select_source == "static":
        return list(spec.options or [])

    attr_rows = db.scalars(select(Item.attrs).where(Item.collection_id == collection_id)).all()
    seen: set[str] = set()
    for attrs in attr_rows:
        if not isinstance(attrs, dict):
            continue
        raw = attrs.get(field_key)
        if raw is None:
            continue
        sval = str(raw).strip()
        if sval:
            seen.add(sval)
    return sorted(seen, key=str.casefold)


# ---------------------------------------------------------------------------
# Validation helpers (used by items API)
# ---------------------------------------------------------------------------


def validate_attrs(
    db: DBSession,
    template: ItemTemplate,
    attrs: dict[str, Any],
    *,
    collection_id: str,
) -> dict[str, Any]:
    """Validate ``attrs`` against ``template.fields``.

    Returns the (possibly coerced) attrs dict; raises HTTPException on error.
    Unknown keys are preserved as-is so callers can carry forward legacy data.
    """
    out: dict[str, Any] = dict(attrs)
    field_specs: list[TemplateField] = [TemplateField.model_validate(f) for f in template.fields]
    for spec in field_specs:
        value = out.get(spec.key)
        if value is None or value == "":
            if spec.required:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Field '{spec.key}' is required",
                )
            if spec.default is not None and spec.key not in out:
                out[spec.key] = spec.default
            continue
        out[spec.key] = _coerce(db, spec, value, collection_id=collection_id)
    return out


def _coerce(db: DBSession, spec: TemplateField, value: Any, *, collection_id: str) -> Any:
    t = spec.type
    try:
        if t == "text" or t == "url":
            return str(value)
        if t == "number":
            return float(value)
        if t == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.lower() in {"1", "true", "yes", "on"}
            return bool(value)
        if t == "date":
            if isinstance(value, datetime):
                return value.isoformat()
            return str(value)
        if t == "multi_value":
            if isinstance(value, (list, tuple)):
                return [str(v).strip() for v in value if str(v).strip()]
            if isinstance(value, str):
                # Accept comma-delimited text for compatibility with simple clients.
                return [v.strip() for v in value.split(",") if v.strip()]
            raise ValueError("must be an array of values or a comma-separated string")
        if t == "select":
            sval = str(value)
            if spec.select_source == "static" and spec.options and sval not in spec.options:
                raise ValueError(
                    f"value '{sval}' not in allowed options for '{spec.key}'"
                )
            return sval
        if t == "relation":
            target_id = str(value).strip()
            if not target_id:
                raise ValueError("must reference an item id")
            target = db.get(Item, target_id)
            if target is None:
                raise ValueError("target item not found")
            if spec.relation_scope == "same_collection" and target.collection_id != collection_id:
                raise ValueError("target item must be in the same collection")
            return target_id
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Field '{spec.key}': {exc}",
        ) from exc
    return value
