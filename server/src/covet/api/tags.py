"""Tag endpoints (per-user)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from covet.auth.deps import AuthContext, require_user
from covet.db import get_session
from covet.models import Tag
from covet.schemas import TagCreate, TagRead, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagRead])
def list_tags(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[TagRead]:
    stmt = select(Tag).where(Tag.owner_id == auth.user.id).order_by(Tag.name)
    return [TagRead.model_validate(t) for t in db.scalars(stmt)]


@router.post("", response_model=TagRead, status_code=status.HTTP_201_CREATED)
def create_tag(
    payload: TagCreate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> TagRead:
    tag = Tag(owner_id=auth.user.id, **payload.model_dump())
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return TagRead.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagRead)
def update_tag(
    tag_id: str,
    payload: TagUpdate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> TagRead:
    tag = db.get(Tag, tag_id)
    if tag is None or tag.owner_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    db.commit()
    db.refresh(tag)
    return TagRead.model_validate(tag)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(
    tag_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> None:
    tag = db.get(Tag, tag_id)
    if tag is None or tag.owner_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    db.delete(tag)
    db.commit()
