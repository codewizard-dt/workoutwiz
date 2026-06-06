# 045 — Annotate routers/exercises.py with OpenAPI route metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md), [039-annotate-schemas-chat](039-annotate-schemas-chat.md), [040-annotate-schemas-user-errors](040-annotate-schemas-user-errors.md)

## Objective

Add `summary`, `description`, and `responses={401: ..., 422: ...}` to the `GET /exercises` route decorator in `backend/app/routers/exercises.py` so the Swagger UI shows assessor-ready documentation for the exercise listing endpoint.

## Approach

The router already has `tags=["exercises"]` and the route already has `response_model=list[ExerciseRead]`. Only `summary`, `description`, and documented error responses need to be added to the decorator. Import `ErrorResponse` from `app.schemas.errors` for the 401 response model.

The `responses` parameter of FastAPI route decorators accepts `{status_code: {"model": Schema, "description": "..."}}`. For 422, FastAPI auto-generates the validation error body so we only need a description.

## Steps

### 1. Add summary, description, and responses to GET /exercises  <!-- agent: general-purpose -->

Edit `backend/app/routers/exercises.py`:

1. Add import: `from app.schemas.errors import ErrorResponse`

2. Replace the route decorator `@router.get("/", response_model=list[ExerciseRead])` with:
   ```python
   @router.get(
       "/",
       response_model=list[ExerciseRead],
       summary="List exercises",
       description=(
           "Return all exercises, optionally filtered by name, muscle group, "
           "equipment, or priority tier. Results are ordered by priority_tier ascending."
       ),
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
           422: {"description": "Validation error — one or more query parameters failed type or constraint checks"},
       },
   )
   ```

- [x] `ErrorResponse` is imported from `app.schemas.errors`
- [x] `@router.get` decorator includes `summary=`
- [x] `@router.get` decorator includes `description=`
- [x] `@router.get` decorator includes `responses=` with 401 and 422 keys
- [x] `response_model=list[ExerciseRead]` is preserved
- [x] File is valid Python (no syntax errors)

## Acceptance Criteria

- [x] `backend/app/routers/exercises.py` imports `ErrorResponse`
- [x] `GET /exercises` decorator has `summary`, `description`, and `responses` keys
- [ ] Running `python -c "from app.routers.exercises import router; r = [r for r in router.routes if r.path == '/'][0]; print(r.summary, r.description)"` from `backend/` prints the summary and description without error
- [ ] No existing tests are broken

---
**UAT**: [`.docs/uat/045-annotate-router-exercises.uat.md`](../uat/045-annotate-router-exercises.uat.md)
