# UAT: Annotate routers/exercises.py with OpenAPI route metadata

> **Source task**: [`.docs/tasks/completed/045-annotate-router-exercises.md`](../tasks/completed/045-annotate-router-exercises.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000` (e.g. `cd backend && uvicorn app.main:app --reload`)
- [ ] Database seeded with exercises (Alembic migrations + seed script applied)
- [ ] Python environment active with `app` package importable from `backend/`

---

## API Tests

### UAT-API-001: GET /exercises returns 200 with array of ExerciseRead objects

- **Endpoint**: `GET /exercises/`
- **Description**: Verify the route still returns a valid list of exercises after the decorator metadata was added (smoke test that the annotation change did not break the handler).
- **Steps**:
  1. Ensure the backend is running and the database is seeded.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/' | jq '.[0] | {id, name, category, muscle_groups, equipment_required, movement_patterns, is_reps, is_duration, supports_weight, is_bilateral, bilateral_pair_id, priority_tier}'
  ```
- **Expected Result**: `200 OK`. The response body is a JSON array of at least one object. The first element contains all ExerciseRead fields: `id` (UUID string), `name` (string), `category` (string), `muscle_groups` (array of strings), `equipment_required` (array of strings), `movement_patterns` (array of strings), `is_reps` (bool), `is_duration` (bool), `supports_weight` (bool), `is_bilateral` (bool), `bilateral_pair_id` (UUID string or null), `priority_tier` (integer 1–3).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-002: GET /exercises?name= filters by exercise name (case-insensitive)

- **Endpoint**: `GET /exercises/?name=squat`
- **Description**: Verify name filtering works correctly with the annotated route.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/?name=squat' | jq '[.[] | .name]'
  ```
- **Expected Result**: `200 OK`. Response is a JSON array where every element's `name` field contains "squat" (case-insensitive). If no exercises match, returns an empty array `[]`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-003: GET /exercises?priority_tier=2 filters by priority tier

- **Endpoint**: `GET /exercises/?priority_tier=2`
- **Description**: Verify priority_tier filtering returns only tier-2 exercises. Results should be ordered by `priority_tier` ascending then `name`. (All 50 seed exercises have priority_tier=2; UAT updated to match actual seed data.)
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/?priority_tier=2' | jq '[.[] | {name, priority_tier}]'
  ```
- **Expected Result**: `200 OK`. Every object in the array has `priority_tier == 2`. Array is non-empty (all 50 seed exercises have priority_tier=2). Objects are ordered alphabetically by `name` within the tier.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-004: GET /exercises?priority_tier=0 returns 422 (out-of-range)

- **Endpoint**: `GET /exercises/?priority_tier=0`
- **Description**: Verify the documented 422 response fires when `priority_tier` is below the allowed minimum (ge=1). This validates that the `422` entry in the `responses=` dict correctly describes real behaviour.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/?priority_tier=0' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response body is a FastAPI validation error JSON, e.g. `{"detail": [{"type": "greater_than_equal", "loc": ["query", "priority_tier"], ...}]}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-005: GET /exercises?priority_tier=4 returns 422 (out-of-range)

- **Endpoint**: `GET /exercises/?priority_tier=4`
- **Description**: Verify the 422 response also fires when `priority_tier` exceeds the allowed maximum (le=3).
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/exercises/?priority_tier=4' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response body is a FastAPI validation error JSON containing a constraint violation for `priority_tier`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: OpenAPI schema includes summary and description for GET /exercises

- **Scenario**: The `summary` and `description` fields added to the decorator must appear in the generated OpenAPI spec served at `/openapi.json`.
- **Steps**:
  1. Run the curl command below to extract the operation object for `GET /exercises/`.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths["/exercises/"].get | {summary, description}'
  ```
- **Expected Result**: JSON object:
  ```json
  {
    "summary": "List exercises",
    "description": "Return all exercises, optionally filtered by name, muscle group, equipment, or priority tier. Results are ordered by priority_tier ascending."
  }
  ```
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-002: OpenAPI schema documents 401 and 422 responses for GET /exercises

- **Scenario**: The `responses={401: ..., 422: ...}` dict on the decorator must appear in the generated OpenAPI spec.
- **Steps**:
  1. Run the curl command below to inspect the documented responses.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths["/exercises/"].get.responses | keys'
  ```
- **Expected Result**: The keys array includes `"200"`, `"401"`, and `"422"` (FastAPI serialises status codes as strings in OpenAPI JSON).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-003: 401 response in OpenAPI schema references ErrorResponse model

- **Scenario**: The `401` entry in `responses=` uses `"model": ErrorResponse`, which should cause the OpenAPI spec to reference the `ErrorResponse` schema component.
- **Steps**:
  1. Run the curl command below to inspect the 401 response schema reference.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths["/exercises/"].get.responses["401"]'
  ```
- **Expected Result**: The 401 response object has a `description` of `"Not authenticated — valid JWT Bearer token required"` and a `content` block whose schema `$ref` points to the `ErrorResponse` component (e.g. `"$ref": "#/components/schemas/ErrorResponse"`).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-004: Python import introspection — route carries summary and description

- **Scenario**: The acceptance criterion in the task requires that the `summary` and `description` attributes are accessible on the route object at import time (no runtime errors).
- **Steps**:
  1. In the `backend/` directory (where the `app` package is importable), run:
- **Command**:
  ```bash
  cd backend && python -c "from app.routers.exercises import router; r = [r for r in router.routes if r.path == '/exercises/'][0]; print(r.summary, '|', r.description)"
  ```
  > **Note**: Path is `/exercises/` (not `/`) because the router is mounted with prefix; command updated accordingly.
- **Expected Result**: Prints without error:
  ```
  List exercises | Return all exercises, optionally filtered by name, muscle group, equipment, or priority tier. Results are ordered by priority_tier ascending.
  ```
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Swagger UI renders exercises endpoint with correct metadata

- **Components**: FastAPI app → `/docs` Swagger UI → `GET /exercises/` operation
- **Flow**: Open the Swagger UI, navigate to the exercises section, and confirm the human-readable metadata is displayed.
- **Steps**:
  1. Open a browser and navigate to `http://localhost:8000/docs`.
  2. Locate the **exercises** section (tagged "exercises").
  3. Expand the `GET /exercises/` operation.
  4. Observe the summary line and description text.
  5. Expand the **Responses** section and verify 200, 401, and 422 entries are listed.
- **Expected Result**:
  - The operation title reads **"List exercises"** (the `summary`).
  - The description reads: *"Return all exercises, optionally filtered by name, muscle group, equipment, or priority tier. Results are ordered by priority_tier ascending."*
  - The Responses table shows entries for **200**, **401** (with description "Not authenticated — valid JWT Bearer token required"), and **422** (with description "Validation error — one or more query parameters failed type or constraint checks").
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->
