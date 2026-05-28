"""Admin endpoints for retro interface ban management."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.orm import Session as DBSession

from tangible.auth.deps import AuthContext, require_admin
from tangible.db import get_session
from tangible.models.retro_security import RetroBannedIP, RetroLoginAttempt

router = APIRouter(prefix="/admin/retro-bans", tags=["retro-bans"])


class BanEntry(BaseModel):
    id: str
    ip_address: str
    interface: str
    attempt_count: int
    banned_at: datetime
    ban_expires_at: datetime | None
    is_permanent: bool
    is_active: bool
    unbanned_at: datetime | None


class AttemptEntry(BaseModel):
    id: str
    ip_address: str
    interface: str
    attempted_at: datetime
    success: bool


def _ban_to_entry(ban: RetroBannedIP) -> BanEntry:
    now = datetime.now(UTC)
    unbanned = ban.unbanned_at is not None
    if unbanned:
        is_active = False
    elif ban.ban_expires_at is None:
        is_active = True
    else:
        expiry = ban.ban_expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=UTC)
        is_active = now < expiry
    return BanEntry(
        id=ban.id,
        ip_address=ban.ip_address,
        interface=ban.interface,
        attempt_count=ban.attempt_count,
        banned_at=ban.banned_at,
        ban_expires_at=ban.ban_expires_at,
        is_permanent=ban.ban_expires_at is None and not unbanned,
        is_active=is_active,
        unbanned_at=ban.unbanned_at,
    )


@router.get("", response_model=list[BanEntry])
def list_bans(
    db: DBSession = Depends(get_session),
    _auth: AuthContext = Depends(require_admin),
) -> list[BanEntry]:
    """List all ban records (active, expired, and cleared)."""
    bans = db.scalars(
        select(RetroBannedIP).order_by(RetroBannedIP.banned_at.desc())
    ).all()
    return [_ban_to_entry(b) for b in bans]


@router.delete("/{ip_address}", status_code=status.HTTP_204_NO_CONTENT)
def unban_ip(
    ip_address: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_admin),
) -> None:
    """Unban an IP address across all interfaces."""
    now = datetime.now(UTC)
    bans = db.scalars(
        select(RetroBannedIP).where(
            RetroBannedIP.ip_address == ip_address,
            RetroBannedIP.unbanned_at.is_(None),
        )
    ).all()
    if not bans:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active ban found for this IP")
    for ban in bans:
        ban.unbanned_at = now
        ban.unbanned_by_user_id = auth.user.id
    # Also clear login attempt history for this IP
    db.execute(
        delete(RetroLoginAttempt).where(RetroLoginAttempt.ip_address == ip_address)
    )
    db.commit()


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def unban_all_expired(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_admin),
) -> None:
    """Mark all expired bans as cleared."""
    now = datetime.now(UTC)
    expired = db.scalars(
        select(RetroBannedIP).where(
            RetroBannedIP.unbanned_at.is_(None),
            RetroBannedIP.ban_expires_at.is_not(None),
            RetroBannedIP.ban_expires_at < now,
        )
    ).all()
    for ban in expired:
        ban.unbanned_at = now
        ban.unbanned_by_user_id = auth.user.id
    db.commit()


@router.get("/{ip_address}/attempts", response_model=list[AttemptEntry])
def get_attempts(
    ip_address: str,
    db: DBSession = Depends(get_session),
    _auth: AuthContext = Depends(require_admin),
) -> list[AttemptEntry]:
    """Get login attempt history for an IP (most recent first)."""
    attempts = db.scalars(
        select(RetroLoginAttempt).where(
            RetroLoginAttempt.ip_address == ip_address
        ).order_by(RetroLoginAttempt.attempted_at.desc()).limit(100)
    ).all()
    return [
        AttemptEntry(
            id=a.id,
            ip_address=a.ip_address,
            interface=a.interface,
            attempted_at=a.attempted_at,
            success=a.success,
        )
        for a in attempts
    ]
