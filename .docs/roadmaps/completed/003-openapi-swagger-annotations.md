# Roadmap 003: OpenAPI/Swagger Annotations

> Make every backend API route assessor-ready in the Swagger UI by adding full OpenAPI metadata to all route decorators and Pydantic schemas.

- **Status**: done
- **Created**: 2026-06-05
- **Last updated**: 2026-06-06
- **Owner**: David Taylor
- **Linked PRD**: —
- **Linked ADRs**: —
- **Tags**: api, docs, openapi

## Goal

Every custom FastAPI route has `tags`, `summary`, `description`, `response_model`, and documented error responses (`401`/`404`/`422`). Every Pydantic schema uses `Field(description=...)` for key fields. The Swagger UI at `/docs` is assessor-ready with no blank or auto-generated-only metadata.

## Phase 1: Schemas

> Enrich all Pydantic schemas with `Field(description=...)` and `example=` values so route docs inherit rich schema-level metadata automatically.

- [x] [TASK-037: Annotate schemas/exercise.py with OpenAPI Field metadata](../tasks/completed/037-annotate-schemas-exercise.md)
- [x] [TASK-038: Annotate schemas/workout.py with OpenAPI Field metadata](../tasks/completed/038-annotate-schemas-workout.md)
- [x] [TASK-039: Annotate schemas/chat.py with OpenAPI Field metadata](../tasks/completed/039-annotate-schemas-chat.md)
- [x] [TASK-040: Annotate schemas/user.py and schemas/errors.py with OpenAPI Field metadata](../tasks/completed/040-annotate-schemas-user-errors.md)

## Phase 2: Routes

> Add `summary`, `description`, `response_model`, and `responses={401/404/422}` to every custom route decorator.

- [x] [TASK-045: Annotate routers/exercises.py with OpenAPI route metadata](../tasks/completed/045-annotate-router-exercises.md)
- [x] [TASK-046: Annotate routers/workouts.py with OpenAPI route metadata](../tasks/completed/046-annotate-router-workouts.md)
- [x] [TASK-047: Annotate routers/chat.py with OpenAPI route metadata](../tasks/completed/047-annotate-router-chat.md)
- [x] [TASK-048: Annotate main.py routes with OpenAPI metadata](../tasks/completed/048-annotate-main-routes.md)

## Notes

