# UAT: Annotate routers/workouts.py with OpenAPI route metadata

> **Source task**: [`.docs/tasks/completed/046-annotate-router-workouts.md`](../tasks/completed/046-annotate-router-workouts.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000` (e.g. `cd backend && uvicorn app.main:app --reload`)
- [ ] Database migrations applied and a test user registered (e.g. via `POST /auth/register`)
- [ ] `UAT_AUTH_TOKEN` environment variable set to a valid JWT for the test user:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -F 'username=test@example.com' -F 'password=<your-password>' | jq -r '.access_token')
  ```

---

## API Tests

### UAT-API-001: POST /workouts/ creates a new workout (201)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /workouts/`
- **Description**: Verify the `create_workout` route returns 201 with a `WorkoutRead` body after the decorator annotation was added. Creates data used by subsequent tests.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set per Prerequisites.
  2. Run the curl command below as-is and save the returned `id` for use in later tests.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/workouts/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"started_at":"2026-06-06T09:00:00Z","ended_at":"2026-06-06T10:00:00Z","sequences":[]}' | jq '{id, user_id, started_at, ended_at, sequences}'
  ```
- **Expected Result**: `201 Created` with a JSON object containing: `id` (UUID string), `user_id` (UUID string), `started_at` (`"2026-06-06T09:00:00Z"` or equivalent ISO), `ended_at` (`"2026-06-06T10:00:00Z"` or equivalent ISO), `sequences` (`[]`).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-002: GET /workouts/ lists the authenticated user's workouts (200)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /workouts/`
- **Description**: Verify the `list_workouts` route returns 200 and includes the workout created in UAT-API-001.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set per Prerequisites.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/workouts/' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq 'length'
  ```
- **Expected Result**: `200 OK`. Response body is a JSON array. `jq 'length'` prints an integer ≥ 1 (the workout from UAT-API-001 is present).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-003: GET /workouts/{workout_id} returns the specific workout (200)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /workouts/{workout_id}`
- **Description**: Verify the `get_workout` route returns 200 for a valid, owned workout ID.
- **Steps**:
  1. Copy the `id` returned by UAT-API-001 and substitute it for `<id-from-UAT-API-001>` below.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/workouts/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{id, started_at, ended_at}'
  ```
- **Expected Result**: `200 OK`. JSON object with `id` matching `<id-from-UAT-API-001>`, `started_at` and `ended_at` matching the values from UAT-API-001.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-004: PUT /workouts/{workout_id} updates and returns the workout (200)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PUT /workouts/{workout_id}`
- **Description**: Verify the `update_workout` route returns 200 with the updated `WorkoutRead` body.
- **Steps**:
  1. Copy the `id` returned by UAT-API-001 and substitute it for `<id-from-UAT-API-001>` below.
- **Command**:
  ```bash
  curl -sS -X PUT 'http://localhost:8000/workouts/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"started_at":"2026-06-06T09:00:00Z","ended_at":"2026-06-06T11:00:00Z","sequences":[]}' | jq '{id, ended_at}'
  ```
- **Expected Result**: `200 OK`. JSON object with `id` matching `<id-from-UAT-API-001>` and `ended_at` of `"2026-06-06T11:00:00Z"` (or equivalent ISO), confirming the update was applied.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-005: DELETE /workouts/{workout_id} deletes the workout (204)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `DELETE /workouts/{workout_id}`
- **Description**: Verify the `delete_workout` route returns 204 No Content.
- **Steps**:
  1. Copy the `id` returned by UAT-API-001 and substitute it for `<id-from-UAT-API-001>` below.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' -X DELETE 'http://localhost:8000/workouts/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: HTTP status `204`. No response body.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: GET /workouts/{workout_id} returns 404 for non-existent ID
- Auth-Required: true
- Auth-Role: user
- **Scenario**: The `get_workout` handler raises `HTTPException(404, "Workout not found")` when `workout_service.get_workout` returns `None`. The 404 entry in `responses=` documents this.
- **Steps**:
  1. Use a valid UUID that does not correspond to any workout.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/workouts/00000000-0000-0000-0000-000000000000' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.'
  ```
- **Expected Result**: `404 Not Found`. Response body: `{"detail": "Workout not found"}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-002: PUT /workouts/{workout_id} returns 404 for non-existent ID
- Auth-Required: true
- Auth-Role: user
- **Scenario**: The `update_workout` handler raises `HTTPException(404, "Workout not found")` when the target workout does not exist.
- **Steps**:
  1. Use a valid UUID that does not correspond to any workout.
- **Command**:
  ```bash
  curl -sS -X PUT 'http://localhost:8000/workouts/00000000-0000-0000-0000-000000000000' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"started_at":"2026-06-06T09:00:00Z","ended_at":null,"sequences":[]}' | jq '.'
  ```
- **Expected Result**: `404 Not Found`. Response body: `{"detail": "Workout not found"}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-003: DELETE /workouts/{workout_id} returns 404 for non-existent ID
- Auth-Required: true
- Auth-Role: user
- **Scenario**: The `delete_workout` handler raises `HTTPException(404, "Workout not found")` when the target workout does not exist.
- **Steps**:
  1. Use a valid UUID that does not correspond to any workout.
- **Command**:
  ```bash
  curl -sS -X DELETE 'http://localhost:8000/workouts/00000000-0000-0000-0000-000000000000' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.'
  ```
- **Expected Result**: `404 Not Found`. Response body: `{"detail": "Workout not found"}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-004: POST /workouts/ returns 422 when required field missing
- Auth-Required: true
- Auth-Role: user
- **Scenario**: The `create_workout` route has `responses={422: {"description": "Validation error — request body failed schema validation"}}`. Sending a body without the required `started_at` field should trigger FastAPI's 422 handler.
- **Steps**:
  1. Send a POST body that omits `started_at`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/workouts/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"sequences":[]}' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response body is a FastAPI validation error JSON with `detail` array containing a missing-field error for `started_at`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-005: GET /workouts/ returns 401 when no auth token provided
- Auth-Required: false
- **Scenario**: The `list_workouts` route depends on `current_active_user`. Omitting the Authorization header should cause fastapi-users to return 401.
- **Steps**:
  1. Call the endpoint with no Authorization header.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/workouts/' | jq '.'
  ```
- **Expected Result**: `401 Unauthorized`. Response body contains an `"detail"` key (e.g. `{"detail": "Unauthorized"}`).
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: OpenAPI schema has correct metadata for all 5 workout routes

- **Components**: FastAPI app → `/openapi.json`
- **Flow**: Verify that the `summary`, `description`, and response codes added to all 5 decorators appear in the generated OpenAPI spec.
- **Steps**:
  1. Run the curl command below to extract summary and response keys for all 5 operations.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths | to_entries | map(select(.key | startswith("/workouts"))) | map({path: .key, methods: (.value | to_entries | map({method: .key, summary: .value.summary, responses: (.value.responses | keys)}))}) '
  ```
- **Expected Result**: The output includes all 5 workout operations with the following summaries and response key sets:
  - `GET /workouts/` → summary `"List workouts"`, responses include `"200"`, `"401"`, `"422"`
  - `POST /workouts/` → summary `"Create workout"`, responses include `"201"`, `"401"`, `"422"`
  - `GET /workouts/{workout_id}` → summary `"Get workout"`, responses include `"200"`, `"401"`, `"404"`, `"422"`
  - `PUT /workouts/{workout_id}` → summary `"Update workout"`, responses include `"200"`, `"401"`, `"404"`, `"422"`
  - `DELETE /workouts/{workout_id}` → summary `"Delete workout"`, responses include `"204"`, `"401"`, `"404"`, `"422"`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-INT-002: Python import introspection — router has 5 routes
- **Components**: `app.routers.workouts` Python module
- **Flow**: The acceptance criterion in the task requires that `router.routes` contains exactly 5 items after the decorator changes.
- **Steps**:
  1. From the `backend/` directory (where `app` is importable), run:
- **Command**:
  ```bash
  cd backend && python -c "from app.routers.workouts import router; print(len(router.routes))"
  ```
- **Expected Result**: Prints `5` with no import errors or tracebacks.
- [x] Pass <!-- 2026-06-06 -->
