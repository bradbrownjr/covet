"""Collection endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session as DBSession

from covet.auth.deps import (
    AuthContext,
    require_collection_role,
    require_user,
)
from covet.db import get_session
from covet.models import Collection, CollectionMembership
from covet.schemas import CollectionCreate, CollectionRead, CollectionUpdate

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get("", response_model=list[CollectionRead])
def list_collections(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[CollectionRead]:
    stmt = (
        select(Collection)
        .outerjoin(
            CollectionMembership,
            CollectionMembership.collection_id == Collection.id,
        )
        .where(
            or_(
                Collection.owner_id == auth.user.id,
                CollectionMembership.user_id == auth.user.id,
            )
        )
        .distinct()
        .order_by(Collection.name)
    )
    return [CollectionRead.model_validate(c) for c in db.scalars(stmt)]


@router.post("", response_model=CollectionRead, status_code=status.HTTP_201_CREATED)
def create_collection(
    payload: CollectionCreate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> CollectionRead:
    collection = Collection(owner_id=auth.user.id, **payload.model_dump())
    db.add(collection)
    db.commit()
    db.refresh(collection)
    return CollectionRead.model_validate(collection)


@router.get("/{collection_id}", response_model=CollectionRead)
def get_collection(
    collection_id: str,
    db: DBSession = Depends(get_session),
    _: AuthContext = Depends(require_collection_role("viewer")),
) -> CollectionRead:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return CollectionRead.model_validate(collection)


@router.patch("/{collection_id}", response_model=CollectionRead)
def update_collection(
    collection_id: str,
    payload: CollectionUpdate,
    db: DBSession = Depends(get_session),
    _: AuthContext = Depends(require_collection_role("owner")),
) -> CollectionRead:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(collection, key, value)
    db.commit()
    db.refresh(collection)
    return CollectionRead.model_validate(collection)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_collection(
    collection_id: str,
    db: DBSession = Depends(get_session),
    _: AuthContext = Depends(require_collection_role("owner")),
) -> None:
    collection = db.get(Collection, collection_id)
    if collection is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(collection)
    db.commit()
