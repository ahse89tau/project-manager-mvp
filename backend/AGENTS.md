# Backend Agent Instructions

This file defines backend conventions for the MVP.

## Scope

- Directory: `backend/`
- Stack: Python + FastAPI
- Package manager: `uv`
- Database: `SQLite` (local file, auto-create if missing)

## Primary Responsibilities

- Serve backend API routes for auth, board read/update, and AI integration.
- Serve static frontend build at `/` once frontend integration is added.
- Persist one board per authenticated user for MVP, with schema ready for multi-user support.

## Implementation Rules

- Keep modules small and explicit.
- Prefer clear service/repository separation only where it reduces duplication.
- Use typed request/response models for API payloads.
- Do not add non-MVP features (no RBAC, no complex session store, no extra abstractions).
- Hardcoded auth credentials for MVP phase: `user` / `password` (replaceable later).

## Data Rules

- Use `SQLite` as the single local persistence layer.
- Create DB/tables on startup if they do not exist.
- Store board state as JSON payload with minimal metadata.
- Validate payload shape before persisting updates.

## AI Rules

- Use OpenRouter with `OPENROUTER_API_KEY` from project root `.env`.
- Model: `openai/gpt-oss-120b:free`.
- Enforce a documented structured output schema before applying AI-suggested board changes.

## Testing Expectations

- Use backend unit tests for core logic and validation.
- Use integration tests for API routes and DB interactions.
- Include negative-path tests (invalid input, auth failure, malformed AI output).
- Aim for strong backend coverage where it adds confidence; avoid low-value tests added only for a numeric threshold.
