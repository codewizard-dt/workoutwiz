# UAT: POST /chat Endpoint with Session Support

> **Source task**: [`.docs/tasks/completed/030-chat-endpoint.md`](../tasks/completed/030-chat-endpoint.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Python virtual environment activated: `cd .docs/guides/1-multi-agent && source .venv/bin/activate`
- [ ] Server running: `uvicorn workout_wiz.main:app --port 8000` (or `--port 18001` to match task Step 3)
- [ ] `ANTHROPIC_API_KEY` set in environment (required by the hub's router node for live integration tests)
- [ ] For mocked unit tests only, no API key needed: `pytest tests/test_chat_endpoint.py -v`

---

## API Tests

### UAT-API-001: Health Check Returns OK
- **Endpoint**: `GET /health`
- **Description**: Verify the health endpoint returns `{"status": "ok"}` — confirms the server started without import errors.
- **Steps**:
  1. Ensure the server is running (see Prerequisites).
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/health'
  ```
- **Expected Result**: `200 OK` with body `{"status":"ok"}`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-002: POST /chat Returns Session ID and Reply
- **Endpoint**: `POST /chat`
- **Description**: Verify a new chat message returns a valid `session_id` (auto-generated UUID), a non-empty `reply`, and `route`/`confidence`/`audit_log` fields.
- **Steps**:
  1. Run the curl command below as-is. A real LLM call will be made to Anthropic.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"What muscles does a squat work?"}'
  ```
- **Expected Result**: `200 OK` with body shape:
  ```json
  {
    "session_id": "<uuid>",
    "reply": "<non-empty string from the coach sub-agent>",
    "route": "COACH",
    "confidence": <float between 0.0 and 1.0>,
    "audit_log": [{"event": "router", "route": "COACH", "confidence": <float>, "model": "<string>", "provider": "anthropic", "latency_ms": <int>, "user_id": "anonymous", "tokens_in": <int>, "tokens_out": <int>}]
  }
  ```
  Copy the `session_id` value for use in UAT-API-003 and UAT-API-005.
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-003: POST /chat Reuses Existing Session (Multi-Turn)
- **Endpoint**: `POST /chat`
- **Description**: Verify that sending a second message with the same `session_id` accumulates conversation history — the hub is invoked with the prior messages already present in state.
- **Steps**:
  1. Substitute `<session-id-from-UAT-API-002>` with the actual `session_id` returned in UAT-API-002.
  2. Run the curl command below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"Can you suggest a full leg day workout?","session_id":"<session-id-from-UAT-API-002>"}'
  ```
- **Expected Result**: `200 OK` with `"session_id"` equal to `<session-id-from-UAT-API-002>` (not a new UUID). The `reply` is a non-empty string. The `audit_log` contains at least one entry with `"event": "router"`.
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-004: POST /chat with X-User-ID Header
- **Endpoint**: `POST /chat`
- **Description**: Verify the `X-User-ID` header flows through to `audit_log[*].user_id` in the response. The audit log router entry must carry the supplied user ID.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -H 'X-User-ID: user-abc-123' -d '{"message":"Give me a quick warm-up routine."}'
  ```
- **Expected Result**: `200 OK`. The `audit_log` array contains at least one entry where `"event": "router"` and `"user_id": "user-abc-123"`.
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-005: DELETE /session Clears Existing Session
- **Endpoint**: `DELETE /session/{session_id}`
- **Description**: Verify that deleting a session removes it from the in-memory store. Subsequent requests with the same `session_id` will start a fresh session (no accumulated history).
- **Steps**:
  1. Substitute `<session-id-from-UAT-API-002>` with the actual `session_id` from UAT-API-002.
  2. Run the curl command below.
- **Command**:
  ```bash
  curl -sS -X DELETE 'http://localhost:8000/session/<session-id-from-UAT-API-002>'
  ```
- **Expected Result**: `200 OK` with body `{"cleared":"<session-id-from-UAT-API-002>"}`.
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-API-006: DELETE /session on Non-Existent Session Returns 200
- **Endpoint**: `DELETE /session/{session_id}`
- **Description**: Verify that deleting a session ID that does not exist returns `200 OK` gracefully (no exception — the implementation uses `dict.pop(..., None)`).
- **Steps**:
  1. Run the curl command below as-is with a fabricated session ID.
- **Command**:
  ```bash
  curl -sS -X DELETE 'http://localhost:8000/session/does-not-exist-session-id'
  ```
- **Expected Result**: `200 OK` with body `{"cleared":"does-not-exist-session-id"}`.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: POST /chat Without session_id Generates a New UUID
- **Scenario**: When `session_id` is omitted from the request body, the endpoint must generate and return a fresh UUID as `session_id` (not `null` or an empty string).
- **Steps**:
  1. Run the curl command below — note no `session_id` field in the payload.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"Hello"}'
  ```
- **Expected Result**: `200 OK` with `session_id` set to a non-empty UUID string (format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`). Running the command a second time with no `session_id` produces a *different* UUID.
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-EDGE-002: POST /chat With Missing message Field Returns 422
- **Scenario**: The `message` field is required by `ChatRequest`. Omitting it must result in a validation error.
- **Steps**:
  1. Run the curl command below — the payload deliberately omits `message`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{}'
  ```
- **Expected Result**: `422 Unprocessable Entity` with a JSON body containing a `"detail"` array describing the missing `message` field (standard FastAPI/Pydantic validation error shape).
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-EDGE-003: POST /chat Default User ID When X-User-ID Header Omitted
- **Scenario**: When the `X-User-ID` header is not sent, the state must default to `"anonymous"` per the handler's `Header(default="anonymous")`.
- **Steps**:
  1. Run the curl command below — no `X-User-ID` header.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat' -H 'Content-Type: application/json' -d '{"message":"How do I improve my bench press?"}'
  ```
- **Expected Result**: `200 OK`. The `audit_log` router entry has `"user_id": "anonymous"`.
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Unit Test Suite Passes (Mocked Hub)
- **Components**: `workout_wiz.main` (FastAPI app), `pytest`, `unittest.mock`
- **Flow**: Run all 5 unit tests in `tests/test_chat_endpoint.py` with the hub mocked — no real LLM calls. Covers: health check, session ID returned, session reuse, X-User-ID header propagation, and session deletion.
- **Steps**:
  1. Navigate to the assessment directory and activate the virtual environment.
  2. Run the command below.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_chat_endpoint.py -v
  ```
- **Expected Result**: All 5 tests pass (`5 passed`). No failures, no errors. Output includes:
  - `test_health PASSED`
  - `test_chat_returns_session_id PASSED`
  - `test_chat_reuses_session PASSED`
  - `test_chat_user_id_header PASSED`
  - `test_clear_session PASSED`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-INT-002: Server Starts Without Import Errors
- **Components**: `workout_wiz.main`, `uvicorn`, all sub-agent and hub imports
- **Flow**: Start the uvicorn server, wait for it to be ready, hit `/health`, confirm the response — proving the module import chain (hub → agents → state → main) has no errors.
- **Steps**:
  1. Navigate to the assessment directory and activate the virtual environment.
  2. Run the command below. The server will start, the health check will print, and uvicorn will be terminated after 5 seconds.
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && timeout 5 python -c "import uvicorn, threading, time, httpx; run=lambda: uvicorn.run('workout_wiz.main:app', port=18001, log_level='error'); t=threading.Thread(target=run, daemon=True); t.start(); time.sleep(2); r=httpx.get('http://localhost:18001/health'); print('Health:', r.json())" || true
  ```
- **Expected Result**: Output contains `Health: {'status': 'ok'}`. No `ImportError`, `ModuleNotFoundError`, or traceback before the health line.
- [x] Pass <!-- 2026-06-05 -->
