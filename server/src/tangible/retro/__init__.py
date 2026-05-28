"""Retro interfaces: HTML 1.0 HTTP, Telnet, and Gopher servers.

All three run as asyncio TCP servers started in the FastAPI lifespan alongside
the main uvicorn process. They share the same SQLAlchemy session factory and
the same argon2 password-verification logic as the main app.

Security note: HTTP Basic Auth and Telnet are plaintext protocols. These
interfaces are intended for LAN / vintage-hardware use only. Do not expose
ports 8080 or 8023 to the public internet.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tangible.config import Settings

log = logging.getLogger(__name__)


async def start_retro_servers(settings: "Settings") -> list[asyncio.Server]:
    """Start all enabled retro servers and return their handles."""
    from tangible.retro.http import create_http_server
    from tangible.retro.telnet import create_telnet_server
    from tangible.retro.gopher import create_gopher_server

    servers: list[asyncio.Server] = []

    if settings.retro_http_enabled:
        srv = await create_http_server(settings)
        servers.append(srv)
        log.info(
            "Retro HTTP server listening",
            extra={"bind": settings.retro_http_bind, "port": settings.retro_http_port},
        )

    if settings.telnet_enabled:
        srv = await create_telnet_server(settings)
        servers.append(srv)
        log.info(
            "Retro Telnet server listening",
            extra={"bind": settings.telnet_bind, "port": settings.telnet_port},
        )

    if settings.retro_gopher_enabled:
        srv = await create_gopher_server(settings)
        servers.append(srv)
        log.info(
            "Retro Gopher server listening",
            extra={"bind": settings.retro_gopher_bind, "port": settings.retro_gopher_port},
        )

    return servers
