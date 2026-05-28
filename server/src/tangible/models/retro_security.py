"""SQLAlchemy models for retro interface brute-force / ban tracking."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from tangible.db import Base
from tangible.models.base import TimestampMixin, ULIDPrimaryKey, ulid_str, utcnow


class RetroLoginAttempt(Base):
    """One record per login attempt on a retro interface."""

    __tablename__ = "retro_login_attempts"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=ulid_str)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    interface: Mapped[str] = mapped_column(String(16), nullable=False)  # "http" | "telnet"
    attempted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)


class RetroBannedIP(Base):
    """An IP address that has been banned from a retro interface."""

    __tablename__ = "retro_banned_ips"

    id: Mapped[str] = mapped_column(String(26), primary_key=True, default=ulid_str)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False, index=True)
    interface: Mapped[str] = mapped_column(String(16), nullable=False)  # "http" | "telnet"
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    banned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    # None = permanent ban (requires admin to unban)
    ban_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    admin_note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    unbanned_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
    unbanned_by_user_id: Mapped[str | None] = mapped_column(
        String(26),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    unbanned_by = relationship("User", foreign_keys=[unbanned_by_user_id], lazy="select")
