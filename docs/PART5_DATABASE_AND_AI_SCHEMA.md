# Part 5: Database and AI Schema Proposal

This document defines the proposed SQLite data model for the MVP and the exact AI structured output contract to be used in Part 9.

## Goals

- Keep MVP persistence simple.
- Support one board per signed-in user now.
- Keep schema ready for multiple users later.
- Store the full Kanban board as JSON.
- Define a strict AI response format that is easy to validate.

## SQLite Approach

### Database File

- Path (proposed for Part 6): `backend/data/pm.db`
- If the DB file or tables do not exist, create them on backend startup.

### Table: `users`

```sql
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

Notes:
- MVP auth is still hardcoded to `user/password`.
- This table exists now for forward compatibility and user-board ownership.

### Table: `boards`

```sql
CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  board_json TEXT NOT NULL CHECK (json_valid(board_json)),
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

Notes:
- `user_id UNIQUE` enforces exactly one board per user.
- `board_json` stores the full board payload.
- `json_valid(board_json)` enforces valid JSON at write time.

### Optional Indexes

```sql
CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
```

The `UNIQUE` constraint already implies uniqueness. The explicit index can still help readability and migration clarity.

## Board JSON Contract

Board JSON stored in `boards.board_json` uses this shape:

```json
{
  "columns": [
    {
      "id": "col-backlog",
      "title": "Backlog",
      "cardIds": ["card-1", "card-2"]
    }
  ],
  "cards": {
    "card-1": {
      "id": "card-1",
      "title": "Align roadmap themes",
      "details": "Draft quarterly themes with impact statements and metrics."
    }
  }
}
```

Validation rules:
- `columns` is an ordered list.
- `cards` is a dictionary keyed by card id.
- Every `cardIds[]` reference must exist in `cards`.
- Extra unknown fields are rejected at backend validation boundaries.

## AI Structured Output Contract (Exact)

The AI must return exactly this top-level object:

```json
{
  "assistantMessage": "string",
  "applyBoardUpdate": false,
  "updatedBoard": null
}
```

Field rules:
- `assistantMessage`:
  - Required string.
  - User-facing response text.
- `applyBoardUpdate`:
  - Required boolean.
  - `true` means AI intends to modify board state.
- `updatedBoard`:
  - Must be `null` when `applyBoardUpdate` is `false`.
  - Must be a full valid board object when `applyBoardUpdate` is `true`.

Example without board change:

```json
{
  "assistantMessage": "You have 3 cards in progress and 1 in review.",
  "applyBoardUpdate": false,
  "updatedBoard": null
}
```

Example with board change:

```json
{
  "assistantMessage": "Moved 'Prototype analytics view' to Review.",
  "applyBoardUpdate": true,
  "updatedBoard": {
    "columns": [
      { "id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"] },
      { "id": "col-review", "title": "Review", "cardIds": ["card-3"] }
    ],
    "cards": {
      "card-1": { "id": "card-1", "title": "Align roadmap themes", "details": "..." },
      "card-3": { "id": "card-3", "title": "Prototype analytics view", "details": "..." }
    }
  }
}
```

## Validation Implementation Notes

For Part 6+:
- Parse incoming board payloads with strict Pydantic models.
- Parse AI structured output with strict Pydantic models.
- Reject malformed board updates and do not persist partial updates.

Current model definitions are prepared in:
- `backend/app/schemas.py`

## Bootstrap Strategy (Part 6)

On app startup:
1. Ensure data directory exists (`backend/data/`).
2. Connect to SQLite.
3. Enable foreign keys (`PRAGMA foreign_keys = ON`).
4. Execute `CREATE TABLE IF NOT EXISTS` for `users` and `boards`.
5. Optionally seed user row for `username='user'` later when auth moves from hardcoded-only to DB-backed.

## Tradeoffs and Rationale

- Full-board JSON replace is simpler than patch operations for MVP.
- One-board-per-user constraint is explicit and easy to reason about.
- Strict structured output decreases AI parsing ambiguity.
- This design is intentionally minimal and can evolve to normalized tables later if needed.
