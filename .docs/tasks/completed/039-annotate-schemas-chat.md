# 039 — Annotate schemas/chat.py with OpenAPI Field metadata

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md), [037-annotate-schemas-exercise](037-annotate-schemas-exercise.md), [038-annotate-schemas-workout](038-annotate-schemas-workout.md)

## Objective

Add `Field(description=..., example=...)` to every field in `ChatRequest` and `ChatResponse` in `backend/app/schemas/chat.py` so the Swagger UI shows rich documentation for all chat endpoints.

## Approach

Use Pydantic v2 `Field(description=..., example=...)`. `ChatRequest` has 2 fields and `ChatResponse` has 5 fields. Use realistic examples that demonstrate the fitness coaching context (COACH/WORKOUT_GENERATE/WORKOUT_LOG intents). Keep the `audit_log` default `[]` via `Field(default=[], description=...)`.

## Steps

### 1. Annotate ChatRequest and ChatResponse fields  <!-- agent: general-purpose -->

Edit `backend/app/schemas/chat.py`:

- Import `Field` from `pydantic` (keep existing `Any` import from `typing`).
- Annotate every field:

**ChatRequest** (lines 7–9):

| Field | Description | Example |
|-------|-------------|---------|
| `message` | The user's natural-language message to the fitness coach | `"Can you suggest a leg workout for today?"` |
| `session_id` | Optional session identifier for conversation continuity; auto-generated if omitted | `null` |

**ChatResponse** (lines 12–17):

| Field | Description | Example |
|-------|-------------|---------|
| `session_id` | Session identifier, echoed back or newly generated | `"sess_abc123"` |
| `reply` | The coach's natural-language response | `"Here is a quad-focused workout for you..."` |
| `route` | Intent the router classified this message as (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK) | `"COACH"` |
| `confidence` | Router confidence score between 0.0 and 1.0 (null if not available) | `0.95` |
| `audit_log` | Ordered list of internal agent reasoning steps for transparency | `[]` |

- Keep `audit_log`'s default via `Field(default=[], description=..., example=...)`.
- Keep `session_id`'s `None` default via `Field(default=None, description=..., example=...)`.

- [x] `Field` is imported from `pydantic` <!-- Completed: 2026-06-06 -->
- [x] All 2 fields in `ChatRequest` have `description=` and `examples=` <!-- Completed: 2026-06-06 -->
- [x] All 5 fields in `ChatResponse` have `description=` and `examples=` <!-- Completed: 2026-06-06 -->
- [x] Existing defaults are preserved <!-- Completed: 2026-06-06 -->
- [x] File is valid Python (no syntax errors) <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/schemas/chat.py` imports `Field` from `pydantic` <!-- Completed: 2026-06-06 -->
- [x] Running `python -c "from app.schemas.chat import ChatRequest, ChatResponse; import json; print(json.dumps(ChatRequest.model_json_schema(), indent=2))"` from `backend/` shows every property with a `description` key <!-- Completed: 2026-06-06 -->
- [ ] No existing tests are broken

---
**UAT**: [`.docs/uat/039-annotate-schemas-chat.uat.md`](../uat/039-annotate-schemas-chat.uat.md)
