"""Auth-related schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from covet.schemas.user import UserRead


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr | None = None
    password: str = Field(min_length=12, max_length=255)
    display_name: str | None = Field(default=None, max_length=128)


class MeUpdate(BaseModel):
    """Self-service profile updates. Cannot change is_admin/is_active."""

    display_name: str | None = Field(default=None, max_length=128)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=12, max_length=255)


class SessionInfo(BaseModel):
    user: UserRead
    expires_at: datetime


class TokenInfo(BaseModel):
    id: str
    name: str
    token: str | None = None  # only populated on creation
    last_used_at: datetime | None
    expires_at: datetime | None
    created_at: datetime


class OIDCProviderInfo(BaseModel):
    name: str
    display_name: str
    login_url: str
