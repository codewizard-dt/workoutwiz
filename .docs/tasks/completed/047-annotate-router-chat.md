# 047 — Annotate routers/chat.py with OpenAPI route metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md), [039-annotate-schemas-chat](039-annotate-schemas-chat.md), [040-annotate-schemas-user-errors](040-annotate-schemas-user-errors.md), [045-annotate-router-exercises](045-annotate-router-exercises.md), [046-annotate-router-workouts](046-annotate-router-workouts.md)

## Objective

Add `summary`, `description`, `response_model` (missing on `get_audit`), and `responses={401: ..., 404: ..., 422: ...}` to all 3 route decorators in `backend/app/routers/chat.py` so the Swagger UI shows assessor-ready documentation for the chat, audit, and session endpoints.

## Approach

The router already has `tags=["chat"]`. The `chat` and `clear_session` routes already have `response_model` or `status_code` set; `get_audit` is missing `response_model`. The three existing docstrings on the functions should be moved into the `description=` parameter of the decorator (FastAPI uses the decorator `description` over function docstrings for display). Import `ErrorResponse` from `app.schemas.errors`.

The `get_audit` response shape is `{"session_id": str, "audit_log": list, "total_entries": int}` — add a `AuditResponse` Pydantic model to `schemas/chat.py` for proper typing, OR use a `Dict[str, Any]` inline response model (simpler — use `response_model=dict` since the shape is variable). Use `response_model=dict` to keep it minimal.

## Steps

### 1. Add response_model to get_audit and move docstrings to decorators  <!-- agent: general-purpose -->

Edit `backend/app/routers/chat.py`:

1. Add import: `from app.schemas.errors import ErrorResponse`

2. Annotate `chat` endpoint (line 19, `@router.post("/", response_model=ChatResponse)`):
   - Add `summary`, `description`, `responses` to the decorator.
   - Remove or keep the existing docstring (decorator description takes precedence in Swagger).
   ```python
   @router.post(
       "/",
       response_model=ChatResponse,
       summary="Send a chat message",
       description=(
           "Send a natural-language message to the fitness coaching multi-agent system. "
           "The hub router classifies intent (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK) "
           "using structured LLM output and delegates to the appropriate sub-agent. "
           "Session history is preserved across calls via the returned session_id."
       ),
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated — valid JWT Bearer token required"},
           422: {"description": "Validation error — request body failed schema validation"},
       },
   )
   ```

3. Annotate `get_audit` endpoint (line 67, `@router.get("/audit/{session_id}")`):
   - Add `response_model=dict`, `summary`, `description`, `responses`.
   ```python
   @router.get(
       "/audit/{session_id}",
       response_model=dict,
       summary="Get session audit log",
       description=(
           "Retrieve the full LLM reasoning audit log for a chat session. "
           "Returns ordered agent events including route decisions, sub-agent calls, and tool invocations."
       ),
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           404: {"model": ErrorResponse, "description": "Session not found — no conversation with this session_id exists in memory"},
           422: {"description": "Validation error"},
       },
   )
   ```

4. Annotate `clear_session` endpoint (line 83, `@router.delete("/session/{session_id}", status_code=204)`):
   ```python
   @router.delete(
       "/session/{session_id}",
       status_code=204,
       summary="Clear a session",
       description="Delete all in-memory conversation history for a chat session. Returns 204 with no body.",
       responses={
           401: {"model": ErrorResponse, "description": "Not authenticated"},
           422: {"description": "Validation error"},
       },
   )
   ```

- [x] `ErrorResponse` imported from `app.schemas.errors`
- [x] `chat` decorator has `summary=`, `description=`, `responses=`
- [x] `get_audit` decorator has `response_model=dict`, `summary=`, `description=`, `responses=`
- [x] `clear_session` decorator has `summary=`, `description=`, `responses=`
- [x] Existing `response_model=ChatResponse` and `status_code=204` values preserved
- [x] File is valid Python

## Acceptance Criteria

- [x] `backend/app/routers/chat.py` imports `ErrorResponse`
- [x] `get_audit` route has `response_model` set (was missing before)
- [x] All 3 routes have `summary`, `description`, and `responses` in their decorators
- [x] Running `python -c "from app.routers.chat import router; print(len(router.routes))"` from `backend/` prints `3` without error
- [x] No existing tests are broken <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/047-annotate-router-chat.uat.md`](../uat/047-annotate-router-chat.uat.md)
