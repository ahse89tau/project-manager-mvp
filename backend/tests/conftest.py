import os
from pathlib import Path

import pytest


def pytest_configure(config) -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, val = line.partition("=")
                os.environ.setdefault(key.strip(), val.strip())


@pytest.fixture
def tmp_db(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """Isolated SQLite DB for a single test. Sets PM_SQLITE_PATH and initialises tables."""
    from app import db as _db

    path = tmp_path / "test.db"
    monkeypatch.setenv(_db.DB_PATH_ENV, str(path))
    _db.init_db()
    return path
