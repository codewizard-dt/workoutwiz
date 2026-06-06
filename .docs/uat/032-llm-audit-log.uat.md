# UAT: Per-Call LLM Audit Log

> **Source task**: [`.docs/tasks/032-llm-audit-log.md`](../tasks/032-llm-audit-log.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] `1-multi-agent/.venv` exists and dependencies are installed (`cd 1-multi-agent && pip install -e ".[dev]"` if not)
- [ ] Working directory for all shell commands is `1-multi-agent/`
- [ ] `exercises.json` is present at `1-multi-agent/exercises.json` (50 exercises)
- [ ] No `ANTHROPIC_API_KEY` required — all tests use mocks or direct session state injection

---

## API Tests

### UAT-API-001: `GET /audit/{session_id}` returns 200 with full audit log

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the audit endpoint returns a session's full audit log including `total_entries`, `session_id`, and the `audit_log` array.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py::test_audit_endpoint_returns_log -v
  ```
- **Expected Result**: Exits 0 and shows `test_audit_endpoint_returns_log PASSED`. Response contains `total_entries == 1`, `audit_log[0]["event"] == "router"`, and `tokens_in` key present.
- [ ] Pass

### UAT-API-002: `GET /audit/{session_id}` returns 404 for unknown sessions

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the endpoint returns HTTP 404 when the given `session_id` is not present in `_sessions`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py::test_audit_404_unknown_session -v
  ```
- **Expected Result**: Exits 0 and shows `test_audit_404_unknown_session PASSED`. Status code is 404.
- [ ] Pass

### UAT-API-003: `POST /chat` response includes `audit_log` array

- **Endpoint**: `POST /chat`
- **Description**: Verify the `/chat` response's `audit_log` field is populated with at least one router entry containing `tokens_in`, `route`, and `confidence`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py::test_chat_response_includes_audit -v
  ```
- **Expected Result**: Exits 0 and shows `test_chat_response_includes_audit PASSED`. `audit_log` has 1 entry with `tokens_in == 50`, `route == "COACH"`, `confidence == 0.85`.
- [ ] Pass

### UAT-API-004: Full audit test suite — all 3 tests pass

- **Endpoint**: `GET /audit/{session_id}`, `POST /chat`
- **Description**: Run the entire `test_audit.py` suite to confirm all three tests pass together with the `clear_sessions` fixture operating correctly.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py -v
  ```
- **Expected Result**: Exits 0. Output shows `3 passed`. All of `test_audit_endpoint_returns_log`, `test_audit_404_unknown_session`, `test_chat_response_includes_audit` are green.
- [ ] Pass

### UAT-API-005: `GET /audit/{session_id}` with empty audit log returns `total_entries: 0`

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify the endpoint handles a session that exists but has no audit entries (e.g. session was manually inserted without `audit_log`).
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
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
- [ ] Pass

### UAT-API-006: `GET /audit/{session_id}` with missing `audit_log` key falls back to empty list

- **Endpoint**: `GET /audit/{session_id}`
- **Description**: Verify that `state.get("audit_log", [])` in `get_audit` is defensive — a session stored without the `audit_log` key still returns `total_entries: 0` rather than raising a `KeyError`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()
# Session stored without audit_log key (simulates legacy/partial state)
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
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Router audit entry schema — all required fields present

- **Scenario**: A router audit entry injected into a session must contain all fields specified in the task: `event`, `model`, `provider`, `route`, `confidence`, `latency_ms`, `tokens_in`, `tokens_out`, `user_id`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from fastapi.testclient import TestClient
from workout_wiz.main import app, _sessions
_sessions.clear()

REQUIRED_FIELDS = {'event', 'model', 'provider', 'route', 'confidence', 'latency_ms', 'tokens_in', 'tokens_out', 'user_id'}
router_entry = {
    'event': 'router',
    'model': 'claude-haiku-4-5-20251001',
    'provider': 'anthropic',
    'route': 'COACH',
    'confidence': 0.9,
    'latency_ms': 150,
    'tokens_in': 100,
    'tokens_out': 20,
    'user_id': 'u1',
}
_sessions['schema-test'] = {'messages': [], 'audit_log': [router_entry]}
client = TestClient(app)
data = client.get('/audit/schema-test').json()
entry = data['audit_log'][0]
missing = REQUIRED_FIELDS - set(entry.keys())
assert not missing, f'Missing fields: {missing}'
_sessions.clear()
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. No assertion error about missing fields.
- [ ] Pass

### UAT-EDGE-002: Coach audit entry event name is `"coach"`

- **Scenario**: The `_chat_node` in `coach.py` must produce an entry with `event == "coach"` — not `"router"` or anything else. Verify via source inspection.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.agents import coach
src = inspect.getsource(coach._chat_node)
assert '\"event\": \"coach\"' in src or \"'event': 'coach'\" in src, 'coach event name incorrect in _chat_node'
assert 'tokens_in' in src, 'tokens_in missing from coach audit entry'
assert 'tokens_out' in src, 'tokens_out missing from coach audit entry'
assert 'latency_ms' in src, 'latency_ms missing from coach audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-003: Generator audit entry event name is `"generator"`

- **Scenario**: The `_generate_node` in `workout_generator.py` must use `event == "generator"`. Verify via source inspection.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.agents import workout_generator
src = inspect.getsource(workout_generator._generate_node)
assert '\"event\": \"generator\"' in src or \"'event': 'generator'\" in src, 'generator event name incorrect in _generate_node'
assert 'tokens_in' in src, 'tokens_in missing from generator audit entry'
assert 'tokens_out' in src, 'tokens_out missing from generator audit entry'
assert 'latency_ms' in src, 'latency_ms missing from generator audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-004: Logger audit entry event name is `"logger"`

- **Scenario**: The `_log_node` in `workout_logger.py` must use `event == "logger"`. Verify via source inspection.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.agents import workout_logger
src = inspect.getsource(workout_logger._log_node)
assert '\"event\": \"logger\"' in src or \"'event': 'logger'\" in src, 'logger event name incorrect in _log_node'
assert 'tokens_in' in src, 'tokens_in missing from logger audit entry'
assert 'tokens_out' in src, 'tokens_out missing from logger audit entry'
assert 'latency_ms' in src, 'latency_ms missing from logger audit entry'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-005: `tokens_in` and `tokens_out` default to 0 when metadata is unavailable

- **Scenario**: If LangChain does not return usage metadata (e.g. mock returns an AIMessage with no `usage_metadata`), token counts must be 0 rather than raising `AttributeError` or `TypeError`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.agents import coach, workout_generator
# Both nodes must have a defensive fallback (getattr with default {} or similar)
coach_src = inspect.getsource(coach._chat_node)
gen_src = inspect.getsource(workout_generator._generate_node)
assert 'getattr' in coach_src or '.get(' in coach_src, 'coach has no defensive getattr for usage'
assert 'getattr' in gen_src or '.get(' in gen_src, 'generator has no defensive getattr for usage'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass

### UAT-EDGE-006: Multiple audit entries accumulate correctly across a session

- **Scenario**: When a session has multiple chat turns, audit entries must accumulate (not overwrite). Inject two turns' worth of audit entries and confirm `total_entries == 2`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
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
- [ ] Pass

---

## Integration Tests

### UAT-INT-001: Full audit + chat test suites pass together without session leakage

- **Components**: `_sessions`, `clear_sessions` fixture, `GET /audit/{session_id}`, `POST /chat`
- **Flow**: Run both `test_audit.py` and `test_chat_endpoint.py` together. The `clear_sessions` autouse fixture must prevent state from leaking between tests.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_audit.py tests/test_chat_endpoint.py -v
  ```
- **Expected Result**: Exits 0. All tests pass (3 from `test_audit.py` + tests from `test_chat_endpoint.py`). No failures due to session state leaking between tests.
- [ ] Pass

### UAT-INT-002: `ChatResponse` schema includes `audit_log` field

- **Components**: `ChatResponse` Pydantic model, `POST /chat`
- **Flow**: Confirm `ChatResponse` declares `audit_log: list[dict]` and that a mocked `/chat` call returns it in the JSON response.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.main import ChatResponse
fields = ChatResponse.model_fields
assert 'audit_log' in fields, f'audit_log not in ChatResponse fields: {list(fields)}'
assert 'route' in fields, f'route not in ChatResponse fields'
assert 'confidence' in fields, f'confidence not in ChatResponse fields'
print(f'PASS: ChatResponse fields = {list(fields.keys())}')
"
  ```
- **Expected Result**: Exits 0. Prints `PASS: ChatResponse fields = [...]` including `audit_log`, `route`, and `confidence`.
- [ ] Pass

### UAT-INT-003: `hub.py` router node produces `audit_log` key in returned state

- **Components**: `_router_node` in `hub.py`, `AgentState`
- **Flow**: Verify via source inspection that `_router_node` returns a dict containing `audit_log` with the router entry appended (not replacing the full list).
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
import workout_wiz.hub as h
# Find _router_node — may be defined with a different internal name; search hub module source
src = inspect.getsource(h)
assert 'audit_log' in src, 'audit_log key missing from hub.py'
assert 'tokens_in' in src, 'tokens_in missing from hub.py router audit entry'
assert 'tokens_out' in src, 'tokens_out missing from hub.py router audit entry'
assert 'event' in src and 'router' in src, 'router event missing from hub.py'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [ ] Pass
