# Roadmap 001: Port Fitness Tracker to Modern Stack

> Replace the legacy Node.js/Express/Mongoose/React system with a modern FastAPI backend, PostgreSQL database, and Vite/React/TypeScript frontend — then integrate with the multi-agent routing hub.

- **Status**: active
- **Created**: 2026-06-03
- **Last updated**: 2026-06-03 (Phase 0 walkthrough complete)
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

- [ ] Create FastAPI project structure with Pydantic models, SQLAlchemy setup, and environment config
- [ ] Set up PostgreSQL database, Alembic migrations tooling, and connection pooling
- [ ] Design relational schema for User, Exercise, Workout, and WorkoutSequenceItem (map from Mongoose nesting)
- [ ] Configure logging, error handling, and async patterns for FastAPI

## Phase 2: Backend Port & Data Migration

> Implement all API endpoints and migrate exercise data.

- [ ] Import and validate exercises.json, load into PostgreSQL
- [ ] Implement `/auth` endpoints (register, signin, signout, token validation) with JWT
- [ ] Implement `/exercises` endpoints (list, search by name/bodyPart/equipment/target)
- [ ] Implement `/workouts` endpoints (list, create, update, delete for authenticated users)
- [ ] Write integration tests for all routes with real database

## Phase 3: Frontend Port

> Migrate React app to Vite and update state management.

- [ ] Scaffold Vite + React + TypeScript project with modern tooling (ESLint, Prettier)
- [ ] Migrate Semantic UI components or evaluate modern UI library alternative
- [ ] Port Redux state (auth, exercises, workouts) to modern state management (React Query, Zustand, or local state)
- [ ] Update API client (Axios) to call FastAPI endpoints with new auth headers
- [ ] Port all React components and test UI against new backend

## Phase 4: Testing & Polish

> Verify resilience, edge cases, and production readiness.

- [ ] End-to-end tests (user auth flow, workout creation, exercise search)
- [ ] Edge case testing (missing data, invalid IDs, concurrent requests, auth token expiry)
- [ ] Performance baseline (API response times, database query optimization)
- [ ] README: Add "How I Would Evaluate This in Production" section per PRD-001 AC-3

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
