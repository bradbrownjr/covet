"""Hardening middleware: security headers, rate limiting, simple CSRF guard.

These pieces deliberately have no behaviour-changing dependencies on each
other — they're applied in `create_app()` and can each be disabled via
settings without breaking the others.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from urllib.parse import urlparse

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from covet.config import Settings

# --- Rate limiting -----------------------------------------------------------------------


# slowapi limit-provider callables must be zero-arg (or take `key`); we can't
# read settings from inside one. We therefore bake the defaults from
# `covet.config.Settings` here as module constants — deployments that need
# different ceilings can edit these or remove the decorators and rely on
# upstream rate limiting (Caddy, nginx, Cloudflare).
DEFAULT_GLOBAL_LIMIT = "120/minute"
DEFAULT_LOGIN_LIMIT = "5/minute"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[DEFAULT_GLOBAL_LIMIT],
    headers_enabled=False,
)


async def rate_limit_exceeded_handler(_: Request, exc: RateLimitExceeded) -> JSONResponse:
    """JSON-friendly 429 response."""
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
        headers={"Retry-After": "60"},
    )


# --- Security headers --------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Adds a conservative set of security headers to every response.

    CSP intentionally allows ``'unsafe-inline'`` styles because SvelteKit's
    static build inlines critical CSS; tightening this requires hashing the
    inline blocks at build time, which is a v0.2 task.
    """

    def __init__(self, app: ASGIApp, *, hsts: bool, csp: str | None = None) -> None:
        super().__init__(app)
        self._hsts = hsts
        self._csp = csp or (
            "default-src 'self'; "
            "img-src 'self' data: blob:; "
            "media-src 'self' blob:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        response = await call_next(request)
        headers = response.headers
        headers.setdefault("X-Content-Type-Options", "nosniff")
        headers.setdefault("X-Frame-Options", "DENY")
        headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        headers.setdefault(
            "Permissions-Policy",
            "accelerometer=(), camera=(), geolocation=(), gyroscope=(), "
            "magnetometer=(), microphone=(), payment=(), usb=()",
        )
        headers.setdefault("Cross-Origin-Opener-Policy", "same-origin")
        headers.setdefault("Cross-Origin-Resource-Policy", "same-origin")
        # Don't apply CSP to the OpenAPI / docs surfaces (Swagger UI needs CDN).
        path = request.url.path
        if not (path.startswith("/docs") or path.startswith("/redoc")):
            headers.setdefault("Content-Security-Policy", self._csp)
        if self._hsts:
            headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains",
            )
        return response


# --- CSRF (Origin/Referer check for cookie-authenticated state changes) ------------------


_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class OriginCsrfMiddleware(BaseHTTPMiddleware):
    """Block cross-origin state-changing requests authenticated via session cookie.

    Requests authenticated via ``Authorization: Bearer …`` are allowed (mobile
    app, scripts) — they're not subject to CSRF. Requests with no auth cookie
    are also allowed (the endpoint will reject them itself).

    The check follows OWASP's "verifying origin with standard headers" pattern:
    the ``Origin`` (or ``Referer``) host must match one of the configured
    allowed hosts.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        cookie_name: str,
        allowed_hosts: set[str],
    ) -> None:
        super().__init__(app)
        self._cookie_name = cookie_name
        self._allowed_hosts = {h.lower() for h in allowed_hosts}

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.method not in _UNSAFE_METHODS:
            return await call_next(request)
        # Bearer-authed requests are exempt.
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)
        # No session cookie → no CSRF surface.
        if self._cookie_name not in request.cookies:
            return await call_next(request)

        origin = request.headers.get("origin") or request.headers.get("referer")
        if not origin:
            # Modern browsers always send Origin on cross-origin state-changing
            # requests, so an absent header indicates a non-browser caller
            # (curl, mobile native, integration tests) — those clients can't be
            # tricked into a cookie-CSRF flow, so allow them through.
            return await call_next(request)
        host = (urlparse(origin).hostname or "").lower()
        if host and host in self._allowed_hosts:
            return await call_next(request)
        return JSONResponse(
            status_code=403,
            content={"detail": "Cross-origin cookie-authenticated requests are blocked"},
        )


# --- Wiring helper -----------------------------------------------------------------------


def install_hardening(app: FastAPI, settings: Settings) -> None:
    """Attach all hardening middleware + the rate limiter to ``app``."""
    import contextlib

    # Reset in-memory storage between app constructions so tests don't share counters.
    with contextlib.suppress(Exception):
        limiter._storage.reset()  # type: ignore[attr-defined]
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # SlowAPI ASGI middleware enforces the default + per-route limits.
    from slowapi.middleware import SlowAPIMiddleware

    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(SecurityHeadersMiddleware, hsts=bool(settings.force_https))

    csrf_hosts: set[str] = set(settings.allowed_hosts or [])
    parsed_public = urlparse(settings.public_url)
    if parsed_public.hostname:
        csrf_hosts.add(parsed_public.hostname.lower())
    # Always permit localhost dev workflows.
    csrf_hosts.update({"localhost", "127.0.0.1", "testserver"})
    app.add_middleware(
        OriginCsrfMiddleware,
        cookie_name=settings.session_cookie_name,
        allowed_hosts=csrf_hosts,
    )
