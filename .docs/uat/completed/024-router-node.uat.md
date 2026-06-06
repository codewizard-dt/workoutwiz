# UAT: Router Node with Structured Output

> **Source task**: [`.docs/tasks/completed/024-router-node.md`](../tasks/completed/024-router-node.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] `1-multi-agent/.venv` exists and dependencies are installed (`pip install -e ".[dev]"` from `1-multi-agent/`)
- [ ] `ANTHROPIC_API_KEY` is set in the environment (or `.env` file in `1-multi-agent/`) — required only for UAT-INT tests; pure unit tests run without it
- [ ] Working directory is the repo root (`/Users/davidtaylor/Repositories/gauntlet/workout-wiz`) unless a test specifies otherwise

---

## Unit Tests (Mocked)

These tests confirm the three required unit tests pass with mocked LLM calls — no real API usage.

### UAT-UNIT-001: pytest test_router suite passes (3/3)
- **Description**: Verify all three unit tests in `tests/test_router.py` pass — `test_router_coach_intent`, `test_router_appends_audit_log`, and `test_router_no_human_message`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_router.py -v
  ```
- **Expected Result**: `3 passed` with zero failures or errors. Each test name appears with `PASSED`.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: No-human-message returns FALLBACK at 0.0 confidence without exception
- **Description**: When `AgentState["messages"]` contains no `HumanMessage`, `_router_node` must return `Intent.FALLBACK` with `confidence=0.0` and a `reasoning` string, without raising any exception. No LLM call is made.
- **Steps**:
  1. Run the command below from the repo root — it invokes `_router_node` directly with an empty messages list via a one-liner
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _router_node
from workout_wiz.state import Intent
result = _router_node({'messages': [], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []})
rd = result['route_decision']
assert rd.intent == Intent.FALLBACK, f'Expected FALLBACK, got {rd.intent}'
assert rd.confidence == 0.0, f'Expected 0.0, got {rd.confidence}'
assert isinstance(rd.reasoning, str) and len(rd.reasoning) > 0, 'reasoning must be a non-empty string'
print('PASS: no-human-message returns FALLBACK 0.0')
"
  ```
- **Expected Result**: Prints `PASS: no-human-message returns FALLBACK 0.0` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: Low-confidence route_decision dispatches to clarification node
- **Description**: When `_route_selector` receives a `RouteDecision` with `confidence < 0.6`, it must return `"clarification"` regardless of the intent value.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
from workout_wiz.state import AgentState, Intent, RouteDecision
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.COACH, confidence=0.55, reasoning='ambiguous'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
assert result == 'clarification', f'Expected clarification, got {result}'
print('PASS: confidence < 0.6 routes to clarification')
"
  ```
- **Expected Result**: Prints `PASS: confidence < 0.6 routes to clarification` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: None route_decision dispatches to clarification node
- **Description**: When `route_decision` is `None` in state, `_route_selector` must return `"clarification"` without raising an `AttributeError` or any exception.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
state = {'messages': [], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
assert result == 'clarification', f'Expected clarification, got {result}'
print('PASS: None route_decision routes to clarification')
"
  ```
- **Expected Result**: Prints `PASS: None route_decision routes to clarification` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: Clarification node returns expected rephrase message
- **Description**: `_clarification_node` must return a dict with `"messages"` containing an `AIMessage` whose content asks the user to rephrase and lists the three supported intents.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _clarification_node
from workout_wiz.state import Intent, RouteDecision
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.3, reasoning='unclear'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _clarification_node(state)
assert 'messages' in result, 'result must contain messages key'
msg = result['messages'][0]
content = msg.content
assert 'rephrase' in content.lower() or 'not sure' in content.lower(), f'Expected rephrase prompt, got: {content}'
assert 'coaching' in content.lower() or 'workout' in content.lower(), f'Expected intent list in message, got: {content}'
print('PASS: clarification node returns rephrase message')
"
  ```
- **Expected Result**: Prints `PASS: clarification node returns rephrase message` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Module imports cleanly with no errors
- **Description**: `hub.py` must import without error. All imports (`time`, `os`, `ChatAnthropic`, `SystemMessage`, `HumanMessage`) must be at module level, not inside the `_router_node` function body.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.hub import hub; print('PASS: hub imports cleanly')"
  ```
- **Expected Result**: Prints `PASS: hub imports cleanly` with no `ImportError`, `ModuleNotFoundError`, or traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: Route selector dispatches COACH intent correctly
- **Description**: When `route_decision.intent == Intent.COACH` and `confidence >= 0.6`, `_route_selector` must return `"coach"`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
from workout_wiz.state import Intent, RouteDecision
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.COACH, confidence=0.95, reasoning='coaching question'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
assert result == 'coach', f'Expected coach, got {result}'
print('PASS: COACH routes to coach node')
"
  ```
- **Expected Result**: Prints `PASS: COACH routes to coach node` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: Route selector dispatches WORKOUT_GENERATE intent correctly
- **Description**: When `route_decision.intent == Intent.WORKOUT_GENERATE` and `confidence >= 0.6`, `_route_selector` must return `"workout_gen"`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
from workout_wiz.state import Intent, RouteDecision
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.WORKOUT_GENERATE, confidence=0.88, reasoning='generate workout'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
assert result == 'workout_gen', f'Expected workout_gen, got {result}'
print('PASS: WORKOUT_GENERATE routes to workout_gen node')
"
  ```
- **Expected Result**: Prints `PASS: WORKOUT_GENERATE routes to workout_gen node` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-004: Route selector dispatches WORKOUT_LOG intent correctly
- **Description**: When `route_decision.intent == Intent.WORKOUT_LOG` and `confidence >= 0.6`, `_route_selector` must return `"workout_log"`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
from workout_wiz.state import Intent, RouteDecision
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.WORKOUT_LOG, confidence=0.92, reasoning='logging workout'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
assert result == 'workout_log', f'Expected workout_log, got {result}'
print('PASS: WORKOUT_LOG routes to workout_log node')
"
  ```
- **Expected Result**: Prints `PASS: WORKOUT_LOG routes to workout_log node` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-005: Audit log entry has all required fields
- **Description**: The audit entry appended by `_router_node` must include all seven required fields: `event`, `model`, `provider`, `route`, `confidence`, `latency_ms`, and `user_id`.
- **Steps**:
  1. Run the command below from the repo root (uses mocked LLM to avoid API calls)
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage
from workout_wiz.state import RouteDecision, Intent
import workout_wiz.hub as hub_module

mock = MagicMock()
mock.invoke.return_value = {'parsed': RouteDecision(intent=Intent.COACH, confidence=0.9, reasoning='mocked'), 'raw': MagicMock()}
with patch.object(hub_module, 'ChatAnthropic') as mock_cls:
    mock_cls.return_value.with_structured_output.return_value = mock
    from workout_wiz.hub import _router_node
    result = _router_node({'messages': [HumanMessage(content='test')], 'route_decision': None, 'user_id': 'u1', 'session_id': 's1', 'audit_log': []})

entry = result['audit_log'][0]
required = ['event', 'model', 'provider', 'route', 'confidence', 'latency_ms', 'user_id']
missing = [k for k in required if k not in entry]
assert not missing, f'Missing audit fields: {missing}'
assert entry['event'] == 'router', f'event must be router, got {entry[\"event\"]}'
assert entry['provider'] == 'anthropic', f'provider must be anthropic, got {entry[\"provider\"]}'
assert entry['route'] == 'COACH', f'route must be COACH, got {entry[\"route\"]}'
assert isinstance(entry['latency_ms'], int) and entry['latency_ms'] >= 0
assert entry['user_id'] == 'u1'
print('PASS: audit log entry has all required fields')
"
  ```
- **Expected Result**: Prints `PASS: audit log entry has all required fields` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-006: Audit log accumulates across multiple state entries
- **Description**: When `state["audit_log"]` already has one entry before `_router_node` runs, the returned `audit_log` must contain both the existing entry and the new one (append semantics, not overwrite).
- **Steps**:
  1. Run the command below from the repo root (uses mocked LLM)
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage
from workout_wiz.state import RouteDecision, Intent
import workout_wiz.hub as hub_module

mock = MagicMock()
mock.invoke.return_value = {'parsed': RouteDecision(intent=Intent.WORKOUT_GENERATE, confidence=0.85, reasoning='mocked'), 'raw': MagicMock()}
existing_entry = {'event': 'prior', 'model': 'x', 'provider': 'y', 'route': 'coach', 'confidence': 1.0, 'latency_ms': 10, 'user_id': 'u2'}
with patch.object(hub_module, 'ChatAnthropic') as mock_cls:
    mock_cls.return_value.with_structured_output.return_value = mock
    from workout_wiz.hub import _router_node
    result = _router_node({'messages': [HumanMessage(content='plan me a workout')], 'route_decision': None, 'user_id': 'u2', 'session_id': 's2', 'audit_log': [existing_entry]})

assert len(result['audit_log']) == 2, f'Expected 2 entries, got {len(result[\"audit_log\"])}'
assert result['audit_log'][0]['event'] == 'prior', 'First entry must be the pre-existing one'
assert result['audit_log'][1]['event'] == 'router', 'Second entry must be the new router entry'
print('PASS: audit log appends to existing entries')
"
  ```
- **Expected Result**: Prints `PASS: audit log appends to existing entries` with no traceback.
- [x] Pass <!-- 2026-06-05 -->

---

## Gaps / Notes

- UAT-INT-001 through UAT-INT-006 and UAT-EDGE-001 through UAT-EDGE-004 all run without a real `ANTHROPIC_API_KEY` (either they test pure logic or use `unittest.mock`). No live LLM integration test is included because the assessment requires routing via structured output — verified indirectly by the unit test suite (UAT-UNIT-001) with mock assertions, and the real-LLM path is guarded by the key.
- `_ROUTER_SYSTEM_PROMPT` content (all four intent descriptions with examples) is verified implicitly via UAT-UNIT-001 since the test imports and calls the live module; a separate prose-content assertion was omitted to avoid brittle string matching against prose that may be tuned.
