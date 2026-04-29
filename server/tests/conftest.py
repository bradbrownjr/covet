"""Pytest fixtures for the Covet server."""

from __future__ import annotations

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session as DBSession

from covet.config import reset_settings_cache
from covet.db import get_engine


def _fast_tmp_root() -> Path:
    """Use tmpfs when available so SQLite migrations don't pay disk fsync cost."""
    base = "/dev/shm" if os.path.isdir("/dev/shm") and os.access("/dev/shm", os.W_OK) else None
    return Path(tempfile.mkdtemp(prefix="covet-test-", dir=base))


@pytest.fixture()
def settings(monkeypatch: pytest.MonkeyPatch):
    root = _fast_tmp_root()
    data_dir = root / "data"
    config_dir = root / "config"
    data_dir.mkdir()
    config_dir.mkdir()

    monkeypatch.setenv("COVET_DATA_DIR", str(data_dir))
    monkeypatch.setenv("COVET_CONFIG_DIR", str(config_dir))
    monkeypatch.setenv("COVET_DB_TYPE", "sqlite")
    monkeypatch.setenv("COVET_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("COVET_PUBLIC_URL", "http://testserver")
    monkeypatch.setenv("COVET_ALLOWED_HOSTS", "testserver")
    monkeypatch.setenv("COVET_DB_AUTO_MIGRATE", "false")  # tests run migrations explicitly
    # Ensure no leftover env from another test
    for key in list(os.environ):
        if key.startswith("COVET_OIDC_"):
            monkeypatch.delenv(key, raising=False)

    reset_settings_cache()
    from covet.config import get_settings

    yield get_settings()
    reset_settings_cache()
    shutil.rmtree(root, ignore_errors=True)


@pytest.fixture()
def app(settings):
    from covet.main import create_app

    app = create_app(settings)
    # Run migrations once for this test database.
    from covet.bootstrap import run_migrations

    run_migrations(settings)
    return app


@pytest.fixture()
def client(app) -> Iterator[TestClient]:
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def db(app) -> Iterator[DBSession]:
    engine = get_engine()
    with DBSession(engine) as session:
        yield session
