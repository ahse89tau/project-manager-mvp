# Code Review

Reviewed: 2026-06-01  
Scope: entire repository (backend, frontend, Docker, tests)

---

## Summary

The codebase is clean, well-structured, and clearly follows the MVP constraints. The implementation is consistent with the documented plan. There is one critical data-loss issue (SQLite not persisted outside the container), several medium-priority correctness and reliability concerns, and a set of lower-priority quality improvements.

---

## Critical

### C1 — SQLite data is lost on container removal

**File:** `docker-compose.yml`

There is no volume mount for the database. The SQLite file lives at `/app/backend/data/pm.db` inside the container. Any `docker compose down` or container rebuild wipes all board data silently.

**Fix:** Add a named volume in `docker-compose.yml`:

```yaml
services:
  pm-app:
    volumes:
      - pm-data:/app/backend/data

volumes:
  pm-data:
```

---

## Medium

### M1 — SQLite connections are never explicitly closed

**File:** `backend/app/db.py:103-108`

`get_connection()` returns a raw `sqlite3.Connection`. The callers use it as `with get_connection() as conn:`, but Python's SQLite connection context manager only manages transactions (commit/rollback on `__exit__`). It does **not** close the connection. Under sustained request load, connections accumulate until GC collects them.

**Fix:** Wrap `get_connection` as a context manager that closes on exit, or explicitly call `conn.close()` in a `finally` block in each route.

```python
from contextlib import contextmanager

@contextmanager
def get_connection():
    conn = sqlite3.connect(resolve_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()
```

### M2 — `init_db()` is called on every `get_connection()` call

**File:** `backend/app/db.py:104`

`get_connection()` calls `init_db()` on every call, which does filesystem work (mkdir + CREATE TABLE IF NOT EXISTS) on every request. `init_db()` already runs once at startup in `main.py:42`.

**Fix:** Remove the `init_db()` call from inside `get_connection()`. Startup init is sufficient.

### M3 — `require_authenticated_username` is a plain function, not a FastAPI Dependency

**File:** `backend/app/main.py:89-93`

Auth is enforced by manually calling `require_authenticated_username(request)` inside each route handler. If a new route is added without that call, it silently becomes unauthenticated. FastAPI's `Depends()` system makes auth mandatory at the signature level and is the idiomatic approach.

**Fix:**
```python
from fastapi import Depends

def get_authenticated_username(request: Request) -> str:
    if request.cookies.get(SESSION_COOKIE_NAME) != "1":
        raise HTTPException(status_code=401, detail="Authentication required")
    return DEMO_USERNAME

@app.get("/api/board")
def read_board(username: str = Depends(get_authenticated_username)) -> dict:
    ...
```

### M4 — Auth flash on initial page load

**File:** `frontend/src/components/AuthGate.tsx:22`

`authStatus` defaults to `"unauthenticated"`, so the login form renders immediately on first load, then disappears when the session check resolves. This produces a visible flash for users who are already logged in.

**Fix:** Add a `"loading"` state and render nothing (or a spinner) until the session check completes:

```ts
type AuthStatus = "loading" | "authenticated" | "unauthenticated";
const [authStatus, setAuthStatus] = useState<AuthStatus>("loading");
```

Then in the render: return `null` (or a loader) when `authStatus === "loading"`.

### M5 — `anyio` not declared as an explicit dev dependency

**File:** `backend/pyproject.toml`

Backend tests use `@pytest.mark.anyio` extensively. `anyio` (which includes the pytest plugin) is only present as a transitive dependency of `httpx` or `fastapi`. If either changes their dependency tree, the tests break without warning.

**Fix:** Add to `[dependency-groups] dev`:
```toml
"anyio[trio]>=4.0",
```

### M6 — Playwright e2e tests mock the backend entirely

**File:** `frontend/tests/kanban.spec.ts:72-134`

All API calls are intercepted via `page.route("**/api/**", ...)`. The e2e suite therefore never exercises the real backend and cannot catch frontend-backend contract drift (field renames, payload shape changes, etc.).

The existing suite is valuable for UI flow testing, but a separate integration-level e2e test against the real running stack is missing. At minimum, a note in the test file or CI documentation should make this gap explicit.

---

## Low

### L1 — `update_board` has a dead-code INSERT fallback

**File:** `backend/app/db.py:146-162`

`update_board` does UPDATE and, if 0 rows affected, falls back to INSERT. But `get_or_create_board` is always called before `update_board` in every route, guaranteeing the row exists. The INSERT branch is never reached under normal flow.

**Fix:** Remove the fallback INSERT and add an assertion or raise instead:
```python
if cursor.rowcount == 0:
    raise RuntimeError(f"Board not found for user_id={user_id}")
```
This surfaces bugs rather than silently masking them.

### L2 — Login form pre-fills credentials

**File:** `frontend/src/components/AuthGate.tsx:23-24`

The login form initialises with `username: "user"` and `password: "password"`. This is convenient for demo use but can confuse anyone who thinks these are persisted credentials.

**Fix:** Initialise both fields to `""`. The credentials are already documented in the UI via `"Use the MVP credentials to continue."`.

### L3 — Message list uses array index as `key`

**File:** `frontend/src/components/AISidebar.tsx:112`

```tsx
{messages.map((msg, i) => (
  <div key={i} ...>
```

Using array index as `key` is safe here because messages are append-only, but it is an antipattern and will cause rendering bugs if message deletion or reordering is ever added.

**Fix:** Assign stable ids to messages at creation time:
```ts
type AIChatMessage = { id: string; role: string; content: string };
// use createId() or crypto.randomUUID() when pushing
```

### L4 — Card details are immutable after creation

**File:** `frontend/src/components/KanbanCard.tsx`

Cards support only delete, not edit. The `title` and `details` fields set at creation time cannot be changed without deleting and re-creating the card. This is likely an intentional MVP scope decision, but it is not documented in `AGENTS.md` or `PLAN.md`.

**Action:** If this is intentional, add a note in `frontend/AGENTS.md`. If not, add a follow-up task.

### L5 — E2E test file duplicates board type definitions

**File:** `frontend/tests/kanban.spec.ts:3-19`

`BoardCard`, `BoardColumn`, and `BoardData` are defined locally in the spec file, identical to the types exported from `src/lib/kanban.ts`.

**Fix:** Import directly:
```ts
import type { BoardData } from "../src/lib/kanban";
```

### L6 — `uv.lock` not committed

**File:** root (missing)

The `.gitignore` has `#uv.lock` commented out (i.e., the lockfile is not ignored, but it is also not committed). Without a committed lockfile, `uv sync` in the Docker build resolves the latest-compatible versions at build time, making builds non-reproducible.

**Fix:** Run `uv lock` in `backend/` and commit `uv.lock`. The Dockerfile's `uv sync --no-dev` will then use pinned versions.

### L7 — `scripts/AGENTS.md` not referenced in `CLAUDE.md`

**File:** `CLAUDE.md`

The scripts directory has its own `AGENTS.md` but it is not referenced in the top-level `CLAUDE.md`. Minor discoverability gap.

---

## Positive Observations

- **Pydantic validation with referential integrity** (`BoardState.validate_card_references`) is a strong design choice. It prevents the AI or any client from producing a board where columns reference non-existent cards, and the validation runs at both the HTTP boundary and before DB writes.
- **Structured AI output contract** is clean and well-enforced. The paired `applyBoardUpdate`/`updatedBoard` validation in `AIKanbanResponse` makes partial/corrupt AI responses fail loudly.
- **`pendingSaveCount` ref pattern** in `KanbanBoard.tsx` correctly tracks concurrent in-flight saves without unnecessary re-renders.
- **`persistBoard` is idempotent**: `handleRetrySave` re-sends `latestBoardRef.current`, which is always the last confirmed local state. The retry pattern is sound.
- **Multi-stage Docker build** is clean: frontend assets are built in a node image and the resulting `out/` directory is copied into the lean Python image. No node runtime in production.
- **Test isolation**: backend tests use `PM_SQLITE_PATH` via `monkeypatch.setenv` and `tmp_path` to avoid touching the real DB. The `conftest.py` loads `.env` without overwriting already-set env vars (`os.environ.setdefault`), so CI and local both work correctly.
- **90%+ backend coverage** with meaningful tests. Negative-path tests for AI schema failures, missing API keys, and auth failures are all present.
