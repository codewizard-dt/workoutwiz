# UAT: Annotate routers/chat.py with OpenAPI route metadata

> **Source task**: [`.docs/tasks/047-annotate-router-chat.md`](../tasks/047-annotate-router-chat.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000` (e.g. `cd backend && uvicorn app.main:app --reload`)
- [ ] `OPENAI_API_KEY` (or configured LLM provider key) is set in the environment so the hub agent can respond
- [ ] A test user registered and `UAT_AUTH_TOKEN` set:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -F 'username=test@example.com' -F 'password=<your-password>' | jq -r '.access_token')
  ```

---

## API Tests

### UAT-API-001: POST /chat/ returns 200 with ChatResponse (happy path)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /chat/`
- **Description**: Verify the `chat` route returns 200 with a complete `ChatResponse` body after the decorator annotation was added. Saves the `session_id` for subsequent audit and clear tests.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set per Prerequisites.
  2. Run the curl command below. Note the returned `session_id` for use in UAT-API-002 and UAT-API-003.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Hello coach, what muscles should I train today?"}' | jq '{session_id, reply, route, confidence}'
  ```
- **Expected Result**: `200 OK`. JSON object with:
  - `session_id`: a non-empty string (UUID or similar)
  - `reply`: a non-empty string (the coach's response)
  - `route`: one of `"COACH"`, `"WORKOUT_GENERATE"`, `"WORKOUT_LOG"`, or `"FALLBACK"` (or `null`)
  - `confidence`: a float 0.0–1.0 or `null`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-002: GET /chat/audit/{session_id} returns the audit log (200)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `GET /chat/audit/{session_id}`
- **Description**: Verify the `get_audit` route returns 200 with `{session_id, audit_log, total_entries}` for a session that was created in UAT-API-001. This route had no `response_model` before the task — the addition of `response_model=dict` is what this tests.
- **Steps**:
  1. Copy the `session_id` returned by UAT-API-001 and substitute it for `<session_id-from-UAT-API-001>` below.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/chat/audit/<session_id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{session_id, total_entries}'
  ```
- **Expected Result**: `200 OK`. JSON object with:
  - `session_id`: matches `<session_id-from-UAT-API-001>`
  - `audit_log`: a JSON array (may be empty `[]` or contain agent event objects)
  - `total_entries`: integer equal to the length of `audit_log`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-API-003: DELETE /chat/session/{session_id} clears the session (204)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `DELETE /chat/session/{session_id}`
- **Description**: Verify the `clear_session` route returns 204 No Content for an existing session.
- **Steps**:
  1. Copy the `session_id` returned by UAT-API-001 and substitute it for `<session_id-from-UAT-API-001>` below.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' -X DELETE 'http://localhost:8000/chat/session/<session_id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: HTTP status `204`. No response body.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: GET /chat/audit/{session_id} returns 404 for unknown session
- Auth-Required: true
- Auth-Role: user
- **Scenario**: `get_audit` raises `HTTPException(404, detail=f"Session '{session_id}' not found")` when the session ID is not in the in-memory `_sessions` store. The 404 entry in `responses=` documents this.
- **Steps**:
  1. Use a session ID that was never created (or was cleared by UAT-API-003).
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/chat/audit/nonexistent-session-id' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.'
  ```
- **Expected Result**: `404 Not Found`. Response body: `{"detail": "Session 'nonexistent-session-id' not found"}`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-002: GET /chat/audit/{session_id} returns 404 after session was cleared
- Auth-Required: true
- Auth-Role: user
- **Scenario**: After `DELETE /chat/session/{session_id}` removes the session from `_sessions`, a subsequent `GET /chat/audit/{session_id}` should return 404.
- **Steps**:
  1. First run UAT-API-001 to create a session, note the `session_id`.
  2. Run UAT-API-003 to clear it.
  3. Then run the command below substituting that same `session_id`.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/chat/audit/<session_id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.detail'
  ```
- **Expected Result**: `404 Not Found`. The `.detail` field equals `"Session '<session_id-from-UAT-API-001>' not found"`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-003: POST /chat/ returns 422 when message field is missing
- Auth-Required: true
- Auth-Role: user
- **Scenario**: The `chat` route validates the request body with `ChatRequest`. Omitting the required `message` field must produce 422 per the `responses=` annotation.
- **Steps**:
  1. Send a POST body that omits `message`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{}' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response body is a FastAPI validation error JSON with `detail` array containing a missing-field error for `message`.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-004: POST /chat/ returns 401 when no auth token provided
- Auth-Required: false
- **Scenario**: The `chat` route depends on `current_active_user`. Omitting the Authorization header should produce 401.
- **Steps**:
  1. Call the endpoint with no Authorization header.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -d '{"message":"hello"}' | jq '.'
  ```
- **Expected Result**: `401 Unauthorized`. Response body contains a `"detail"` key (e.g. `{"detail": "Unauthorized"}`).
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-EDGE-005: DELETE /chat/session/{session_id} silently succeeds for unknown session (204)
- Auth-Required: true
- Auth-Role: user
- **Scenario**: `clear_session` uses `_sessions.pop(session_id, None)` — it silently no-ops when the session does not exist, returning 204 rather than 404. The task does NOT document a 404 for DELETE; this verifies the actual implementation behaviour matches the decorator.
- **Steps**:
  1. Call DELETE with a session ID that does not exist.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' -X DELETE 'http://localhost:8000/chat/session/does-not-exist' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: HTTP status `204`. No body (the route silently ignores the missing session).
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: OpenAPI schema has correct metadata for all 3 chat routes

- **Components**: FastAPI app → `/openapi.json`
- **Flow**: Verify that the `summary`, `description`, `response_model`, and response codes added to all 3 decorators appear in the generated OpenAPI spec.
- **Steps**:
  1. Run the curl command below to extract operation metadata for all chat paths.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '.paths | to_entries | map(select(.key | startswith("/chat"))) | map({path: .key, methods: (.value | to_entries | map({method: .key, summary: .value.summary, responses: (.value.responses | keys)}))})'
  ```
- **Expected Result**: Three operations present with:
  - `POST /chat/` → summary `"Send a chat message"`, responses include `"200"`, `"401"`, `"422"`
  - `GET /chat/audit/{session_id}` → summary `"Get session audit log"`, responses include `"200"`, `"401"`, `"404"`, `"422"`
  - `DELETE /chat/session/{session_id}` → summary `"Clear a session"`, responses include `"204"`, `"401"`, `"422"`
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-INT-002: POST /chat/ session continuity — second message uses same session

- Auth-Required: true
- Auth-Role: user
- **Components**: `POST /chat/` → `_sessions` store → `hub.invoke()` → `POST /chat/` again
- **Flow**: Verify that sending a `session_id` returned from a first call continues the conversation in the same session (session history is preserved per the `description=` text).
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set per Prerequisites.
  2. Run UAT-API-001 to obtain a `session_id`.
  3. Run the command below substituting that `session_id`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Thanks, what about upper body?","session_id":"<session_id-from-UAT-API-001>"}' | jq '{session_id, route}'
  ```
- **Expected Result**: `200 OK`. The returned `session_id` matches `<session_id-from-UAT-API-001>` (same session, not a new UUID), confirming session continuity.
- [x] Pass <!-- 2026-06-06 -->

---

### UAT-INT-003: Python import introspection — router has 3 routes
- **Components**: `app.routers.chat` Python module
- **Flow**: The acceptance criterion in the task requires that `router.routes` contains exactly 3 items after the decorator changes.
- **Steps**:
  1. From the `backend/` directory (where `app` is importable), run:
- **Command**:
  ```bash
  cd backend && python -c "from app.routers.chat import router; print(len(router.routes))"
  ```
- **Expected Result**: Prints `3` with no import errors or tracebacks.
- [x] Pass <!-- 2026-06-06 -->
