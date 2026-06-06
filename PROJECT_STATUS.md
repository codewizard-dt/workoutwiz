# Project Status

**Last updated:** 2026-06-05

## Current Focus

[ROADMAP-003: OpenAPI/Swagger Annotations](.docs/roadmaps/003-openapi-swagger-annotations.md) — enriching all Pydantic schemas and FastAPI routes with full OpenAPI metadata for assessor-ready Swagger UI.

## Active Tasks

No active tasks — all ROADMAP-002 work is complete.

## Recently Completed

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
