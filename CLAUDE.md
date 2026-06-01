# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Kanban-based project management app with:
- Next.js (App Router) frontend exported as static files
- Python FastAPI backend that serves both the API and the static frontend
- SQLite for persistence, one board per user (hardcoded auth: `user` / `password`)
- AI sidebar via OpenRouter (`openai/gpt-oss-120b:free`) that can read and mutate the board
- Everything packaged into a single Docker container

## Commands

### Running locally (Docker)

```bash
./scripts/start_mac.sh    # builds image and starts container at http://localhost:8000
./scripts/stop_mac.sh
```

### Frontend (run from `frontend/`)

```bash
npm install
npm run dev           # dev server
npm run build         # static export to frontend/out/
npm run lint
npm run test:unit     # vitest
npm run test:e2e      # playwright
npm run test:all
```

### Backend (run from `backend/`)

```bash
uv sync               # install deps
uv run uvicorn app.main:app --reload --port 8000
uv run pytest                          # all tests with coverage
uv run pytest tests/unit/test_schemas.py   # single test file
uv run pytest -k "test_name"               # single test by name
```

Backend tests auto-load the root `.env` via `tests/conftest.py` — `OPENROUTER_API_KEY` is needed for integration tests.

## Architecture

### Request flow

```
Browser → FastAPI (:8000)
  /api/*        → FastAPI routes (auth, board CRUD, AI chat)
  /*            → StaticFiles serving frontend/out/ (Next.js static export)
```

### Backend modules (`backend/app/`)

| File | Responsibility |
|---|---|
| `main.py` | FastAPI app, all route definitions, cookie-based session auth |
| `db.py` | SQLite init, `ensure_user`, `get_or_create_board`, `update_board` |
| `schemas.py` | Pydantic models: `BoardState`, `BoardColumn`, `BoardCard`, `AIKanbanResponse` |
| `ai.py` | OpenRouter HTTP calls; `board_chat()` returns a validated `AIKanbanResponse` |

Auth is a cookie (`pm_session=1`). All `/api/board` and `/api/ai/*` routes call `require_authenticated_username()` which checks this cookie.

Board state is stored as a JSON blob in SQLite. The `BoardState` Pydantic model validates that every `cardId` referenced in a column's `cardIds` list exists in the `cards` dict — this invariant is enforced on write.

AI responses use `response_format: json_object` and are validated against `AIKanbanResponse` before any board mutation is applied.

DB path defaults to `backend/data/pm.db`; override with `PM_SQLITE_PATH` env var. Frontend static dir defaults to `frontend/out/`; override with `FRONTEND_STATIC_DIR`.

### Frontend modules (`frontend/src/`)

| Path | Responsibility |
|---|---|
| `lib/kanban.ts` | Core types (`Card`, `Column`, `BoardData`), pure `moveCard()` helper, `createId()` |
| `components/KanbanBoard.tsx` | Top-level board state, API calls, drag-and-drop orchestration via `@dnd-kit` |
| `components/KanbanColumn.tsx` | Per-column rendering and inline rename |
| `components/KanbanCard.tsx` | Card display and edit |
| `app/page.tsx` | Renders `KanbanBoard` |

The frontend fetches board state from `/api/board` on load and PUTs the full board on every mutation. The AI sidebar sends messages to `/api/ai/chat`; if `boardUpdated` is true in the response, the frontend re-fetches the board.

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`

## Coding Standards

- No over-engineering; no extra abstractions beyond what the task needs.
- No emojis anywhere.
- When hitting issues: identify root cause with evidence before fixing.
- Frontend unit test coverage target: >=80%.
- Backend: include negative-path tests (invalid input, auth failure, malformed AI output).
