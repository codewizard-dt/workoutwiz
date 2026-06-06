# Roadmap 001: Port Fitness Tracker to Modern Stack

> Replace the legacy Node.js/Express/Mongoose/React system with a modern FastAPI backend, PostgreSQL database, and Vite/React/TypeScript frontend — then integrate with the multi-agent routing hub.

- **Status**: done
- **Created**: 2026-06-03
- **Last updated**: 2026-06-04 (all tasks completed)
- **Owner**: David Taylor
- **Linked PRD**: PRD-001
- **Linked ADRs**: —
- **Tags**: backend-migration, database, frontend-modernization

## Goal

When complete, the legacy fitness tracker will be replaced with a production-ready FastAPI backend (PostgreSQL, SQLAlchemy ORM) and modern Vite/React/TypeScript frontend, with all three core workflows (auth, exercise management, workout logging) ported and tested. The system will be ready for the LangGraph multi-agent routing layer to be wired in as a separate effort.

## Phase 0: Assessment & Walkthrough

> Systematically decide which legacy features, models, and workflows are worth porting to the new stack.

- [x] Document all legacy features, models, and API endpoints (see `.docs/legacy.md`)
- [x] Walkthrough with user: which features are must-have, nice-to-have, or out-of-scope for the port
- [x] Define porting decisions: schema translation strategy, auth approach, state management for new frontend
- [x] Identify any legacy gaps that need to be fixed in the modern version

## Phase 1: Foundation

> Set up modern backend and database infrastructure.

- [x] [TASK-001: Create FastAPI Project Structure](../tasks/completed/001-fastapi-project-structure.md)
- [x] [TASK-002: Set Up PostgreSQL Database, Alembic Migrations, and Connection Pooling](../tasks/completed/002-postgres-alembic-setup.md)
- [x] [TASK-003: Design Relational Schema: User, Exercise, Workout, WorkoutSequence, WorkoutSet](../tasks/completed/003-relational-schema-design.md)
- [x] [TASK-004: Configure Logging, Error Handling, and Async Patterns for FastAPI](../tasks/completed/004-fastapi-logging-error-handling.md)

## Phase 2: Backend Port & Data Migration

> Implement all API endpoints and migrate exercise data.

- [x] [TASK-005: Import and Validate exercises.json, Load into PostgreSQL](../tasks/completed/005-exercise-seed-data.md)
- [x] [TASK-006: Implement /auth Endpoints with fastapi-users](../tasks/completed/006-auth-endpoints.md)
- [x] [TASK-007: Implement /exercises Endpoints](../tasks/completed/007-exercise-endpoints.md)
- [x] [TASK-008: Implement /workouts Endpoints](../tasks/completed/008-workout-endpoints.md)
- [x] [TASK-009: Write Integration Tests for All Routes with Real Database](../tasks/completed/009-integration-tests.md)

## Phase 3: Frontend Port

> Migrate React app to Vite and update state management.

- [x] [TASK-010: Scaffold Vite + React + TypeScript Frontend Project](../tasks/completed/010-vite-react-ts-scaffold.md)
- [x] [TASK-011: Install Tailwind CSS and shadcn/ui (Replace Semantic UI)](../tasks/completed/011-tailwind-shadcn-ui.md)
- [x] [TASK-012: Set Up React Query (TanStack Query) State Management](../tasks/completed/012-react-query-state.md)
- [x] [TASK-014: Port React Components and Test UI Against Backend](../tasks/completed/014-port-react-components.md)

## Phase 4: Testing & Polish

> Verify resilience, edge cases, and production readiness.

- [x] [TASK-015: End-to-End Tests (User Auth Flow, Workout Creation, Exercise Search)](../tasks/completed/015-e2e-tests.md)
- [x] [TASK-016: Edge Case Testing (Missing Data, Invalid IDs, Auth Token Expiry)](../tasks/completed/016-edge-case-testing.md)
- [x] [TASK-017: Performance Baseline (API Response Times, Query Optimization)](../tasks/completed/017-performance-baseline.md)
- [x] [TASK-018: Add "How I Would Evaluate This in Production" README Section](../tasks/completed/018-production-readme.md)

## Notes

### Phase 0 Decisions (2026-06-03)

| Decision | Choice | Notes |
|----------|--------|-------|
| **Exercise data source** | `1-multi-agent/exercises.json` (50 exercises, UUID IDs) | NOT the legacy MongoDB dataset; new schema already matches PRD needs |
| **Exercise loading** | One-time seed script at migration time | Parse JSON → insert all 50 rows; no runtime dependency on file |
| **Auth library** | `fastapi-users` | Production-quality; assessors will recognize it; minimal boilerplate |
| **Workout DB schema** | 3 tables: Workout → WorkoutSequence (phase) → WorkoutSet | Fully relational; clean SQL joins; retains warmup/main/cooldown concept |
| **Set types** | `SetType` enum: `STRENGTH` (reps + weight) / `CARDIO` (duration + speed/distance/etc.) | Driven by exercise's `is_reps` / `is_duration` flags |
| **Weight tracking** | Include `weight_kg` on WorkoutSet (required for STRENGTH sets) | `barWeight` / `weightAssist` dropped; clean weight field only |
| **Exercise search** | Adapt legacy filters + expand to `movement_patterns` and `priority_tier` | `muscle_groups` replaces bodyPart/target; `equipment_required` replaces equipment |
| **UI library** | Tailwind CSS + shadcn/ui | Replaces Semantic UI React |
| **State management** | React Query (TanStack Query) + local `useState` | No Redux; server state via React Query; auth/UI state local |
| **NOT porting** | Exercise GIFs (`gifUrl`), `barWeight`, `weightAssist`, Redux DevTools | No image hosting needed; cleaner weight model |

### Key Schema Changes vs Legacy

| Legacy (MongoDB/Mongoose) | New (PostgreSQL/SQLAlchemy) |
|---------------------------|-----------------------------|
| `Exercise.bodyPart` (single string) | `Exercise.muscle_groups` (string array, or junction table) |
| `Exercise.target` (single string) | Removed — covered by `muscle_groups` |
| `Exercise.gifUrl` | Removed |
| `Exercise.equipment` (single string) | `Exercise.equipment_required` (string array) |
| `Workout.sequenceList` (nested array) | `WorkoutSequence` table (phase) → `WorkoutSet` table (individual set) |
| `WorkoutSet` single type, all fields nullable | `WorkoutSet.set_type` (`STRENGTH` / `CARDIO`) with conditional fields |

**Delivery**: This roadmap delivers the ported system ready for the LangGraph multi-agent integration (PRD-001's routing hub and sub-agents). The multi-agent work is a **separate roadmap**.
