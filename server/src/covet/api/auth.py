"""Authentication endpoints (local password + sessions + API tokens + OIDC)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session as DBSession

from covet.auth import oidc as oidc_service
from covet.auth import service as auth_service
from covet.auth.deps import AuthContext, require_admin, require_user
from covet.config import Settings, get_settings
from covet.db import get_session
from covet.hardening import DEFAULT_LOGIN_LIMIT, limiter
from covet.models import APIToken, User
from covet.schemas import (
    LoginRequest,
    MeUpdate,
    RegisterRequest,
    SessionInfo,
    TokenInfo,
    UserCreate,
    UserRead,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookie(response: Response, raw: str, settings: Settings) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        raw,
        max_age=settings.session_ttl_hours * 3600,
        httponly=True,
        secure=bool(settings.session_cookie_secure),
        samesite=settings.session_cookie_samesite,
        path="/",
    )


@router.post("/login", response_model=SessionInfo)
@limiter.limit(DEFAULT_LOGIN_LIMIT)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DBSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SessionInfo:
    user = auth_service.authenticate(db, username=payload.username, password=payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )
    session, raw = auth_service.create_session(
        db,
        user=user,
        settings=settings,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()
    _set_session_cookie(response, raw, settings)
    return SessionInfo(user=UserRead.model_validate(user), expires_at=session.expires_at)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    response: Response,
    db: DBSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    cookie = request.cookies.get(settings.session_cookie_name)
    if cookie:
        auth_service.revoke_session(db, raw_token=cookie)
        db.commit()
    response.delete_cookie(settings.session_cookie_name, path="/")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
@limiter.limit(DEFAULT_LOGIN_LIMIT)
def register(
    payload: RegisterRequest,
    request: Request,
    db: DBSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> UserRead:
    # First-run: if there are no users yet, allow registration regardless of
    # COVET_REGISTRATION_ENABLED and promote the first user to admin so a
    # fresh deployment can be bootstrapped without any environment vars.
    is_first_user = db.scalar(select(User.id).limit(1)) is None
    if not is_first_user and not settings.registration_enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Registration is disabled"
        )
    user = auth_service.create_user(
        db,
        username=payload.username,
        password=payload.password,
        email=payload.email,
        display_name=payload.display_name,
        is_admin=is_first_user,
    )
    db.commit()
    return UserRead.model_validate(user)


@router.get("/me", response_model=UserRead)
def me(auth: AuthContext = Depends(require_user)) -> UserRead:
    return UserRead.model_validate(auth.user)


@router.patch("/me", response_model=UserRead)
def update_me(
    payload: MeUpdate,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> UserRead:
    """Update the signed-in user's own profile (display name, email, password).

    Cannot change ``is_admin`` / ``is_active`` from this endpoint — that would
    let any user self-promote. Use the admin user endpoints for that.
    """
    user = auth.user
    if payload.display_name is not None:
        user.display_name = payload.display_name or None
    if payload.email is not None:
        user.email = payload.email or None
    if payload.password:
        from covet.security import hash_password

        user.password_hash = hash_password(payload.password)
    db.flush()
    db.commit()
    return UserRead.model_validate(user)


# --- Admin user management ---------------------------------------------------------------


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: UserCreate,
    db: DBSession = Depends(get_session),
    _: AuthContext = Depends(require_admin),
) -> UserRead:
    user = auth_service.create_user(
        db,
        username=payload.username,
        password=payload.password,
        email=payload.email,
        display_name=payload.display_name,
        is_admin=payload.is_admin,
    )
    db.commit()
    return UserRead.model_validate(user)


# --- API tokens ---------------------------------------------------------------------------


@router.post("/tokens", response_model=TokenInfo, status_code=status.HTTP_201_CREATED)
def create_token(
    name: str,
    db: DBSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
    auth: AuthContext = Depends(require_user),
) -> TokenInfo:
    token, raw = auth_service.create_api_token(
        db, user=auth.user, name=name, ttl_days=settings.api_token_ttl_days
    )
    db.commit()
    return TokenInfo(
        id=token.id,
        name=token.name,
        token=raw,
        last_used_at=token.last_used_at,
        expires_at=token.expires_at,
        created_at=token.created_at,
    )


@router.get("/tokens", response_model=list[TokenInfo])
def list_tokens(
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> list[TokenInfo]:
    rows = db.scalars(
        select(APIToken).where(APIToken.user_id == auth.user.id).order_by(APIToken.created_at)
    ).all()
    return [
        TokenInfo(
            id=t.id,
            name=t.name,
            token=None,
            last_used_at=t.last_used_at,
            expires_at=t.expires_at,
            created_at=t.created_at,
        )
        for t in rows
        if not t.revoked
    ]


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_token(
    token_id: str,
    db: DBSession = Depends(get_session),
    auth: AuthContext = Depends(require_user),
) -> Response:
    token = db.get(APIToken, token_id)
    if token is None or token.user_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Token not found")
    token.revoked = True
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- OIDC ---------------------------------------------------------------------------------


def _redirect_uri(request: Request, settings: Settings, provider_name: str) -> str:
    """Build the absolute callback URL for the given provider."""
    provider = oidc_service.get_provider(settings, provider_name)
    if provider and provider.redirect_uri:
        return provider.redirect_uri
    base = settings.public_url.rstrip("/")
    return f"{base}/auth/oidc/{provider_name}/callback"


@router.get("/oidc/{provider_name}/login", include_in_schema=False)
async def oidc_login(
    provider_name: str,
    request: Request,
    next: str = "/",
    settings: Settings = Depends(get_settings),
) -> Response:
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC disabled")
    client = oidc_service.client_for(settings, provider_name)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown OIDC provider")
    request.session["oidc_next"] = next or "/"
    return await client.authorize_redirect(
        request, _redirect_uri(request, settings, provider_name)
    )


@router.get("/oidc/{provider_name}/callback", include_in_schema=False)
async def oidc_callback(
    provider_name: str,
    request: Request,
    db: DBSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> Response:
    if not settings.oidc_enabled:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="OIDC disabled")
    provider = oidc_service.get_provider(settings, provider_name)
    client = oidc_service.client_for(settings, provider_name)
    if provider is None or client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown OIDC provider")

    try:
        token = await client.authorize_access_token(request)
    except Exception as exc:  # authlib raises a few different errors here
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC exchange failed: {exc.__class__.__name__}",
        ) from exc

    claims = token.get("userinfo") or {}
    if not claims:
        # Some providers don't return userinfo with the token; ask explicitly.
        try:
            resp = await client.userinfo(token=token)
            claims = dict(resp)
        except Exception:
            claims = {}

    user = oidc_service.upsert_user_from_claims(
        db, settings=settings, provider=provider, claims=claims
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="OIDC login rejected (user creation disabled or missing subject)",
        )

    _session, raw = auth_service.create_session(
        db,
        user=user,
        settings=settings,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    db.commit()

    next_url = request.session.pop("oidc_next", "/") or "/"
    if not next_url.startswith("/"):
        next_url = "/"
    response = RedirectResponse(url=next_url, status_code=status.HTTP_303_SEE_OTHER)
    _set_session_cookie(response, raw, settings)
    return response

