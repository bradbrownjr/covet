"""Startup helpers (data dirs, migrations, admin bootstrap)."""

from __future__ import annotations

from pathlib import Path

import structlog
from alembic import command
from alembic.config import Config
from sqlalchemy import select

from covet.auth.service import create_user
from covet.config import Settings
from covet.db import get_engine, init_engine

log = structlog.get_logger(__name__)


def ensure_data_dirs(settings: Settings) -> None:
    for path in (settings.data_dir, settings.config_dir, settings.photos_dir):
        if path is not None:
            Path(path).mkdir(parents=True, exist_ok=True)


def _alembic_config(settings: Settings) -> Config:
    server_root = Path(__file__).resolve().parent.parent.parent
    cfg = Config(str(server_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(server_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.resolved_database_url())
    return cfg


def run_migrations(settings: Settings) -> None:
    """Run Alembic upgrade head."""
    log.info("running_migrations", url=settings.resolved_database_url().split("@")[-1])
    cfg = _alembic_config(settings)
    command.upgrade(cfg, "head")


def bootstrap_admin_if_needed(settings: Settings) -> None:
    """Create the initial admin from env if no users exist."""
    from sqlalchemy.orm import Session as DBSession

    from covet.models import User

    if not (settings.admin_username and settings.admin_password):
        return

    try:
        engine = get_engine()
    except RuntimeError:
        engine = init_engine(settings)

    with DBSession(engine) as db:
        existing = db.scalar(select(User).limit(1))
        if existing is not None:
            return
        log.info("bootstrapping_admin", username=settings.admin_username)
        create_user(
            db,
            username=settings.admin_username,
            password=settings.admin_password,
            email=settings.admin_email,
            is_admin=True,
        )
        db.commit()
