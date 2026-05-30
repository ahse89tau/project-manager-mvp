# Project Plan (Execution Checklist)

This is the working plan for the Project Management MVP.

## Global Rules

- Keep implementation simple; do not add non-MVP features.
- Use scoped instructions from `backend/AGENTS.md`, `scripts/AGENTS.md`, and (once created) `frontend/AGENTS.md`.
- Standardize naming to `SQLite` (not `SQLLite`).
- Testing baseline:
  - Aim for about `80%` unit coverage when it is sensible.
  - Prioritize high-value tests over adding low-signal tests just to hit a numeric target.
  - Robust integration testing for API and frontend-backend flows.
- Approval gates:
  - Pause for user approval after Part 1 (this plan).
  - Pause for user sign-off in Part 5 before implementing schema-dependent APIs.

## Part 1: Plan and Documentation

### Checklist

- [x] Expand this plan into actionable checklists (this document).
- [x] Define test expectations and success criteria for every part.
- [x] Create `frontend/AGENTS.md` documenting the existing frontend codebase structure, commands, and conventions.
- [x] Update `backend/AGENTS.md` with backend conventions for FastAPI, `uv`, testing, and SQLite usage.
- [x] Update `scripts/AGENTS.md` with script naming and behavior conventions.
- [x] Request and obtain user approval before any implementation.

### Tests

- [x] Documentation quality review: all parts include checklist + tests + success criteria.
- [x] Manual verification that all expected AGENTS files exist and are coherent.

### Success Criteria

- [x] `docs/PLAN.md` is complete and unambiguous.
- [x] `frontend/AGENTS.md` exists and accurately describes current frontend.
- [x] User explicitly approves plan before Part 2 starts.

## Part 2: Scaffolding (Docker + FastAPI + Scripts)

### Checklist

- [x] Create backend app scaffold in `backend/` with FastAPI.
- [x] Configure Python dependency management with `uv`.
- [x] Add Docker setup to run backend and serve basic static content.
- [x] Add hello-world endpoint(s) and sample API route.
- [x] Add start/stop scripts:
  - [x] `scripts/start_mac.sh`
  - [x] `scripts/stop_mac.sh`
  - [x] `scripts/start_linux.sh`
  - [x] `scripts/stop_linux.sh`
  - [x] `scripts/start_windows.bat`
  - [x] `scripts/stop_windows.bat`
- [x] Ensure scripts work from project root with clear output.

### Tests

- [x] Backend unit tests for startup health route(s).
- [x] Integration test for API call from running container.
- [x] Script smoke tests on current platform; static validation for other platform scripts.

### Success Criteria

- [x] `docker` run brings up app locally.
- [x] `/` serves basic static hello-world page.
- [x] API route responds successfully.
- [x] Start/stop scripts are present and functional.

## Part 3: Serve Existing Frontend at `/`

### Checklist

- [x] Build frontend static assets from existing `frontend/`.
- [x] Configure FastAPI/static serving so Kanban demo is served at `/`.
- [x] Ensure routing and asset paths work under Docker.
- [x] Add/update tests for static serving and app load.

### Tests

- [x] Frontend unit tests for core board rendering behavior.
- [x] Backend integration test that `/` returns frontend app.
- [ ] End-to-end smoke test that Kanban UI loads in browser.

### Success Criteria

- [x] Existing demo Kanban is visible at `/` in containerized app.
- [x] No regression in basic board interactions.
- [x] Coverage trend remains healthy with valuable tests.

## Part 4: Dummy Sign-In / Sign-Out

### Checklist

- [x] Add login gate on initial visit to `/`.
- [x] Implement backend auth check with hardcoded credentials (`user` / `password`) for MVP.
- [x] Add logout behavior.
- [x] Keep auth approach simple and clearly isolated for later replacement.

### Tests

- [x] Backend unit tests for login success/failure behavior.
- [x] Frontend unit tests for login form, error state, and logout.
- [x] Integration test for end-to-end login -> board access -> logout.

### Success Criteria

- [x] Unauthenticated users cannot access board.
- [x] Valid credentials show board.
- [x] Logout returns user to login screen.

## Part 5: Database Modeling and Sign-Off

### Checklist

- [x] Propose SQLite schema supporting multi-user readiness and one board per user (MVP).
- [x] Store Kanban board payload as JSON with minimal metadata.
- [x] Define migration/bootstrap strategy for auto-creating DB if missing.
- [x] Document schema and tradeoffs in `docs/`.
- [x] Define AI structured output schema (exact JSON contract) in docs before implementation.
- [x] Request explicit user sign-off before Part 6.

### Tests

- [x] Schema validation tests (model serialization/deserialization).
- [x] Documentation review checklist for clarity and completeness.

### Success Criteria

- [x] Approved schema doc exists and is implementation-ready.
- [x] Structured output contract is documented and unambiguous.
- [x] User approval captured before coding Part 6.

## Part 6: Backend Kanban APIs

### Checklist

- [x] Implement DB initialization (create SQLite DB if absent).
- [x] Implement user-scoped board read API.
- [x] Implement board update API for card/column changes.
- [x] Add validation and error handling for malformed payloads.
- [x] Keep routes and models straightforward and minimal.

### Tests

- [x] Backend unit tests for service/repository logic.
- [x] API integration tests for read/update flows.
- [x] Negative tests for invalid payloads and auth failures.
- [x] Backend test coverage is tracked pragmatically; expand tests where they add value.

### Success Criteria

- [x] Board state persists across restarts.
- [x] Authenticated user can fetch and update board.
- [x] Backend unit test coverage is reasonable for implemented risk.

## Part 7: Frontend + Backend Integration

### Checklist

- [x] Replace frontend demo-only state with backend API calls.
- [x] Load persisted board after login.
- [x] Persist board edits and drag/drop moves through backend APIs.
- [x] Add loading and error states for network requests.

### Tests

- [x] Frontend unit tests for API client and state transitions.
- [x] Integration tests for edit/move/persist/reload workflows.
- [x] End-to-end test for full login + board persistence path.
- [x] Frontend test coverage is tracked pragmatically; expand tests where they add value.

### Success Criteria

- [x] Board changes persist and reload correctly.
- [x] User interactions remain responsive.
- [x] Frontend unit test coverage is reasonable for implemented risk.

## Part 8: OpenRouter Connectivity

### Checklist

- [x] Add backend OpenRouter client using `OPENROUTER_API_KEY` from project `.env`.
- [x] Use model `openai/gpt-oss-120b:free`.
- [x] Add minimal AI route/service for connectivity check.
- [x] Implement simple `"2+2"` health-style AI test path.

### Tests

- [x] Unit tests with mocked OpenRouter client.
- [x] Integration test for successful API invocation (real key when available).
- [x] Error-path tests for missing/invalid API key.

### Success Criteria

- [x] Backend can call OpenRouter successfully.
- [x] `"2+2"` sanity check returns an AI response.
- [x] Failures are handled with clear API errors.

## Part 9: AI with Board Context + Structured Output

### Checklist

- [x] Send board JSON + user message + conversation history to AI.
- [x] Enforce documented structured output schema from Part 5.
- [x] Parse AI response into:
  - [x] User-facing assistant message
  - [x] Optional board mutation payload
- [x] Validate mutation payload before applying DB updates.

### Tests

- [x] Unit tests for schema validation and parser behavior.
- [x] Integration tests for:
  - [x] Message-only responses
  - [x] Message + valid board update
  - [x] Invalid structured output fallback behavior
- [x] Regression tests for preserving board integrity.

### Success Criteria

- [x] AI responses are reliably parsed into documented schema.
- [x] Optional board updates are applied only when valid.
- [x] Invalid outputs do not corrupt persisted board data.

## Part 10: Frontend AI Sidebar UX

### Checklist

- [x] Add responsive sidebar chat UI aligned with project color scheme.
- [x] Support conversation history display and user input.
- [x] Wire sidebar to backend AI endpoint.
- [x] Apply AI-issued board updates and refresh board automatically.
- [x] Ensure mobile and desktop usability.

### Tests

- [x] Frontend unit tests for chat UI state and rendering.
- [x] Integration tests for chat request/response and board refresh.
- [x] End-to-end scenario: user asks AI to modify board, UI updates automatically.

### Success Criteria

- [x] AI chat sidebar is functional and responsive.
- [x] Board refreshes automatically after valid AI mutations.
- [x] No regressions in login, board interactions, or persistence.

## Final Project Exit Criteria

- [ ] All 10 parts completed with checklist items checked.
- [ ] Backend and frontend test coverage are reviewed pragmatically with value-focused tests.
- [ ] Integration test suites pass.
- [ ] Local Dockerized app runs with start/stop scripts.
- [ ] User confirms MVP acceptance.
