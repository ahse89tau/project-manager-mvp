import sqlite3

import pytest

from app import db
from app.schemas import BoardState


@pytest.fixture
def sqlite_path(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "pm-test.db"
    monkeypatch.setenv(db.DB_PATH_ENV, str(path))
    db.init_db()
    return path


def test_init_db_creates_required_tables(sqlite_path) -> None:
    db.init_db()

    with sqlite3.connect(sqlite_path) as conn:
        names = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

    assert "users" in names
    assert "boards" in names


def test_ensure_user_returns_stable_id(sqlite_path) -> None:
    with db.get_connection() as conn:
        first = db.ensure_user(conn, "user")
        second = db.ensure_user(conn, "user")

    assert first == second


def test_get_or_create_and_update_board(sqlite_path) -> None:
    with db.get_connection() as conn:
        user_id = db.ensure_user(conn, "user")
        board = db.get_or_create_board(conn, user_id)
        assert board.columns[0].id == "col-backlog"

        payload = board.model_dump(by_alias=True)
        payload["columns"][0]["title"] = "Ideas"
        updated_board = BoardState.model_validate(payload)
        db.update_board(conn, user_id, updated_board)

        fetched = db.get_or_create_board(conn, user_id)
        assert fetched.columns[0].title == "Ideas"
