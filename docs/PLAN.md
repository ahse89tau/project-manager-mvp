# Project Plan (Execution Checklist)

This is the working plan for the Project Management MVP.

## Global Rules

- Keep implementation simple; do not add non-MVP features.
- Use scoped instructions from `backend/AGENTS.md`, `scripts/AGENTS.md`, and (once created) `frontend/AGENTS.md`.
- Standardize naming to `SQLite` (not `SQLLite`).
- Testing baseline:
  - Minimum `80%` unit test coverage for backend and frontend by the end of the project.
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
- [ ] Request and obtain user approval before any implementation.

### Tests

- [x] Documentation quality review: all parts include checklist + tests + success criteria.
- [x] Manual verification that all expected AGENTS files exist and are coherent.

### Success Criteria

- [x] `docs/PLAN.md` is complete and unambiguous.
- [x] `frontend/AGENTS.md` exists and accurately describes current frontend.
- [ ] User explicitly approves plan before Part 2 starts.

## Part 2: Scaffolding (Docker + FastAPI + Scripts)

### Checklist

- [ ] Create backend app scaffold in `backend/` with FastAPI.
- [ ] Configure Python dependency management with `uv`.
- [ ] Add Docker setup to run backend and serve basic static content.
- [ ] Add hello-world endpoint(s) and sample API route.
- [ ] Add start/stop scripts:
  - [ ] `scripts/start_mac.sh`
  - [ ] `scripts/stop_mac.sh`
  - [ ] `scripts/start_linux.sh`
  - [ ] `scripts/stop_linux.sh`
  - [ ] `scripts/start_windows.bat`
  - [ ] `scripts/stop_windows.bat`
- [ ] Ensure scripts work from project root with clear output.

### Tests

- [ ] Backend unit tests for startup health route(s).
- [ ] Integration test for API call from running container.
- [ ] Script smoke tests on current platform; static validation for other platform scripts.

### Success Criteria

- [ ] `docker` run brings up app locally.
- [ ] `/` serves basic static hello-world page.
- [ ] API route responds successfully.
- [ ] Start/stop scripts are present and functional.

## Part 3: Serve Existing Frontend at `/`

### Checklist

- [ ] Build frontend static assets from existing `frontend/`.
- [ ] Configure FastAPI/static serving so Kanban demo is served at `/`.
- [ ] Ensure routing and asset paths work under Docker.
- [ ] Add/update tests for static serving and app load.

### Tests

- [ ] Frontend unit tests for core board rendering behavior.
- [ ] Backend integration test that `/` returns frontend app.
- [ ] End-to-end smoke test that Kanban UI loads in browser.

### Success Criteria

- [ ] Existing demo Kanban is visible at `/` in containerized app.
- [ ] No regression in basic board interactions.
- [ ] Coverage trend supports reaching `>=80%` unit coverage target.

## Part 4: Dummy Sign-In / Sign-Out

### Checklist

- [ ] Add login gate on initial visit to `/`.
- [ ] Implement backend auth check with hardcoded credentials (`user` / `password`) for MVP.
- [ ] Add logout behavior.
- [ ] Keep auth approach simple and clearly isolated for later replacement.

### Tests

- [ ] Backend unit tests for login success/failure behavior.
- [ ] Frontend unit tests for login form, error state, and logout.
- [ ] Integration test for end-to-end login -> board access -> logout.

### Success Criteria

- [ ] Unauthenticated users cannot access board.
- [ ] Valid credentials show board.
- [ ] Logout returns user to login screen.

## Part 5: Database Modeling and Sign-Off

### Checklist

- [ ] Propose SQLite schema supporting multi-user readiness and one board per user (MVP).
- [ ] Store Kanban board payload as JSON with minimal metadata.
- [ ] Define migration/bootstrap strategy for auto-creating DB if missing.
- [ ] Document schema and tradeoffs in `docs/`.
- [ ] Define AI structured output schema (exact JSON contract) in docs before implementation.
- [ ] Request explicit user sign-off before Part 6.

### Tests

- [ ] Schema validation tests (model serialization/deserialization).
- [ ] Documentation review checklist for clarity and completeness.

### Success Criteria

- [ ] Approved schema doc exists and is implementation-ready.
- [ ] Structured output contract is documented and unambiguous.
- [ ] User approval captured before coding Part 6.

## Part 6: Backend Kanban APIs

### Checklist

- [ ] Implement DB initialization (create SQLite DB if absent).
- [ ] Implement user-scoped board read API.
- [ ] Implement board update API for card/column changes.
- [ ] Add validation and error handling for malformed payloads.
- [ ] Keep routes and models straightforward and minimal.

### Tests

- [ ] Backend unit tests for service/repository logic.
- [ ] API integration tests for read/update flows.
- [ ] Negative tests for invalid payloads and auth failures.
- [ ] Unit coverage in backend at or above `80%`.

### Success Criteria

- [ ] Board state persists across restarts.
- [ ] Authenticated user can fetch and update board.
- [ ] Backend unit coverage is `>=80%`.

## Part 7: Frontend + Backend Integration

### Checklist

- [ ] Replace frontend demo-only state with backend API calls.
- [ ] Load persisted board after login.
- [ ] Persist board edits and drag/drop moves through backend APIs.
- [ ] Add loading and error states for network requests.

### Tests

- [ ] Frontend unit tests for API client and state transitions.
- [ ] Integration tests for edit/move/persist/reload workflows.
- [ ] End-to-end test for full login + board persistence path.
- [ ] Frontend unit coverage at or above `80%`.

### Success Criteria

- [ ] Board changes persist and reload correctly.
- [ ] User interactions remain responsive.
- [ ] Frontend unit coverage is `>=80%`.

## Part 8: OpenRouter Connectivity

### Checklist

- [ ] Add backend OpenRouter client using `OPENROUTER_API_KEY` from project `.env`.
- [ ] Use model `openai/gpt-oss-120b:free`.
- [ ] Add minimal AI route/service for connectivity check.
- [ ] Implement simple `"2+2"` health-style AI test path.

### Tests

- [ ] Unit tests with mocked OpenRouter client.
- [ ] Integration test for successful API invocation (real key when available).
- [ ] Error-path tests for missing/invalid API key.

### Success Criteria

- [ ] Backend can call OpenRouter successfully.
- [ ] `"2+2"` sanity check returns an AI response.
- [ ] Failures are handled with clear API errors.

## Part 9: AI with Board Context + Structured Output

### Checklist

- [ ] Send board JSON + user message + conversation history to AI.
- [ ] Enforce documented structured output schema from Part 5.
- [ ] Parse AI response into:
  - [ ] User-facing assistant message
  - [ ] Optional board mutation payload
- [ ] Validate mutation payload before applying DB updates.

### Tests

- [ ] Unit tests for schema validation and parser behavior.
- [ ] Integration tests for:
  - [ ] Message-only responses
  - [ ] Message + valid board update
  - [ ] Invalid structured output fallback behavior
- [ ] Regression tests for preserving board integrity.

### Success Criteria

- [ ] AI responses are reliably parsed into documented schema.
- [ ] Optional board updates are applied only when valid.
- [ ] Invalid outputs do not corrupt persisted board data.

## Part 10: Frontend AI Sidebar UX

### Checklist

- [ ] Add responsive sidebar chat UI aligned with project color scheme.
- [ ] Support conversation history display and user input.
- [ ] Wire sidebar to backend AI endpoint.
- [ ] Apply AI-issued board updates and refresh board automatically.
- [ ] Ensure mobile and desktop usability.

### Tests

- [ ] Frontend unit tests for chat UI state and rendering.
- [ ] Integration tests for chat request/response and board refresh.
- [ ] End-to-end scenario: user asks AI to modify board, UI updates automatically.

### Success Criteria

- [ ] AI chat sidebar is functional and responsive.
- [ ] Board refreshes automatically after valid AI mutations.
- [ ] No regressions in login, board interactions, or persistence.

## Final Project Exit Criteria

- [ ] All 10 parts completed with checklist items checked.
- [ ] Backend and frontend unit coverage each `>=80%`.
- [ ] Integration test suites pass.
- [ ] Local Dockerized app runs with start/stop scripts.
- [ ] User confirms MVP acceptance.
