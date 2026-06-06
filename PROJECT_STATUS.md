# Project Status

**Last updated:** 2026-06-06 (updated with TASK-084: Test source_type population)

## Current Focus

[ROADMAP-004: Knowledge Graph Coaching System](.docs/roadmaps/004-knowledge-graph-coaching-system.md) — building the Neo4j-backed coaching layer with GraphRAG retrieval, injury-aware generation, and exercise feedback.

- [TASK-049: Injury ingestion](.docs/tasks/049-injury-ingestion.md) — ingest synthetic injury records into Neo4j as Injury nodes + HAS_INJURY + CONTRAINDICATED_BY edges.
- [TASK-050: Exercise Neo4j ingestion](.docs/tasks/050-exercise-neo4j-ingestion.md) — load all 50 exercises from exercises.json into Neo4j as Exercise nodes and wire CONTRAINDICATED_BY edges to pre-existing Injury nodes.
- [TASK-051: Member profile ingestion](.docs/tasks/051-member-profile-ingestion.md) — create standalone idempotent ingest_members.py that MERGEs 15 synthetic Member nodes into Neo4j with all schema-required goal/preference properties.
- [TASK-052: Workout history ingestion](.docs/tasks/052-ingest-workout-history-neo4j.md) — load synthetic workout sessions into Neo4j as WorkoutSession nodes with PERFORMED and INCLUDED edges.
- [TASK-053: Feedback ingestion](.docs/tasks/053-feedback-ingestion-neo4j.md) — load ExerciseFeedback rows from PostgreSQL into Neo4j as FeedbackEvent nodes with edges to Exercise, WorkoutSession, and Set nodes.
- [TASK-054: ADR — GraphRAG retrieval strategy](.docs/tasks/054-graphrag-adr.md) — create an ADR covering traversal depth, embedding model, context token budget, and merge strategy for the GraphRAG retrieval layer.
- [TASK-055: Vector embeddings](.docs/tasks/055-vector-embeddings.md) — implement embed_exercises() and get_exercise_vector_store() with swappable embedding providers and Neo4j vector index.
- [TASK-056: Injury traversal queries](.docs/tasks/056-injury-traversal-queries.md) — implement Cypher traversal queries for injury-aware exercise filtering and member profile lookup.
- [TASK-057: Preference/feedback traversal](.docs/tasks/057-preference-feedback-traversal.md) — extend traversal.py with get_preferred_exercises() and get_performed_exercises() for preference and recency signals.
- [TASK-058: Context assembler](.docs/tasks/058-context-assembler.md) — create context_assembler.py with assemble_context() that merges traversal + vector results into a 2048-token-budgeted ContextSlice.
- [TASK-059: Retrieval sub-graph](.docs/tasks/059-retrieval-subgraph.md) — create retrieval_graph.py LangGraph StateGraph orchestrating the full GraphRAG retrieval pipeline, and wire KNOWLEDGE_GRAPH intent into the hub.

## Active Tasks

| # | Task | Objective |
|---|------|-----------|
| 049 | [injury-ingestion](.docs/tasks/049-injury-ingestion.md) | Ingest synthetic injury records into Neo4j as Injury nodes + HAS_INJURY + CONTRAINDICATED_BY edges. |
| 050 | [exercise-neo4j-ingestion](.docs/tasks/050-exercise-neo4j-ingestion.md) | Load all 50 exercises from exercises.json into Neo4j as Exercise nodes and wire CONTRAINDICATED_BY edges to pre-existing Injury nodes. |
| 051 | [member-profile-ingestion](.docs/tasks/051-member-profile-ingestion.md) | Create standalone idempotent ingest_members.py that MERGEs 15 synthetic Member nodes into Neo4j with all schema-required goal/preference properties. |
| 052 | [ingest-workout-history-neo4j](.docs/tasks/052-ingest-workout-history-neo4j.md) | Create ingest_workout_history.py — load synthetic workout sessions into Neo4j as WorkoutSession nodes with PERFORMED and INCLUDED edges. |
| 053 | [feedback-ingestion-neo4j](.docs/tasks/053-feedback-ingestion-neo4j.md) | Load ExerciseFeedback rows from PostgreSQL into Neo4j as FeedbackEvent nodes with edges to Exercise, WorkoutSession, and Set nodes. |
| 054 | [graphrag-adr](.docs/tasks/054-graphrag-adr.md) | Create an ADR for the GraphRAG retrieval strategy covering traversal depth, embedding model, context token budget, and merge strategy. |
| 055 | [vector-embeddings](.docs/tasks/055-vector-embeddings.md) | Implement embed_exercises() and get_exercise_vector_store() in backend/app/kg/embeddings.py with swappable sentence-transformers/OpenAI providers and a Neo4j vector index. |
| 056 | [injury-traversal-queries](.docs/tasks/056-injury-traversal-queries.md) | Implement Cypher traversal queries in backend/app/kg/traversal.py for injury-aware exercise filtering and member profile lookup. |
| 057 | [preference-feedback-traversal](.docs/tasks/057-preference-feedback-traversal.md) | Extend traversal.py with get_preferred_exercises() and get_performed_exercises() for preference and recency signals. |
| 058 | [context-assembler](.docs/tasks/058-context-assembler.md) | Create context_assembler.py with assemble_context() that merges traversal + vector results into a 2048-token-budgeted ContextSlice dict. |
| 059 | [retrieval-subgraph](.docs/tasks/059-retrieval-subgraph.md) | Create retrieval_graph.py with a LangGraph StateGraph orchestrating the full GraphRAG retrieval pipeline, and wire KNOWLEDGE_GRAPH intent into the hub. |
| 074 | [observability-adr](.docs/tasks/074-observability-adr.md) | Write Observability Stack ADR — document in-process audit_log extension to all agent nodes and KG layers. |
| 084 | [test-source-type-population](.docs/tasks/084-test-source-type-population.md) | Write tests asserting every exercise in KG recommendation has source_type set to valid enum (SAFE_SET \| PREFERRED \| VECTOR_SEARCH \| FALLBACK). |

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
