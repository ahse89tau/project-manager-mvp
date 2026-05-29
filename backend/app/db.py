import json
import os
import sqlite3
from pathlib import Path

from app.schemas import BoardState

DB_PATH_ENV = "PM_SQLITE_PATH"
BASE_DIR = Path(__file__).resolve().parent.parent

DEFAULT_BOARD_DATA = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


def resolve_db_path() -> Path:
    raw_path = os.getenv(DB_PATH_ENV)
    if raw_path:
        return Path(raw_path)
    return BASE_DIR / "data" / "pm.db"


def init_db() -> None:
    db_path = resolve_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS boards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL UNIQUE,
              board_json TEXT NOT NULL CHECK (json_valid(board_json)),
              updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id)"
        )
        conn.commit()


def get_connection() -> sqlite3.Connection:
    init_db()
    conn = sqlite3.connect(resolve_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def ensure_user(conn: sqlite3.Connection, username: str) -> int:
    conn.execute(
        "INSERT OR IGNORE INTO users (username) VALUES (?)",
        (username,),
    )
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if row is None:
        raise RuntimeError("Failed to resolve user id")
    return int(row["id"])


def get_or_create_board(conn: sqlite3.Connection, user_id: int) -> BoardState:
    row = conn.execute(
        "SELECT board_json FROM boards WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        default_board = BoardState.model_validate(DEFAULT_BOARD_DATA)
        conn.execute(
            "INSERT INTO boards (user_id, board_json) VALUES (?, ?)",
            (
                user_id,
                json.dumps(default_board.model_dump(by_alias=True)),
            ),
        )
        conn.commit()
        return default_board

    board_payload = json.loads(row["board_json"])
    return BoardState.model_validate(board_payload)


def update_board(conn: sqlite3.Connection, user_id: int, board: BoardState) -> BoardState:
    board_json = json.dumps(board.model_dump(by_alias=True))
    cursor = conn.execute(
        """
        UPDATE boards
        SET board_json = ?, updated_at = CURRENT_TIMESTAMP
        WHERE user_id = ?
        """,
        (board_json, user_id),
    )
    if cursor.rowcount == 0:
        conn.execute(
            "INSERT INTO boards (user_id, board_json) VALUES (?, ?)",
            (user_id, board_json),
        )
    conn.commit()
    return board
