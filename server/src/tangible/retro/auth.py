"""Shared authentication logic for retro interfaces.

Validates username + password directly against the User table using the same
argon2 hash as the main app. Returns the User on success, None on failure.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from tangible.models.user import User
from tangible.security import verify_password


def authenticate(db: Session, username: str, password: str) -> User | None:
    """Return User if credentials are valid, None otherwise."""
    user = db.scalar(
        select(User).where(User.username == username)
    )
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
