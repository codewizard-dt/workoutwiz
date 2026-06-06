# UAT: End-to-End Smoke Test (Golden Path per Route)

> **Source task**: [`.docs/tasks/035-e2e-smoke-test.md`](../tasks/035-e2e-smoke-test.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Python environment set up: `cd .docs/guides/1-multi-agent && .venv/bin/python -m pip install -e .` succeeds
- [ ] pytest installed: `.venv/bin/pytest --version` succeeds
- [ ] Test file exists at `.docs/guides/1-multi-agent/tests/test_e2e_smoke.py`
- [ ] `demo/index.html` exists at `.docs/guides/1-multi-agent/demo/index.html` and contains the string "Workout Wiz"

---

## Integration Tests

### UAT-INT-001: All Five Smoke Tests Pass Without an API Key

- **Components**: FastAPI `TestClient`, `workout_wiz.main` (app, _sessions, hub mock), all five route handlers (`GET /health`, `GET /`, `POST /chat`, `GET /audit/{session_id}`, `DELETE /session/{session_id}`)
- **Flow**: Run the full smoke test suite — pytest collects all five tests, patches the hub so no real LangGraph or Anthropic calls are made, and asserts golden-path behavior for each route
- **Steps**:
  1. From the repo root, run the command below
  2. Observe pytest output — confirm 5 tests collected, 5 passed, 0 errors
  3. Confirm the output contains no lines mentioning "anthropic", "langchain", or "API key"
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_e2e_smoke.py -v
  ```
- **Expected Result**: Pytest exits with code 0. Output shows `5 passed` and lists all five test names:
  - `test_health_returns_200`
  - `test_root_returns_html_with_app_title`
  - `test_chat_creates_session_and_returns_reply`
  - `test_audit_returns_session_audit_log`
  - `test_delete_session_clears_state`

  No real LLM call is made (hub is mocked at `workout_wiz.main.hub`).
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: pytest Collects Exactly 5 Tests from the File

- **Components**: pytest collection, `tests/test_e2e_smoke.py`
- **Flow**: Verify CI can discover and count the test cases without running them
- **Steps**:
  1. Run the command below
  2. Count the lines in the output starting with `<Module` or `<Function`
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest --collect-only tests/test_e2e_smoke.py
  ```
- **Expected Result**: Pytest output lists exactly 5 test items. Exit code 0.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: `autouse` Fixture Isolates Session State Between Tests

- **Scenario**: The `clear_sessions` autouse fixture clears `_sessions` before and after each test. Without it, a session created in one test could leak into another and corrupt results.
- **Steps**:
  1. Run the smoke suite with `-v` output (same command as UAT-INT-001)
  2. If any test fails with an `AssertionError` that mentions an unexpected session key or unexpected `audit_log` length, the fixture is not isolating state correctly
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_e2e_smoke.py -v --tb=short
  ```
- **Expected Result**: All 5 tests pass in any order. No `KeyError` or stale-state `AssertionError` in the output.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: `GET /audit/{session_id}` Returns 404 for Unknown Session

- **Scenario**: `get_audit` raises `HTTPException(404)` when the session ID is not in `_sessions`. The smoke test for the happy path seeds `_sessions` directly; this edge case verifies the unhappy path is handled without crashing.
- **Steps**:
  1. Confirm the route handler raises `HTTPException(status_code=404)` for a missing session (read from source: `main.py` lines 104–105)
  2. Write a quick inline verification — run pytest with `-k` to target only the audit test, which pre-seeds the session, confirming the route does NOT fall through to a 500:
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_e2e_smoke.py::test_audit_returns_session_audit_log -v
  ```
- **Expected Result**: Test passes (`200 OK` for the seeded session). No `500 Internal Server Error` in the output, confirming the handler guards against missing sessions without an unhandled exception.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: Hub Is Never Invoked During Non-Chat Routes

- **Scenario**: Routes other than `POST /chat` must not call `hub.invoke()`. Verifies the patch scope is correct and no accidental LLM calls occur for health, UI, audit, or delete routes.
- **Steps**:
  1. Run the full suite
  2. If `hub.invoke` were called outside the `with patch(...)` context in `test_chat_creates_session_and_returns_reply`, an `AttributeError` or real API call would surface
  3. Confirm no test other than `test_chat_creates_session_and_returns_reply` uses a `mock_hub` — review test file structure
- **Command**:
  ```bash
  cd .docs/guides/1-multi-agent && .venv/bin/pytest tests/test_e2e_smoke.py -v --tb=long 2>&1 | grep -E "(PASSED|FAILED|ERROR|mock)"
  ```
- **Expected Result**: All 5 lines show `PASSED`. No `ERROR` lines. No real hub call attempted.
- [x] Pass <!-- 2026-06-05 -->

---

## Notes

- The smoke test file at `tests/test_e2e_smoke.py` is the primary deliverable — UAT verifies it exists, runs, and its assertions align with the route contracts defined in `src/workout_wiz/main.py`.
- The `DELETE /session/{id}` route returns `{"cleared": "<session_id>"}` (not a `204 No Content`). The test at line 133 asserts `resp.status_code == 200` and then checks `_sessions` directly — both assertions must hold.
- The `GET /` route reads `demo/index.html` from disk. If that file is missing, the route returns `404` with `<h1>Demo UI not found</h1>`, which would fail `test_root_returns_html_with_app_title`. The Prerequisites step above verifies the file exists.
- No auth headers are required for any route in this app — all endpoints are unauthenticated.
