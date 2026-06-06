# UAT: Annotate main.py routes with OpenAPI metadata

> **Source task**: [`.docs/tasks/048-annotate-main-routes.md`](../tasks/048-annotate-main-routes.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000` (e.g. `cd backend && uvicorn app.main:app --reload`)
- [ ] A test user registered and `UAT_AUTH_TOKEN` set (required for `/auth/me` tests only):
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -F 'username=test@example.com' -F 'password=<your-password>' | jq -r '.access_token')
  ```

---

## API Tests

### UAT-API-001: GET /healthz returns 200 with {"status": "ok"}

- **Endpoint**: `GET /healthz`
- **Description**: Verify the health check route still returns the correct response after the decorator annotation was added (`tags`, `response_model=dict`, `summary`, `description`). No auth required.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/healthz' | jq '.'
  ```
- **Expected Result**: `200 OK`. Response body: `{"status": "ok"}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-002: GET /auth/me returns 200 with user id and email

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /auth/me`
- **Description**: Verify the `/auth/me` route returns the authenticated user's `id` and `email` after `response_model=dict`, `summary`, `description`, and `responses={401:...}` were added to the decorator.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set per Prerequisites.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/auth/me' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.'
  ```
- **Expected Result**: `200 OK`. Response body: `{"id": "<uuid-string>", "email": "<test-user-email>"}`. Both fields are non-empty strings.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: GET /auth/me returns 401 without auth token

- Auth-Required: false
- **Scenario**: `/auth/me` depends on `current_active_user`. The decorator now documents `responses={401: {"model": ErrorResponse, ...}}`. Omitting the Authorization header must produce 401.
- **Steps**:
  1. Call the endpoint with no Authorization header.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/auth/me' | jq '.'
  ```
- **Expected Result**: `401 Unauthorized`. Response body contains a `"detail"` key (e.g. `{"detail": "Unauthorized"}`).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-002: GET /healthz returns 200 without auth token

- **Scenario**: The `/healthz` route is explicitly described as requiring no authentication. Verify it remains public after the decorator change.
- **Steps**:
  1. Call the endpoint with no Authorization header.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/healthz' | jq '.status'
  ```
- **Expected Result**: `200 OK`. Output: `"ok"` (the `.status` field from the response body).
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: OpenAPI schema has correct metadata for /healthz

- **Components**: FastAPI app → `/openapi.json`
- **Flow**: Verify the `tags`, `summary`, and `description` added to the `/healthz` decorator appear in the generated OpenAPI spec.
- **Steps**:
  1. Run the curl command below to extract the GET /healthz operation object.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths["/healthz"].get | {summary, description, tags}'
  ```
- **Expected Result**: JSON object:
  ```json
  {
    "summary": "Health check",
    "description": "Returns {\"status\": \"ok\"} when the service is running. No authentication required.",
    "tags": ["health"]
  }
  ```
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-INT-002: OpenAPI schema has correct metadata for /auth/me

- **Components**: FastAPI app → `/openapi.json`
- **Flow**: Verify the `summary`, `description`, `response_model`, and 401 response entry added to the `/auth/me` decorator appear in the generated OpenAPI spec.
- **Steps**:
  1. Run the curl command below to extract the GET /auth/me operation object.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths["/auth/me"].get | {summary, description, tags, responses: (.responses | keys)}'
  ```
- **Expected Result**: JSON object:
  ```json
  {
    "summary": "Get current user",
    "description": "Return the authenticated user's ID and email address. Requires a valid JWT Bearer token.",
    "tags": ["auth"],
    "responses": ["200", "401"]
  }
  ```
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-INT-003: Python import introspection — both routes carry summary attributes

- **Components**: `app.main` Python module
- **Flow**: The acceptance criterion in the task requires that `routes['/healthz'].summary` and `routes['/auth/me'].summary` are accessible at import time without errors.
- **Steps**:
  1. From the `backend/` directory (where `app` is importable), run:
- **Command**:
  ```bash
  cd backend && python -c "from app.main import app; routes = {r.path: r for r in app.routes}; print(routes['/healthz'].summary, routes['/auth/me'].summary)"
  ```
- **Expected Result**: Prints without error:
  ```
  Health check Get current user
  ```
- [x] Pass <!-- 2026-06-06 -->
