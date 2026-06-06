# 048 — Annotate main.py routes with OpenAPI metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md), [039-annotate-schemas-chat](039-annotate-schemas-chat.md), [040-annotate-schemas-user-errors](040-annotate-schemas-user-errors.md), [045-annotate-router-exercises](045-annotate-router-exercises.md), [046-annotate-router-workouts](046-annotate-router-workouts.md), [047-annotate-router-chat](047-annotate-router-chat.md)

## Objective

Add `tags`, `response_model`, and `summary` to the `/healthz` and `/auth/me` routes defined directly on the `app` instance in `backend/app/main.py` so these routes appear properly in the Swagger UI.

## Approach

Both routes are currently minimal:
- `/healthz` (line 97): `@app.get("/healthz")` — missing `tags`, `response_model`, `summary`
- `/auth/me` (line 128): `@app.get("/auth/me", tags=["auth"])` — missing `response_model` and `summary`

The `/healthz` response shape is `{"status": "ok"}` — use `response_model=dict`. The `/auth/me` response returns `{"id": str, "email": str}` — use `response_model=dict` for simplicity (or a small inline schema if preferred, but `dict` avoids extra schema clutter).

Also import `ErrorResponse` from `app.schemas.errors` for documenting the 401 on `/auth/me`.

## Steps

### 1. Annotate /healthz  <!-- agent: general-purpose -->

Edit `backend/app/main.py`:

1. Replace `@app.get("/healthz")` (line 97) with:
   ```python
   @app.get(
       "/healthz",
       tags=["health"],
       response_model=dict,
       summary="Health check",
       description="Returns {\"status\": \"ok\"} when the service is running. No authentication required.",
   )
   ```

- [x] `/healthz` decorator has `tags=["health"]`
- [x] `/healthz` decorator has `response_model=dict`
- [x] `/healthz` decorator has `summary="Health check"`
- [x] `/healthz` decorator has `description=`

### 2. Annotate /auth/me  <!-- agent: general-purpose -->

1. Add import near the top of `main.py`: `from app.schemas.errors import ErrorResponse` (if not already imported).

2. Replace `@app.get("/auth/me", tags=["auth"])` (line 128) with:
   ```python
   @app.get(
       "/auth/me",
       tags=["auth"],
       response_model=dict,
       summary="Get current user",
       description="Return the authenticated user's ID and email address. Requires a valid JWT Bearer token.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
       },
   )
   ```

- [x] `/auth/me` decorator has `response_model=dict`
- [x] `/auth/me` decorator has `summary="Get current user"`
- [x] `/auth/me` decorator has `description=`
- [x] `/auth/me` decorator has `responses={401: ...}`
- [x] Existing `tags=["auth"]` is preserved
- [x] File is valid Python

## Acceptance Criteria

- [x] `/healthz` has `tags`, `response_model`, `summary`, and `description` in its decorator
- [x] `/auth/me` has `response_model`, `summary`, `description`, and `responses` in its decorator
- [ ] Running `python -c "from app.main import app; routes = {r.path: r for r in app.routes}; print(routes['/healthz'].summary, routes['/auth/me'].summary)"` from `backend/` prints both summaries without error
- [ ] No existing tests are broken

---
**UAT**: [`.docs/uat/048-annotate-main-routes.uat.md`](../uat/048-annotate-main-routes.uat.md)
