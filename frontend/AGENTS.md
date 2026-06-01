# Frontend Agent Instructions

This file describes the current frontend and how to work on it safely.

## Scope

- Directory: `frontend/`
- Stack: Next.js (App Router), React, TypeScript, Tailwind CSS
- Current role: MVP Kanban demo UI (frontend-only today)

## Current Structure

- `src/app/`
  - `layout.tsx`: root layout
  - `page.tsx`: renders `KanbanBoard`
  - `globals.css`: global theme styles and design tokens
- `src/components/`
  - `KanbanBoard.tsx`: top-level board state and drag/drop orchestration
  - `KanbanColumn.tsx`: per-column rendering and controls
  - `KanbanCard.tsx`, `KanbanCardPreview.tsx`, `NewCardForm.tsx`
- `src/lib/kanban.ts`
  - Core board types (`Card`, `Column`, `BoardData`)
  - Seed data (`initialData`)
  - Pure board helpers (`moveCard`, `createId`)
- Tests:
  - Unit/component tests in `src/**/*.{test,spec}.{ts,tsx}` (Vitest + Testing Library)
  - E2E tests in `tests/` (Playwright)

## Commands

Run commands from `frontend/`.

- `npm install`
- `npm run dev`
- `npm run build`
- `npm run start`
- `npm run lint`
- `npm run test:unit`
- `npm run test:e2e`
- `npm run test:all`

## Working Rules

- Keep UI behavior simple and deterministic.
- Prefer pure utility functions in `src/lib/` for business logic.
- Keep component state local unless there is a clear need to lift it.
- Preserve existing design direction and color tokens from project-level requirements.
- Avoid adding heavy state/data libraries unless explicitly requested.

## Testing Expectations

- Add or update unit tests for each behavior change.
- Keep tests close to behavior under change:
  - UI/component behavior: `src/components/*.test.tsx`
  - Logic behavior: `src/lib/*.test.ts`
- Maintain frontend unit coverage toward project minimum `>=80%`.
- Add/update Playwright tests for critical user flows when behavior changes across screens.

## Intentional Scope Limits

- Cards have no edit UI after creation. Title and details are set once via `NewCardForm` and cannot be changed. Only deletion is supported. This is an intentional MVP constraint.

## Integration Direction (Upcoming Parts)

- Frontend will move from local in-memory state to backend APIs.
- Keep data-fetching boundaries clear so local state can be replaced cleanly.
- Auth UI will gate board access in later parts using backend-authenticated state.
