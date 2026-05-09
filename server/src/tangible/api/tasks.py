"""Standalone task endpoints (one-off to-dos scoped to a collection)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from tangible.auth.deps import AuthContext, collection_role, require_user
from tangible.db import get_session
from tangible.models import Collection, StandaloneTask
from tangible.schemas import StandaloneTaskCreate, StandaloneTaskRead, StandaloneTaskUpdate

router = APIRouter(tags=["tasks"])

_EDITOR_ROLES = {"editor", "owner"}
_VIEWER_ROLES = {"viewer", "editor", "owner"}


def _require_role(
    db: DBSession, auth: AuthContext, collection_id: str, allowed: set[str]
) -> None:
    role = collection_role(db, auth.user, collection_id)
    if role is None or role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


@router.get("/tasks", response_model=list[StandaloneTaskRead])
def list_tasks(
    completed: bool = Query(default=False),
    collection_id: str | None = Query(default=None),
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[StandaloneTaskRead]:
    """List standalone tasks visible to the requesting user."""
    stmt = select(StandaloneTask)
    if completed:
        stmt = stmt.where(StandaloneTask.completed_at.isnot(None))
    else:
        stmt = stmt.where(StandaloneTask.completed_at.is_(None))
    if collection_id is not None:
        _require_role(db, auth, collection_id, _VIEWER_ROLES)
        stmt = stmt.where(StandaloneTask.collection_id == collection_id)
    stmt = stmt.order_by(StandaloneTask.due_at.nullslast())

    out: list[StandaloneTaskRead] = []
    for task in db.scalars(stmt).all():
        if collection_role(db, auth.user, task.collection_id) not in _VIEWER_ROLES:
            continue
        out.append(StandaloneTaskRead.model_validate(task))
    return out


@router.post(
    "/collections/{collection_id}/tasks",
    response_model=StandaloneTaskRead,
    status_code=status.HTTP_201_CREATED,
)
def create_task(
    collection_id: str,
    payload: StandaloneTaskCreate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> StandaloneTaskRead:
    _require_role(db, auth, collection_id, _EDITOR_ROLES)
    if db.get(Collection, collection_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found")
    task = StandaloneTask(
        collection_id=collection_id,
        created_by_user_id=auth.user.id,
        **payload.model_dump(),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return StandaloneTaskRead.model_validate(task)


@router.get("/tasks/{task_id}", response_model=StandaloneTaskRead)
def get_task(
    task_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> StandaloneTaskRead:
    task = db.get(StandaloneTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, task.collection_id, _VIEWER_ROLES)
    return StandaloneTaskRead.model_validate(task)


@router.patch("/tasks/{task_id}", response_model=StandaloneTaskRead)
def update_task(
    task_id: str,
    payload: StandaloneTaskUpdate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> StandaloneTaskRead:
    task = db.get(StandaloneTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, task.collection_id, _EDITOR_ROLES)
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    return StandaloneTaskRead.model_validate(task)


@router.post("/tasks/{task_id}/complete", response_model=StandaloneTaskRead)
def complete_task(
    task_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> StandaloneTaskRead:
    task = db.get(StandaloneTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, task.collection_id, _EDITOR_ROLES)
    if task.completed_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task already completed"
        )
    task.completed_at = datetime.now(UTC)
    task.completed_by_user_id = auth.user.id
    db.commit()
    db.refresh(task)
    return StandaloneTaskRead.model_validate(task)


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> None:
    task = db.get(StandaloneTask, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    _require_role(db, auth, task.collection_id, _EDITOR_ROLES)
    db.delete(task)
    db.commit()
