# Roadmap 003: OpenAPI/Swagger Annotations

> Make every backend API route assessor-ready in the Swagger UI by adding full OpenAPI metadata to all route decorators and Pydantic schemas.

- **Status**: active
- **Created**: 2026-06-05
- **Last updated**: 2026-06-05
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: api, docs, openapi

## Goal

Every custom FastAPI route has `tags`, `summary`, `description`, `response_model`, and documented error responses (`401`/`404`/`422`). Every Pydantic schema uses `Field(description=...)` for key fields. The Swagger UI at `/docs` is assessor-ready with no blank or auto-generated-only metadata.

## Phase 1: Schemas

> Enrich all Pydantic schemas with `Field(description=...)` and `example=` values so route docs inherit rich schema-level metadata automatically.

- [ ] Annotate `schemas/exercise.py` — add `Field(description=...)` to `ExerciseRead` and filter param fields
- [ ] Annotate `schemas/workout.py` — add `Field(description=...)` to `WorkoutCreate`, `WorkoutRead`, sequence and set schemas
- [ ] Annotate `schemas/chat.py` — add `Field(description=..., example=...)` to `ChatRequest` and `ChatResponse`
- [ ] Annotate `schemas/user.py` and `schemas/errors.py` — add `Field(description=...)` to `UserRead`, `UserCreate`, and error schemas

## Phase 2: Routes

> Add `summary`, `description`, `response_model`, and `responses={401/404/422}` to every custom route decorator.

- [ ] Annotate `routers/exercises.py` — add `summary`, `description`, `responses={401: ..., 422: ...}` to `GET /exercises`
- [ ] Annotate `routers/workouts.py` — add `summary`, `description`, `responses={401: ..., 404: ..., 422: ...}` to all 5 CRUD endpoints
- [ ] Annotate `routers/chat.py` — add `summary`, `description`, missing `response_model` on audit endpoint, and error responses to all 3 endpoints
- [ ] Annotate `main.py` routes — add `tags`, `response_model`, `summary` to `/healthz` and `/auth/me`

## Notes

