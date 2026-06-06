# 046 — Annotate routers/workouts.py with OpenAPI route metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md), [039-annotate-schemas-chat](039-annotate-schemas-chat.md), [040-annotate-schemas-user-errors](040-annotate-schemas-user-errors.md), [045-annotate-router-exercises](045-annotate-router-exercises.md)

## Objective

Add `summary`, `description`, and `responses={401: ..., 404: ..., 422: ...}` to all 5 CRUD route decorators in `backend/app/routers/workouts.py` so the Swagger UI shows assessor-ready documentation for every workout endpoint.

## Approach

The router already has `tags=["workouts"]` and all routes have `response_model` set (except `DELETE` which returns 204). Import `ErrorResponse` from `app.schemas.errors` for the error response models. Add `summary`, `description`, and `responses` to each `@router.get/post/put/delete` decorator. 404 only applies to the three endpoints that fetch by `workout_id` (GET by id, PUT, DELETE).

## Steps

### 1. Import ErrorResponse and annotate all 5 routes  <!-- agent: general-purpose -->

Edit `backend/app/routers/workouts.py`:

1. Add import: `from app.schemas.errors import ErrorResponse`

2. Annotate `list_workouts` (line 13, `@router.get("/", ...)`):
   ```python
   @router.get(
       "/",
       response_model=list[WorkoutRead],
       summary="List workouts",
       description="Return all workouts belonging to the authenticated user, ordered by started_at descending.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           422: {"description": "Validation error"},
       },
   )
   ```

3. Annotate `create_workout` (line 21, `@router.post("/", ...)`):
   ```python
   @router.post(
       "/",
       response_model=WorkoutRead,
       status_code=201,
       summary="Create workout",
       description="Create a new workout for the authenticated user with optional sequences and sets.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           422: {"description": "Validation error — request body failed schema validation"},
       },
   )
   ```

4. Annotate `get_workout` (line 30, `@router.get("/{workout_id}", ...)`):
   ```python
   @router.get(
       "/{workout_id}",
       response_model=WorkoutRead,
       summary="Get workout",
       description="Return a single workout by ID. Only the owning user's workouts are accessible.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
           422: {"description": "Validation error — workout_id is not a valid UUID"},
       },
   )
   ```

5. Annotate `update_workout` (line 42, `@router.put("/{workout_id}", ...)`):
   ```python
   @router.put(
       "/{workout_id}",
       response_model=WorkoutRead,
       summary="Update workout",
       description="Replace a workout's data (started_at, ended_at, sequences). Full replacement — partial updates not supported.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
           422: {"description": "Validation error"},
       },
   )
   ```

6. Annotate `delete_workout` (line 55, `@router.delete("/{workout_id}", ...)`):
   ```python
   @router.delete(
       "/{workout_id}",
       status_code=204,
       summary="Delete workout",
       description="Permanently delete a workout and all its sequences and sets.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           404: {"model": ErrorResponse, "description": "Workout not found or does not belong to this user"},
           422: {"description": "Validation error — workout_id is not a valid UUID"},
       },
   )
   ```

- [x] `ErrorResponse` imported from `app.schemas.errors`
- [x] All 5 route decorators have `summary=`
- [x] All 5 route decorators have `description=`
- [x] All 5 route decorators have `responses=` (list_workouts and create_workout: 401+422; get/put/delete by id: 401+404+422)
- [x] All existing `response_model` and `status_code` values are preserved
- [x] File is valid Python <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/routers/workouts.py` imports `ErrorResponse`
- [x] All 5 route functions have `summary`, `description`, and `responses` in their decorators
- [x] Running `python -c "from app.routers.workouts import router; print(len(router.routes))"` from `backend/` prints `5` without error
- [ ] No existing tests are broken

---
**UAT**: [`.docs/uat/completed/046-annotate-router-workouts.uat.md`](../uat/completed/046-annotate-router-workouts.uat.md)
