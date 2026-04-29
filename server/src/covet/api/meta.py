"""Health, version, and discovery endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from covet import __version__
from covet.config import get_settings
from covet.db import get_engine

router = APIRouter(tags=["meta"])


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe — process is up and answering. Cheap, no I/O."""
    return {"status": "ok"}


@router.get("/readyz")
def readyz(response: Response) -> dict[str, str]:
    """Readiness probe — confirms the database is reachable."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except (RuntimeError, SQLAlchemyError) as exc:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "unavailable", "detail": str(exc.__class__.__name__)}
    return {"status": "ready"}


@router.get("/version")
def version() -> dict[str, str]:
    return {"version": __version__}


@router.get("/config/public")
def public_config() -> dict[str, object]:
    """Return non-sensitive runtime info for clients (web/mobile)."""
    settings = get_settings()
    providers = []
    if settings.oidc_enabled:
        providers = [
            {
                "name": p.name,
                "label": p.display_name,
                "login_url": f"/auth/oidc/{p.name}/login",
            }
            for p in settings.oidc_providers
        ]
    return {
        "version": __version__,
        "registration_enabled": settings.registration_enabled,
        "oidc_enabled": settings.oidc_enabled,
        "oidc_providers": providers,
        "public_url": settings.public_url,
    }
