# Project Status

**Last updated:** 2026-06-07 (ROADMAP-006 created: 16 assessment-gap-closure tasks (086–101) authored via /task-add)

## Current Focus

[ROADMAP-006: Assessment Gap Closure](.docs/roadmaps/006-assessment-gap-closure.md) — close every gap from the 2026-06-07 assessment audit (multi-agent, knowledge-graph, and candidate-assessment-main specs) so the repo is submission-ready.

**Phase 1 — Quick Wins**
- [TASK-086: README KG production-eval section](.docs/tasks/086-readme-kg-production-eval.md) — add a "How I would evaluate the KG system in production" README section.
- [TASK-087: Fix stale test_intent_values](.docs/tasks/087-fix-stale-intent-values-test.md) — add KNOWLEDGE_GRAPH to the Intent-enum test assertion.
- [TASK-088: Cooldown phase in build_workout](.docs/tasks/088-build-workout-cooldown-phase.md) — emit a non-empty cooldown phase of stretch/mobility movements.
- [TASK-089: Sub-agent LLM error handling](.docs/tasks/089-subagent-llm-error-handling.md) — graceful fallback + audit entry in coach/generator nodes instead of HTTP 500.

**Phase 2 — KG Depth**
- [TASK-090: 3-pass concept resolver](.docs/tasks/090-concept-resolver-3pass.md) — runtime exact → fuzzy → embedding resolver with confidence thresholds.
- [TASK-091: Muscle/MovementPattern/Equipment nodes](.docs/tasks/091-kg-muscle-equipment-pattern-nodes.md) — promote array properties to first-class nodes with typed edges.
- [TASK-092: Fix retrieval double-traversal](.docs/tasks/092-fix-retrieval-double-traversal.md) — thread pre-fetched state into assemble_context.
- [TASK-093: Neo4j driver singleton](.docs/tasks/093-neo4j-driver-singleton.md) — shared connection-pooled driver via lifespan + dependency.

**Phase 3 — Frontend Completion**
- [TASK-094: Exclusion/equipment filter UI](.docs/tasks/094-workout-exclusion-filter-ui.md) — interactive adjustment controls on the New Workout page.
- [TASK-095: Coach chat image support](.docs/tasks/095-coach-chat-image-support.md) — attach and view images in the Coach Copilot chat.
- [TASK-096: Coach message/comparison charts](.docs/tasks/096-coach-message-charts.md) — message-pattern + 4-week comparison charts (Recharts).
- [TASK-097: Coach member switcher](.docs/tasks/097-coach-member-switcher.md) — member list/switcher (depends on 099).
- [TASK-098: Workout duration field](.docs/tasks/098-workout-duration-field.md) — structured session-duration/time-window control.

**Phase 4 — Polish**
- [TASK-099: Multi-persona context seeding](.docs/tasks/099-seed-multi-persona-context.md) — rich member context for all personas, not just Jordan Rivera.
- [TASK-100: OPE & COPPER ontology docs](.docs/tasks/100-document-ope-copper-ontologies.md) — document what was used vs omitted, with rationale.
- [TASK-101: Fix ChatMessage kg_result type](.docs/tasks/101-fix-chatmessage-kg-result-type.md) — add kg_result to the exported TypeScript interface.

## Active Tasks

| # | Task | Objective |
|---|------|-----------|
| 086 | [readme-kg-production-eval](.docs/tasks/086-readme-kg-production-eval.md) | Add a "How I would evaluate the KG system in production" README section (retrieval quality, injury-safety monitoring, latency, GraphRAG signals). |
| 087 | [fix-stale-intent-values-test](.docs/tasks/087-fix-stale-intent-values-test.md) | Update test_intent_values to include KNOWLEDGE_GRAPH so the Intent-enum assertion passes. |
| 088 | [build-workout-cooldown-phase](.docs/tasks/088-build-workout-cooldown-phase.md) | Make build_workout_tool emit a non-empty cooldown phase of low-intensity stretch/mobility movements from the dataset. |
| 089 | [subagent-llm-error-handling](.docs/tasks/089-subagent-llm-error-handling.md) | Wrap LLM calls in coach/generator nodes to return a graceful fallback + audit entry instead of HTTP 500. |
| 090 | [concept-resolver-3pass](.docs/tasks/090-concept-resolver-3pass.md) | Implement a runtime 3-pass concept resolver (exact → fuzzy → embedding) with confidence thresholds and graceful degradation. |
| 091 | [kg-muscle-equipment-pattern-nodes](.docs/tasks/091-kg-muscle-equipment-pattern-nodes.md) | Promote Muscle/MovementPattern/Equipment to first-class Neo4j nodes with typed TARGETS/REQUIRES/HAS_PATTERN edges. |
| 092 | [fix-retrieval-double-traversal](.docs/tasks/092-fix-retrieval-double-traversal.md) | Eliminate redundant double-traversal in retrieval_graph.assemble by threading pre-fetched state into context assembly. |
| 093 | [neo4j-driver-singleton](.docs/tasks/093-neo4j-driver-singleton.md) | Replace per-request Neo4j driver instantiation with a shared connection-pooled driver via lifespan + dependency. |
| 094 | [workout-exclusion-filter-ui](.docs/tasks/094-workout-exclusion-filter-ui.md) | Add interactive exercise-exclusion and equipment-filter controls to the New Workout page. |
| 095 | [coach-chat-image-support](.docs/tasks/095-coach-chat-image-support.md) | Let a coach attach and view images in the Coach Copilot chat (client-side MVP). |
| 096 | [coach-message-charts](.docs/tasks/096-coach-message-charts.md) | Add message-pattern and 4-week comparison charts to the Coach dashboard using Recharts. |
| 097 | [coach-member-switcher](.docs/tasks/097-coach-member-switcher.md) | Add a member list/switcher so the coach dashboard is not hardcoded to one member (depends on 099). |
| 098 | [workout-duration-field](.docs/tasks/098-workout-duration-field.md) | Add a structured session-duration/time-window control to the New Workout page. |
| 099 | [seed-multi-persona-context](.docs/tasks/099-seed-multi-persona-context.md) | Seed rich member context (labs, chat, workouts, profile) for all personas, not just Jordan Rivera (blocks 097). |
| 100 | [document-ope-copper-ontologies](.docs/tasks/100-document-ope-copper-ontologies.md) | Document OPE & COPPER ontology decisions (used vs omitted, with rationale) in the methodology doc. |
| 101 | [fix-chatmessage-kg-result-type](.docs/tasks/101-fix-chatmessage-kg-result-type.md) | Add the kg_result field (and KGResult type) to the exported ChatMessage TypeScript interface. |

## Recently Completed

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

- ROADMAP-003 Phase 1: Annotate Pydantic schemas (`exercise.py`, `workout.py`, `chat.py`, `user.py`, `errors.py`)
- ROADMAP-003 Phase 2: Annotate FastAPI route decorators (`exercises.py`, `workouts.py`, `chat.py`, `main.py`)
