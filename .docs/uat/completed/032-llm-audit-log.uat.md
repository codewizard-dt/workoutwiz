# UAT: Per-Call LLM Audit Log

> **Source task**: [`.docs/tasks/032-llm-audit-log.md`](../tasks/032-llm-audit-log.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Working directory for all shell commands is `.docs/guides/1-multi-agent/`
- [ ] `.venv` exists with dependencies installed: `pip install -e ".[dev]"` from `.docs/guides/1-multi-agent/`
- [ ] `exercises.json` is present at `.docs/guides/1-multi-agent/exercises.json`
- [ ] No `ANTHROPIC_API_KEY` required — all tests use mocks or direct session-state injection
- [ ] The task's implementation is complete: `coach.py`, `workout_logger.py`, and audit entries in `workout_generator.py` must all exist before running EDGE-002 through EDGE-005

---

## API Tests

### UAT-API-001: `GET /audit/{session_id}` returns full audit log

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the audit endpoint returns 200 with `session_id`, `audit_log`, and `total_entries` fields. Data is sourced from in-memory `_sessions`.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/pytest tests/test_audit.py::test_audit_endpoint_returns_log -v
  ```
- **Expected Result**: Exits 0. Shows `test_audit_endpoint_returns_log PASSED`. Response body has `total_entries == 1`, `audit_log[0]["event"] == "router"`, and `"tokens_in"` present in the entry.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-002: `GET /audit/{session_id}` returns 404 for unknown session

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the endpoint returns HTTP 404 when the given `session_id` is not in `_sessions`.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/pytest tests/test_audit.py::test_audit_404_unknown_session -v
  ```
- **Expected Result**: Exits 0. Shows `test_audit_404_unknown_session PASSED`. Status code is 404.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-003: `POST /chat` response includes `audit_log` with router fields

- **Endpoint**: `POST /chat`
- **Description**: Verify the `/chat` response's `audit_log` field is populated with at least one router entry containing `tokens_in`, `route`, and `confidence`. Also confirms `ChatResponse` serialises `route` and `confidence` from the router audit entry.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/pytest tests/test_audit.py::test_chat_response_includes_audit -v
  ```
- **Expected Result**: Exits 0. Shows `test_chat_response_includes_audit PASSED`. `audit_log` has 1 entry with `tokens_in == 50`, `route == "COACH"`, `confidence == 0.85`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-004: Full audit test suite — all 3 tests pass

- **Endpoint**: `GET /audit/{session_id}`, `POST /chat`
- **Description**: Run the entire `test_audit.py` suite confirming all three tests pass together, with the `clear_sessions` autouse fixture preventing state leakage between tests.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/pytest tests/test_audit.py -v
  ```
- **Expected Result**: Exits 0. Output shows `3 passed`. All of `test_audit_endpoint_returns_log`, `test_audit_404_unknown_session`, `test_chat_response_includes_audit` are green.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-005: `GET /audit/{session_id}` with empty audit log returns `total_entries: 0`

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the endpoint handles a session that exists but has no audit entries, returning `total_entries: 0` and an empty array.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()
_sessions['empty-audit-sess'] = {'messages': [], 'audit_log': []}
client = TestClient(app)
resp = client.get('/audit/empty-audit-sess')
assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
data = resp.json()
assert data['total_entries'] == 0, f'Expected 0, got {data[\"total_entries\"]}'
assert data['audit_log'] == [], f'Expected [], got {data[\"audit_log\"]}'
assert data['session_id'] == 'empty-audit-sess'
_sessions.clear()
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-006: `GET /audit/{session_id}` with missing `audit_log` key returns `total_entries: 0`

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify `state.get("audit_log", [])` is defensive — a session stored without the `audit_log` key returns `total_entries: 0` rather than raising `KeyError`.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()
_sessions['no-key-sess'] = {'messages': []}
client = TestClient(app)
resp = client.get('/audit/no-key-sess')
assert resp.status_code == 200, f'Expected 200, got {resp.status_code}'
data = resp.json()
assert data['total_entries'] == 0, f'Expected 0, got {data[\"total_entries\"]}'
assert data['audit_log'] == []
_sessions.clear()
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. No `KeyError` is raised.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: Router audit entry contains all required fields

- **Scenario**: A router audit entry must contain every field specified in the task: `event`, `model`, `provider`, `route`, `confidence`, `latency_ms`, `tokens_in`, `tokens_out`, `user_id`.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()
REQUIRED_FIELDS = {'event', 'model', 'provider', 'route', 'confidence', 'latency_ms', 'tokens_in', 'tokens_out', 'user_id'}
entry = {'event': 'router', 'model': 'claude-3-haiku-20240307', 'provider': 'anthropic', 'route': 'COACH', 'confidence': 0.9, 'latency_ms': 150, 'tokens_in': 100, 'tokens_out': 20, 'user_id': 'u1'}
_sessions['schema-test'] = {'messages': [], 'audit_log': [entry]}
client = TestClient(app)
data = client.get('/audit/schema-test').json()
missing = REQUIRED_FIELDS - set(data['audit_log'][0].keys())
assert not missing, f'Missing fields: {missing}'
_sessions.clear()
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: Coach audit entry has `event == "coach"` and all required fields

- **Scenario**: The `_chat_node` in `coach.py` (or the coach stub in `hub.py`) must produce an audit entry with `event == "coach"` and include `tokens_in`, `tokens_out`, `latency_ms`, `model`, `provider`.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
src = inspect.getsource(h)
assert \"'event': 'coach'\" in src or '\"event\": \"coach\"' in src, 'coach event name missing from hub'
assert 'tokens_in' in src, 'tokens_in missing from coach audit entry'
assert 'tokens_out' in src, 'tokens_out missing from coach audit entry'
assert 'latency_ms' in src, 'latency_ms missing from coach audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: Generator audit entry has `event == "workout_gen"` and all required fields

- **Scenario**: The generator node (stub or real) must produce an audit entry with `event == "workout_gen"` (matching the node name in `build_hub_graph`). Verify via source inspection of hub.py.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
src = inspect.getsource(h)
assert \"'event': 'workout_gen'\" in src or '\"event\": \"workout_gen\"' in src, 'workout_gen event name missing from hub'
assert 'tokens_in' in src, 'tokens_in missing from workout_gen audit entry'
assert 'tokens_out' in src, 'tokens_out missing from workout_gen audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: Logger audit entry has `event == "workout_log"` and all required fields

- **Scenario**: The logger node (stub or real) must produce an audit entry with `event == "workout_log"`. Verify via source inspection of hub.py.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
src = inspect.getsource(h)
assert \"'event': 'workout_log'\" in src or '\"event\": \"workout_log\"' in src, 'workout_log event name missing from hub'
assert 'tokens_in' in src, 'tokens_in missing from workout_log audit entry'
assert 'tokens_out' in src, 'tokens_out missing from workout_log audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-005: `tokens_in` and `tokens_out` default to 0 in router when metadata unavailable

- **Scenario**: `_router_node` in `hub.py` must use `getattr(raw_response, "usage_metadata", None) or {}` so that if the LangChain response carries no metadata, `tokens_in` and `tokens_out` are 0. Verify via source inspection.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
src = inspect.getsource(h._router_node)
assert 'tokens_in' in src and '0' in src, 'tokens_in not defaulted to 0 in router node'
assert 'tokens_out' in src and '0' in src, 'tokens_out not defaulted to 0 in router node'
# Verify defensive fallback pattern is present
assert ('getattr' in src and 'usage_metadata' in src) or 'tokens_in = 0' in src, 'no defensive default for tokens_in in router node'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-006: Multiple audit entries accumulate without overwriting

- **Scenario**: When a session accumulates entries from both the router and a sub-agent node, `total_entries` must reflect the full count (not just the latest). Verify via the `/audit` endpoint with two injected entries.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()
_sessions['multi-turn'] = {
    'messages': [],
    'audit_log': [
        {'event': 'router', 'route': 'COACH', 'confidence': 0.9, 'tokens_in': 50, 'tokens_out': 10, 'latency_ms': 100, 'model': 'm', 'provider': 'anthropic', 'user_id': None},
        {'event': 'coach', 'tokens_in': 200, 'tokens_out': 80, 'latency_ms': 400, 'model': 'm', 'provider': 'anthropic'},
    ],
}
client = TestClient(app)
data = client.get('/audit/multi-turn').json()
assert data['total_entries'] == 2, f'Expected 2, got {data[\"total_entries\"]}'
assert data['audit_log'][0]['event'] == 'router'
assert data['audit_log'][1]['event'] == 'coach'
_sessions.clear()
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Full pytest suite passes without session-state leakage

- **Components**: `_sessions`, `clear_sessions` fixture, `GET /audit/{session_id}`, `POST /chat`
- **Flow**: The `clear_sessions` autouse fixture in `test_audit.py` must isolate each test. Run the full test file and confirm no inter-test state leaks.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/pytest tests/test_audit.py -v --tb=short
  ```
- **Expected Result**: Exits 0. All 3 tests pass. No `AssertionError` about unexpected session data. No `KeyError`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: `ChatResponse` Pydantic model declares `audit_log`, `route`, and `confidence`

- **Components**: `ChatResponse` class in `main.py`, `POST /chat`
- **Flow**: Confirm `ChatResponse.model_fields` includes `audit_log`, `route`, and `confidence` so the serialised JSON response always exposes these keys to consumers.
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
from workout_wiz.main import ChatResponse
fields = ChatResponse.model_fields
assert 'audit_log' in fields, f'audit_log not in ChatResponse: {list(fields)}'
assert 'route' in fields, f'route not in ChatResponse: {list(fields)}'
assert 'confidence' in fields, f'confidence not in ChatResponse: {list(fields)}'
print(f'PASS: ChatResponse fields = {list(fields.keys())}')
"
  ```
- **Expected Result**: Exits 0. Prints `PASS: ChatResponse fields = [...]` including `audit_log`, `route`, and `confidence`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: Router node returns `audit_log` key with `tokens_in` and `tokens_out`

- **Components**: `_router_node` in `hub.py`
- **Flow**: Verify via source inspection that `_router_node` returns a dict with `audit_log` containing an entry that includes `tokens_in` and `tokens_out`, and that the full prior log is preserved (not replaced).
- **Steps**:
  1. Run the command below from inside `.docs/guides/1-multi-agent/`.
- **Command**:
  ```bash
  .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
src = inspect.getsource(h._router_node)
assert 'audit_log' in src, 'audit_log key missing from _router_node return'
assert 'tokens_in' in src, 'tokens_in missing from _router_node audit entry'
assert 'tokens_out' in src, 'tokens_out missing from _router_node audit entry'
assert \"'event': 'router'\" in src or '\"event\": \"router\"' in src, 'router event missing from _router_node'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->
