# UAT: Annotate Chat Schemas with OpenAPI Field Metadata

> **Source task**: [`.docs/tasks/039-annotate-schemas-chat.md`](../tasks/039-annotate-schemas-chat.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend dependencies installed (`pip install -e .` or `poetry install` from `backend/`)
- [ ] Backend server running on `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/`)
- [ ] A valid JWT bearer token stored in `$UAT_AUTH_TOKEN` (obtain via `POST /auth/jwt/login`)
- [ ] LLM API key configured in the environment (the `/chat/` endpoint invokes the LangGraph hub)

---

## API Tests

### UAT-API-001: ChatRequest JSON schema has `description` on every property

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `ChatRequest.model_json_schema()` includes a `description` key for both `message` and `session_id`. This is the primary acceptance criterion for the request schema.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "import json; from app.schemas.chat import ChatRequest; s = ChatRequest.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE'); print('Properties:', list(props.keys()))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE` and `Properties: ['message', 'session_id']` (order may vary).
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: ChatResponse JSON schema has `description` on every property

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `ChatResponse.model_json_schema()` includes a `description` key for all five fields: `session_id`, `reply`, `route`, `confidence`, `audit_log`.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "import json; from app.schemas.chat import ChatResponse; s = ChatResponse.model_json_schema(); props = s.get('properties', {}); missing = [k for k, v in props.items() if 'description' not in v]; print('Missing descriptions:', missing or 'NONE'); print('Property count:', len(props))"
  ```
- **Expected Result**: Output contains `Missing descriptions: NONE` and `Property count: 5`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: ChatRequest defaults preserved — `session_id` defaults to `None`

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that annotating `session_id` with `Field(default=None, description=..., examples=[...])` preserved the `None` default, so callers can omit it.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.chat import ChatRequest; r = ChatRequest(message='hello'); print('session_id default:', r.session_id)"
  ```
- **Expected Result**: Output is `session_id default: None`. No `ValidationError` is raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: ChatResponse defaults preserved — `route`, `confidence` default to `None`, `audit_log` defaults to `[]`

- **Endpoint**: N/A (Python import verification)
- **Description**: Verify that `route`, `confidence`, and `audit_log` defaults survive the Field annotation change.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /path/to/backend && python -c "from app.schemas.chat import ChatResponse; r = ChatResponse(session_id='s1', reply='hi'); print('route:', r.route, '| confidence:', r.confidence, '| audit_log:', r.audit_log)"
  ```
- **Expected Result**: Output is `route: None | confidence: None | audit_log: []`. No `ValidationError` is raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: POST /chat/ returns 200 with ChatResponse-shaped body

- **Endpoint**: `POST /chat/`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that the chat endpoint still returns a correctly structured `ChatResponse` after the schema annotation change. The annotation is additive and must not break request parsing or response serialization.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"What muscles does a barbell squat work?"}' | jq '{session_id, reply_length: (.reply | length), route, confidence, audit_log_count: (.audit_log | length)}'
  ```
- **Expected Result**: `200 OK`. Response body contains `session_id` (non-empty string), `reply_length` > 0, `route` (one of `"COACH"`, `"WORKOUT_GENERATE"`, `"WORKOUT_LOG"`, `"FALLBACK"`, or `null`), `confidence` (number between 0.0 and 1.0 or `null`), `audit_log_count` (integer >= 0).
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: POST /chat/ with explicit `session_id` echoes it back

- **Endpoint**: `POST /chat/`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that when a `session_id` is provided in the request, the same value is returned in the response — confirming the field is parsed correctly from the annotated schema.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Give me a push workout","session_id":"test-session-uat-039"}' | jq '{session_id, route}'
  ```
- **Expected Result**: `200 OK`. `session_id` in the response is `"test-session-uat-039"`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-007: OpenAPI `/openapi.json` includes descriptions on `ChatRequest` and `ChatResponse` component schemas

- **Endpoint**: `GET /openapi.json`
- **Description**: Verify the live OpenAPI spec includes `description` fields for all properties on both `ChatRequest` and `ChatResponse` components. This confirms Swagger UI will show the annotations end-to-end.
- **Steps**:
  1. Ensure the backend server is running
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/openapi.json' | jq '[.components.schemas | to_entries[] | select(.key | test("Chat")) | {schema: .key, missing_desc: [.value.properties // {} | to_entries[] | select(.value | has("description") | not) | .key]}] | map(select(.missing_desc | length > 0))'
  ```
- **Expected Result**: `200 OK`. The jq output is `[]` (empty array) — every property on both `ChatRequest` and `ChatResponse` has a `description` field.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: POST /chat/ without `session_id` still succeeds and returns a new session_id

- **Scenario**: Verify that `session_id` being optional (default `None`) in `ChatRequest` is preserved — omitting the field should cause the server to auto-generate one, not raise a validation error.
- **Auth-Required**: true
- **Auth-Role**: user
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"Hello coach"}' | jq '{session_id_present: (.session_id | length > 0), has_reply: (.reply | length > 0)}'
  ```
- **Expected Result**: `200 OK`. `session_id_present` is `true` (a non-empty UUID was auto-generated), `has_reply` is `true`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: POST /chat/ missing required `message` field returns 422

- **Scenario**: Verify that `message` is still required in `ChatRequest` after annotation — the `Field(description=...)` change must not accidentally make it optional.
- **Auth-Required**: true
- **Auth-Role**: user
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"session_id":"no-message"}' | jq '{status: .detail[0].type}'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response contains a validation error indicating `message` is missing (e.g. `detail[0].type` is `"missing"`).
- [x] Pass <!-- 2026-06-06 -->
