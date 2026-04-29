"""Import + backup endpoints."""

from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session as DBSession

from covet.auth.deps import (
    AuthContext,
    collection_role,
    require_user,
)
from covet.db import get_session
from covet.importers import CLZ_IMPORTERS, BackupStats, CSVImporter, export_user, import_backup
from covet.models import Item

router = APIRouter(prefix="/imports", tags=["imports"])

_EDITOR_ROLES = {"editor", "owner"}


def _check_collection(db: DBSession, auth: AuthContext, collection_id: str) -> None:
    role = collection_role(db, auth.user, collection_id)
    if role is None or role not in _EDITOR_ROLES:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _persist_items(
    db: DBSession, *, collection_id: str, items_data: list[dict]
) -> int:
    count = 0
    for raw in items_data:
        db.add(
            Item(
                collection_id=collection_id,
                type=raw["type"],
                title=raw["title"],
                subtitle=raw.get("subtitle"),
                notes=raw.get("notes"),
                condition=raw.get("condition"),
                quantity=int(raw.get("quantity", 1)),
                purchase_price=raw.get("purchase_price"),
                current_value=raw.get("current_value"),
                currency=raw.get("currency"),
                location=raw.get("location"),
                identifiers=raw.get("identifiers", {}) or {},
                attrs=raw.get("attrs", {}) or {},
            )
        )
        count += 1
    db.commit()
    return count


@router.post("/clz", status_code=status.HTTP_200_OK)
async def import_clz(
    collection_id: Annotated[str, Form(...)],
    flavor: Annotated[str, Form(..., description="One of: clz-movie/music/book/comic/game")],
    file: Annotated[UploadFile, File(...)],
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> dict:
    _check_collection(db, auth, collection_id)
    importer_cls = CLZ_IMPORTERS.get(flavor)
    if importer_cls is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown CLZ flavor: {flavor}",
        )
    importer = importer_cls()
    result = importer.parse(file.file)
    inserted = _persist_items(
        db,
        collection_id=collection_id,
        items_data=[
            {
                "type": i.type,
                "title": i.title,
                "subtitle": i.subtitle,
                "notes": i.notes,
                "condition": i.condition,
                "quantity": i.quantity,
                "purchase_price": i.purchase_price,
                "current_value": i.current_value,
                "currency": i.currency,
                "location": i.location,
                "identifiers": i.identifiers,
                "attrs": i.attrs,
            }
            for i in result.items
        ],
    )
    return {"imported": inserted, "warnings": result.warnings}


@router.post("/csv", status_code=status.HTTP_200_OK)
async def import_csv(
    collection_id: Annotated[str, Form(...)],
    item_type: Annotated[str, Form(..., description="movie|music|book|comic|game|other")],
    mapping: Annotated[str, Form(..., description="JSON object: csv_header → target field")],
    file: Annotated[UploadFile, File(...)],
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> dict:
    _check_collection(db, auth, collection_id)
    try:
        column_map = json.loads(mapping)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"mapping is not valid JSON: {exc}",
        ) from exc
    if not isinstance(column_map, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mapping must be a JSON object",
        )
    importer = CSVImporter(item_type=item_type, mapping=column_map)
    result = importer.parse(file.file)
    inserted = _persist_items(
        db,
        collection_id=collection_id,
        items_data=[
            {
                "type": i.type,
                "title": i.title,
                "subtitle": i.subtitle,
                "notes": i.notes,
                "condition": i.condition,
                "quantity": i.quantity,
                "purchase_price": i.purchase_price,
                "current_value": i.current_value,
                "currency": i.currency,
                "location": i.location,
                "identifiers": i.identifiers,
                "attrs": i.attrs,
            }
            for i in result.items
        ],
    )
    return {"imported": inserted, "warnings": result.warnings}


@router.get("/backup", status_code=status.HTTP_200_OK)
def download_backup(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> JSONResponse:
    payload = export_user(db, user=auth.user)
    return JSONResponse(
        payload,
        headers={"content-disposition": 'attachment; filename="covet-backup.json"'},
    )


@router.post("/restore", status_code=status.HTTP_200_OK)
async def upload_backup(
    file: Annotated[UploadFile, File(...)],
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> BackupStats:
    raw = await file.read()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid backup file: {exc}",
        ) from exc
    try:
        return import_backup(db, user=auth.user, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
