# Project Status

**Last updated:** 2026-06-08 (ROADMAP-006 complete; tasks 086–101, 103–104 all shipped; type-safety patch merged)

## Current Focus

Remaining open tasks: **TASK-071** (feedback submission UI, 5/5 steps done — pending UAT) and **TASK-084** (test-source-type-population, 0/5).

## Active Tasks

| # | Task | Objective |
|---|------|-----------|
| 071 | [feedback-submission-ui](.docs/tasks/071-feedback-submission-ui.md) | FeedbackForm component: star rating + text, POST /kg/feedback — implementation done, pending UAT. |
| 084 | [test-source-type-population](.docs/tasks/084-test-source-type-population.md) | Write tests asserting every exercise in KG recommendation has source_type set to a valid enum value. |

## Recently Completed

### KG Retrieval Expansion & Type-Safety Patch (2026-06-08)
- **TASK-103**: Biomarker & lab-result KG nodes wired into retrieval graph — `get_biomarkers()`, `get_lab_results()` in `traversal.py`; `run_biomarker_traversal` node in `retrieval_graph.py`; `ContextSlice` extended; schema constraints + seed coverage for all 15 personas.
- **TASK-104**: Coach–member chat history KG nodes wired in — `get_recent_chat_history()` in `traversal.py`; `run_chat_history_traversal` node; `ContextSlice` extended; `ChatMessage` schema constraint; all 15 personas seeded.
- **Type-safety patch**: merge conflict resolution, unused variable removal, type annotations, import fixes across `coach.py`, `workout_generator.py`, `context_assembler.py`, `RatingWidget.tsx`, `CoachPage.tsx`, `WorkoutNewPage.tsx`, `frontend/src/types/index.ts`, `tsconfig.app.json`, `pyrightconfig.json`.

### ROADMAP-006: Assessment Gap Closure (2026-06-07 → 2026-06-08)
All 19 items shipped — repo is now assessment-submission-ready:
- **Phase 1 — Quick Wins**: TASK-086 (README KG eval section), TASK-087 (stale intent-values test), TASK-088 (cooldown phase), TASK-089 (sub-agent LLM error handling).
- **Phase 2 — KG Depth**: TASK-090 (3-pass concept resolver), TASK-091 (Muscle/Equipment/Pattern nodes), TASK-092 (fix retrieval double-traversal), TASK-093 (Neo4j driver singleton).
- **Phase 3 — Frontend Completion**: TASK-094 (exclusion filter UI), TASK-095 (coach chat image support), TASK-096 (coach message charts), TASK-097 (coach member switcher), TASK-098 (workout duration field).
- **Phase 4 — Polish**: TASK-099 (multi-persona context seeding), TASK-101 (fix ChatMessage KG result type).

### UI Polish & Auth Hardening (2026-06-06)
- **Landing page** — new `LandingPage.tsx` at `/` with full-viewport hero (`workout-wiz-hero-selected.png`), features grid, and footer CTA; authenticated users redirected to `/chat`.
- **Logo** — updated to `workout-wiz-logo-smile.png` across AppShell, LoginPage, RegisterPage, and LandingPage.
- **Global layout** — AppShell wraps `children` in a fixed 1280px-wide centred container so all pages have consistent width regardless of content volume.
- **Exercises page** — wrapped in `ProtectedRoute` + `AppShell`; redundant `maxWidth`/`margin` removed.
- **Login / Register** — ember-gradient radial blob decorations added to background.
- **Chat UX** — textarea background changed from grey `var(--input)` to white `var(--surface-card)` for proper contrast; prompt chips now auto-send on click instead of populating the textarea.
- **401 → logout** — `apiFetch` wrapper dispatches `ww:unauthorized` custom event on 401; `AuthProvider` listens and calls `setToken(null)`; `ProtectedRoute` then redirects to `/login`.
- **Active workout draft** — AppShell reads `ww_workout_draft` localStorage key and shows "Current Workout (N)" badge instead of "Start New Workout" when exercises are queued; updates reactively via `ww:draft-updated` events; ExercisesPage dispatches the event after adding an exercise.
- **WorkoutNewPage draft hydration** — on mount, draft from localStorage is converted to `WorkoutSequence[]` and loaded into the sequence panel; cleared on save or explicit clear.
- **Workout generation button** — backend `ChatResponse` now includes `workout_draft` (extracted from `build_workout_tool` `ToolMessage`); WorkoutNewPage shows a "✓ Use This Workout" button on generator responses that loads the structured plan into the sequence panel.

### Live LLM Integration Tests
- Fixed pre-existing `conftest.py` seed bug: `movement_patterns` was being cast as `jsonb` but the column is `varchar[]` after migration `e4a51dde0a60` — all existing tests were broken by this.
- Added `api_key=settings.anthropic_api_key` to every `ChatAnthropic` instantiation in `hub.py`, `coach.py`, `workout_generator.py`, `workout_logger.py` so the key from root `.env` is always passed explicitly.
- Registered `live` pytest marker in `pyproject.toml`.
- Created `backend/tests/test_live_llm.py` — 6 tests covering all four agent pathways (`COACH`, `WORKOUT_GENERATE`, `WORKOUT_LOG`, clarification), the audit endpoint, and multi-turn session accumulation against the real Anthropic API.

Run live tests: `cd backend && pytest -m live -v`

### Phase 5: Critical-Path Tests + Polish (ROADMAP-002)
- [TASK-033: Critical-Path Test A: Router Intent Classification](.docs/tasks/completed/033-critical-path-router-test.md)
- [TASK-034: Critical-Path Test B: Workout Generator Grounding](.docs/tasks/completed/034-critical-path-generator-test.md)
- [TASK-035: E2E Smoke Test](.docs/tasks/completed/035-e2e-smoke-test.md)
- [TASK-036: README Production Evaluation Section](.docs/tasks/completed/036-readme-production-eval.md)

### Phase 4: Chat Endpoint + UI + Audit (ROADMAP-002)
- [TASK-026: Clarification Node](.docs/tasks/completed/026-clarification-node.md)
- [TASK-030: Chat Endpoint](.docs/tasks/completed/030-chat-endpoint.md)
- [TASK-031: Web UI](.docs/tasks/completed/031-web-ui.md)
- [TASK-032: LLM Audit Log](.docs/tasks/completed/032-llm-audit-log.md)

### Phase 3: Sub-Agents (ROADMAP-002)
- [TASK-027: Coach Sub-Agent Graph](.docs/tasks/completed/027-coach-sub-agent.md)
- [TASK-028: Workout Generator Sub-Agent](.docs/tasks/completed/028-workout-generator-sub-agent.md)
- [TASK-029: Workout Logger Sub-Agent](.docs/tasks/completed/029-workout-logger-sub-agent.md)

### Phase 2: Hub Agent (ROADMAP-002)
- [TASK-023: Hub StateGraph with Typed State and Explicit Edges](.docs/tasks/completed/023-hub-stategraph.md)
- [TASK-024: Router Node with Structured Output](.docs/tasks/completed/024-router-node.md)
- [TASK-025: Conditional Edge Routing Integration Tests](.docs/tasks/completed/025-conditional-edge-routing.md)

### Phase 1: Foundation (ROADMAP-002)
- [TASK-019: Python Package Setup](.docs/tasks/completed/019-python-package-setup.md)
- [TASK-020: Install Core Dependencies](.docs/tasks/completed/020-install-core-dependencies.md)
- [TASK-021: Shared Typed State and Route Schema](.docs/tasks/completed/021-shared-state-and-route-schema.md)
- [TASK-022: Exercise Data Loader](.docs/tasks/completed/022-exercise-data-loader.md)

### Infrastructure (ROADMAP-001)
- FastAPI project structure, logging/error handling, exercise seed data, workout endpoints, integration tests
- Vite + React + TypeScript scaffold, Tailwind + shadcn/ui, React Query state, production README, Python package setup
- Docker dev stack: `docker-compose.yml` (all services with image refs), `docker-compose.build.yml` (slim build/volume overlay), `backend/Dockerfile.dev`, `frontend/Dockerfile.dev`, Makefile Docker targets, `security.yml` CodeQL matrix, `vite.config.ts` PROXY_TARGET patch

## Upcoming

- Complete TASK-084: write `source_type` population tests for KG exercise recommendations.
- Complete TASK-071 UAT: walk through feedback submission UI tests and move to `completed/`.
- ROADMAP-003 Phase 1: Annotate Pydantic schemas (`exercise.py`, `workout.py`, `chat.py`, `user.py`, `errors.py`)
- ROADMAP-003 Phase 2: Annotate FastAPI route decorators (`exercises.py`, `workouts.py`, `chat.py`, `main.py`)
