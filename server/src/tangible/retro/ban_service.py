"""Brute-force / rate-limiting service for retro interfaces.

Ramp-up cooldown schedule (failures within the tracking window):
  3  failures → 30-second block
  5  failures → 5-minute block
  7  failures → 1-hour block
  10 failures → 24-hour block
  15+ failures → permanent block (requires admin action to unban)

Returns:
  is_banned() → False (not banned), True (permanent), or datetime (expiry time)
  record_attempt() → None (not newly banned), True (permanent), or datetime (new expiry)
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from tangible.models.retro_security import RetroBannedIP, RetroLoginAttempt

# How far back to count failures when making a ban decision
_WINDOW = timedelta(hours=24)

# (min_failures, ban_duration | None-for-permanent)
_THRESHOLDS: list[tuple[int, timedelta | None]] = [
    (15, None),                       # permanent
    (10, timedelta(hours=24)),
    (7, timedelta(hours=1)),
    (5, timedelta(minutes=5)),
    (3, timedelta(seconds=30)),
]


def is_banned(db: Session, ip: str, interface: str) -> bool | datetime:
    """Return False if not banned, True if permanently banned, datetime if temporarily banned.

    The datetime is the expiry time (UTC). Expired bans are auto-cleared.
    """
    now = datetime.now(UTC)
    ban = db.scalar(
        select(RetroBannedIP).where(
            RetroBannedIP.ip_address == ip,
            RetroBannedIP.interface == interface,
            RetroBannedIP.unbanned_at.is_(None),
        ).order_by(RetroBannedIP.banned_at.desc())
    )
    if ban is None:
        return False

    # Permanent ban
    if ban.ban_expires_at is None:
        return True

    expiry = ban.ban_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)

    if now >= expiry:
        # Expired — auto-clear
        ban.unbanned_at = now
        db.commit()
        return False

    return expiry


def record_attempt(
    db: Session, ip: str, interface: str, success: bool
) -> None | bool | datetime:
    """Record a login attempt. On success, clears prior failed attempts.

    Returns:
        None  — no new ban triggered
        True  — newly permanently banned
        datetime — newly banned until this UTC time
    """
    now = datetime.now(UTC)

    attempt = RetroLoginAttempt(
        ip_address=ip,
        interface=interface,
        attempted_at=now,
        success=success,
    )
    db.add(attempt)

    if success:
        # Clear all prior failed attempts for this IP+interface
        db.execute(
            delete(RetroLoginAttempt).where(
                RetroLoginAttempt.ip_address == ip,
                RetroLoginAttempt.interface == interface,
                RetroLoginAttempt.success == False,  # noqa: E712
            )
        )
        db.commit()
        return None

    # Count failures in the tracking window
    window_start = now - _WINDOW
    from sqlalchemy import func
    failure_count = db.scalar(
        select(func.count()).where(
            RetroLoginAttempt.ip_address == ip,
            RetroLoginAttempt.interface == interface,
            RetroLoginAttempt.success == False,  # noqa: E712
            RetroLoginAttempt.attempted_at >= window_start,
        )
    ) or 0

    # Find the applicable threshold
    ban_duration: timedelta | None | bool = False  # False = no ban
    for min_fails, duration in _THRESHOLDS:
        if failure_count >= min_fails:
            ban_duration = duration  # None = permanent
            break

    if ban_duration is False:
        db.commit()
        return None

    # Remove any existing (possibly expired) ban record before inserting a new one
    db.execute(
        delete(RetroBannedIP).where(
            RetroBannedIP.ip_address == ip,
            RetroBannedIP.interface == interface,
        )
    )

    if ban_duration is None:
        # Permanent
        ban = RetroBannedIP(
            ip_address=ip,
            interface=interface,
            attempt_count=failure_count,
            banned_at=now,
            ban_expires_at=None,
        )
        db.add(ban)
        db.commit()
        return True
    else:
        expiry = now + ban_duration
        ban = RetroBannedIP(
            ip_address=ip,
            interface=interface,
            attempt_count=failure_count,
            banned_at=now,
            ban_expires_at=expiry,
        )
        db.add(ban)
        db.commit()
        return expiry
