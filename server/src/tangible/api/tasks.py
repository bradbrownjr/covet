"""Standalone task endpoints (one-off to-dos scoped to a collection)."""

from __future__ import annotations

from collections import defaultdict
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from tangible.auth.deps import AuthContext, collection_role, require_user
from tangible.db import get_session
from tangible.models import (
    Chore,
    ChoreCompletion,
    Collection,
    CollectionMembership,
    Item,
    MaintenanceCompletion,
    MaintenanceTask,
    StandaloneTask,
    User,
)
from tangible.schemas import ScoreboardEntry, StandaloneTaskCreate, StandaloneTaskRead, StandaloneTaskUpdate
from tangible.schemas.maintenance import _compute_achievements

router = APIRouter(tags=["tasks"])

_EDITOR_ROLES = {"editor", "owner"}
_VIEWER_ROLES = {"viewer", "editor", "owner"}


def _require_role(
    db: DBSession, auth: AuthContext, collection_id: str, allowed: set[str]
) -> None:
    role = collection_role(db, auth.user, collection_id)
    if role is None or role not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")


def _readable_collection_ids(db: DBSession, user: User) -> list[str] | None:
    """Return list of readable collection IDs, or None for admins (unrestricted)."""
    if user.is_admin:
        return None
    owned = list(db.scalars(select(Collection.id).where(Collection.owner_id == user.id)).all())
    member = list(
        db.scalars(
            select(CollectionMembership.collection_id).where(
                CollectionMembership.user_id == user.id
            )
        ).all()
    )
    return list(set(owned + member))


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


# NOTE: this route must be registered before /tasks/{task_id} to avoid ambiguity
@router.get("/tasks/scoreboard", response_model=list[ScoreboardEntry])
def get_scoreboard(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[ScoreboardEntry]:
    """Return per-member completion counts across chores, maintenance, and standalone tasks."""
    readable = _readable_collection_ids(db, auth.user)

    def _col_filter(col_id_column):  # type: ignore[no-untyped-def]
        if readable is None:
            return True
        if not readable:
            return False
        return col_id_column.in_(readable)

    # Chore completions
    chore_stmt = (
        select(ChoreCompletion.completed_by_user_id, func.count().label("n"))
        .join(Chore, ChoreCompletion.chore_id == Chore.id)
        .where(ChoreCompletion.completed_by_user_id.isnot(None))
        .where(_col_filter(Chore.collection_id))
        .group_by(ChoreCompletion.completed_by_user_id)
    )

    # Maintenance completions (join through item to get collection_id)
    maint_stmt = (
        select(MaintenanceCompletion.completed_by_user_id, func.count().label("n"))
        .join(MaintenanceTask, MaintenanceCompletion.task_id == MaintenanceTask.id)
        .join(Item, MaintenanceTask.item_id == Item.id)
        .where(MaintenanceCompletion.completed_by_user_id.isnot(None))
        .where(_col_filter(Item.collection_id))
        .group_by(MaintenanceCompletion.completed_by_user_id)
    )

    # Standalone task completions
    task_stmt = (
        select(StandaloneTask.completed_by_user_id, func.count().label("n"))
        .where(StandaloneTask.completed_at.isnot(None))
        .where(StandaloneTask.completed_by_user_id.isnot(None))
        .where(_col_filter(StandaloneTask.collection_id))
        .group_by(StandaloneTask.completed_by_user_id)
    )

    # Skip if no readable collections (non-admin with zero memberships)
    if readable is not None and not readable:
        return []

    chore_counts: dict[str, int] = dict(db.execute(chore_stmt).all())
    maint_counts: dict[str, int] = dict(db.execute(maint_stmt).all())
    task_counts: dict[str, int] = dict(db.execute(task_stmt).all())

    all_user_ids = set(chore_counts) | set(maint_counts) | set(task_counts)
    if not all_user_ids:
        return []

    users = {
        u.id: u
        for u in db.scalars(select(User).where(User.id.in_(all_user_ids))).all()
    }

    entries: list[ScoreboardEntry] = []
    for uid in all_user_ids:
        c = chore_counts.get(uid, 0)
        m = maint_counts.get(uid, 0)
        t = task_counts.get(uid, 0)
        total = c + m + t
        user = users.get(uid)
        entries.append(
            ScoreboardEntry(
                user_id=uid,
                display_name=(user.display_name or user.username) if user else uid,
                chore_count=c,
                maintenance_count=m,
                task_count=t,
                total=total,
                achievements=_compute_achievements(total),
            )
        )

    entries.sort(key=lambda e: e.total, reverse=True)
    return entries


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
