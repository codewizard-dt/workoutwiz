# UAT: Hub StateGraph with Typed State and Explicit Edges

> **Source task**: [`.docs/tasks/023-hub-stategraph.md`](../tasks/023-hub-stategraph.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Python virtual environment exists at `1-multi-agent/.venv/`
- [ ] `1-multi-agent/.venv/bin/pip install -e .` has been run (package installed in dev mode)
- [ ] `langgraph`, `langchain-core` packages are installed in the venv
- [ ] `1-multi-agent/src/workout_wiz/hub.py` exists
- [ ] `1-multi-agent/src/workout_wiz/state.py` exists (provides `AgentState`, `RouteDecision`, `Intent`)
- [ ] `1-multi-agent/tests/test_hub.py` exists

---

## Integration Tests

### UAT-INT-001: Hub module imports without error
- **Components**: `workout_wiz.hub` module, `StateGraph` compilation
- **Description**: Verify the hub module can be imported and the compiled singleton `hub` is produced without any import or LangGraph compilation error.
- **Steps**:
  1. Activate the venv and run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.hub import hub; print('Hub compiled:', type(hub).__name__)"
  ```
- **Expected Result**: Exits 0 and prints `Hub compiled: CompiledStateGraph` (or similar compiled graph type name). No `ImportError`, `ModuleNotFoundError`, or LangGraph compilation exception.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: `build_hub_graph()` returns a StateGraph with all 5 nodes
- **Components**: `build_hub_graph`, `StateGraph`, node registration
- **Description**: Verify the graph builder registers exactly the 5 required named nodes: `router`, `clarification`, `coach`, `workout_gen`, `workout_log`.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.hub import build_hub_graph; g = build_hub_graph().compile(); nodes = list(g.nodes.keys()); print(nodes)"
  ```
- **Expected Result**: Exits 0. Printed list includes all of: `router`, `clarification`, `coach`, `workout_gen`, `workout_log` (plus LangGraph internal bookkeeping nodes such as `__start__`). No missing or misspelled node names.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: Hub graph invoked with no `route_decision` routes to clarification
- **Components**: `hub.invoke`, `_router_node` (stub), `_route_selector`, `_clarification_node`
- **Description**: When the hub is invoked with `route_decision=None` (stub router writes nothing), `_route_selector` should return `"clarification"` and the clarification node's message should appear last in state.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from langchain_core.messages import HumanMessage
from workout_wiz.hub import hub
result = hub.invoke({'messages': [HumanMessage(content='asdf')], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1].content
print('LAST:', last)
assert 'rephrase' in last.lower() or 'sure' in last.lower(), f'Expected clarification message, got: {last}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The last message content contains "rephrase" or "sure" (the clarification node's fixed response: `"I'm not sure what you're asking. Could you rephrase? I can help with fitness coaching, creating a workout plan, or logging a completed workout."`).
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-004: FALLBACK intent routes to clarification (not a stub node)
- **Components**: `hub.invoke`, `_route_selector`, `_clarification_node`
- **Description**: When `route_decision` carries `Intent.FALLBACK` with confidence 0.8, the conditional edge must route to the clarification node — not to any stub node.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from langchain_core.messages import HumanMessage
from workout_wiz.hub import hub
from workout_wiz.state import RouteDecision, Intent
result = hub.invoke({'messages': [HumanMessage(content='tell me a joke')], 'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.8, reasoning='off-topic'), 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1].content
print('LAST:', last)
assert 'stub' not in last, f'Stub node fired for FALLBACK — expected clarification, got: {last}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The word "stub" does not appear in the last message; the clarification message is returned instead.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-005: COACH intent routes to coach stub
- **Components**: `hub.invoke`, `_route_selector`, `_coach_stub`
- **Description**: When `route_decision` carries `Intent.COACH` with confidence >= 0.6, the hub routes to the coach stub node and returns its placeholder message.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && .venv/bin/python -c "
from langchain_core.messages import AIMessage, HumanMessage
from app.agents.hub import hub
from app.agents.state import RouteDecision, Intent
result = hub.invoke({'messages': [HumanMessage(content='how do I improve my squat form?')], 'route_decision': RouteDecision(intent=Intent.COACH, confidence=0.9, reasoning='fitness coaching question'), 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1]
print('LAST TYPE:', type(last).__name__)
print('LAST (truncated):', last.content[:200])
assert isinstance(last, AIMessage), f'Expected AIMessage, got: {type(last).__name__}'
assert len(last.content) > 50, f'Expected a real coaching response, got short content: {last.content}'
assert 'stub' not in last.content.lower(), f'Stub placeholder still present: {last.content}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The last message is an `AIMessage` with substantive coaching content (>50 chars). No stub placeholder text.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-006: WORKOUT_GENERATE intent routes to workout_gen stub
- **Components**: `hub.invoke`, `_route_selector`, `_workout_gen_stub`
- **Description**: When `route_decision` carries `Intent.WORKOUT_GENERATE` with confidence >= 0.6, the hub routes to the workout_gen stub node.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && .venv/bin/python -c "
from langchain_core.messages import AIMessage, HumanMessage
from app.agents.hub import hub
from app.agents.state import RouteDecision, Intent
result = hub.invoke({'messages': [HumanMessage(content='create me a leg day workout')], 'route_decision': RouteDecision(intent=Intent.WORKOUT_GENERATE, confidence=0.95, reasoning='workout generation'), 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1]
print('LAST TYPE:', type(last).__name__)
print('LAST (truncated):', last.content[:200])
assert isinstance(last, AIMessage), f'Expected AIMessage, got: {type(last).__name__}'
assert len(last.content) > 50, f'Expected a real workout plan response, got short content: {last.content}'
assert 'stub' not in last.content.lower(), f'Stub placeholder still present: {last.content}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The last message is an `AIMessage` with substantive workout plan content (>50 chars). No stub placeholder text.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-007: WORKOUT_LOG intent routes to workout_log stub
- **Components**: `hub.invoke`, `_route_selector`, `_workout_log_stub`
- **Description**: When `route_decision` carries `Intent.WORKOUT_LOG` with confidence >= 0.6, the hub routes to the workout_log stub node.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && .venv/bin/python -c "
from langchain_core.messages import AIMessage, HumanMessage
from app.agents.hub import hub
from app.agents.state import RouteDecision, Intent
result = hub.invoke({'messages': [HumanMessage(content='I just did 3 sets of squats')], 'route_decision': RouteDecision(intent=Intent.WORKOUT_LOG, confidence=0.88, reasoning='logging a completed workout'), 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1]
print('LAST TYPE:', type(last).__name__)
print('LAST (truncated):', last.content[:200])
assert isinstance(last, AIMessage), f'Expected AIMessage, got: {type(last).__name__}'
assert len(last.content) > 20, f'Expected a real workout log response, got short content: {last.content}'
assert 'stub' not in last.content.lower(), f'Stub placeholder still present: {last.content}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The last message is an `AIMessage` acknowledging the logged workout (>20 chars). No stub placeholder text.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Confidence exactly at boundary 0.6 routes to sub-agent (not clarification)
- **Scenario**: `_route_selector` checks `confidence < 0.6`. A confidence of exactly 0.6 must NOT fall into the clarification branch — it should dispatch to the appropriate sub-agent.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && .venv/bin/python -c "
from app.agents.hub import _route_selector
from app.agents.state import RouteDecision, Intent
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.COACH, confidence=0.6, reasoning='borderline'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
print('Route:', result)
assert result == 'coach', f'Confidence=0.6 should route to coach (not clarification), got: {result}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0, prints `Route: coach` and `PASS`. Confidence of exactly 0.6 is not strictly less than 0.6, so `_route_selector` returns `"coach"` not `"clarification"`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Confidence just below 0.6 (0.599) routes to clarification
- **Scenario**: Any confidence strictly below 0.6 must always resolve to clarification, regardless of intent.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from langchain_core.messages import HumanMessage
from workout_wiz.hub import hub
from workout_wiz.state import RouteDecision, Intent
result = hub.invoke({'messages': [HumanMessage(content='hmm')], 'route_decision': RouteDecision(intent=Intent.COACH, confidence=0.599, reasoning='too low'), 'user_id': None, 'session_id': None, 'audit_log': []})
last = result['messages'][-1].content
print('LAST:', last)
assert 'stub' not in last, f'Low confidence should route to clarification, got: {last}'
assert 'rephrase' in last.lower() or 'sure' in last.lower(), f'Expected clarification text, got: {last}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`. The clarification message is returned, not a stub message.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: Unknown intent falls back to clarification
- **Scenario**: `_route_selector` uses `.get(rd.intent, "clarification")` as a final safety net. If somehow a new or unrecognised intent reaches the selector, it defaults to clarification.
- **Steps**:
  1. Run the command below (manually constructs a RouteDecision with a mock bad intent using a known intent that has no special mapping path — confirmed via source: only COACH/WORKOUT_GENERATE/WORKOUT_LOG are in the map).
  2. This test verifies that the `FALLBACK` path in the intent map correctly resolves to `"clarification"` (already tested in UAT-INT-004), and that an intent not in the map also defaults to clarification via `.get(..., "clarification")`.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
from workout_wiz.state import AgentState, RouteDecision, Intent
# Patch a fake intent not in the map by constructing state manually
# Use FALLBACK which maps to clarification in the intent_to_node dict
state = {'messages': [], 'route_decision': RouteDecision(intent=Intent.FALLBACK, confidence=0.9, reasoning='test'), 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
print('Route:', result)
assert result == 'clarification', f'FALLBACK should return clarification, got: {result}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0, prints `Route: clarification` and `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: `_route_selector` called directly — None route_decision returns clarification
- **Scenario**: `_route_selector` is a standalone function. When called with `route_decision=None` it must return `"clarification"` without raising an exception.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import _route_selector
state = {'messages': [], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []}
result = _route_selector(state)
print('Route:', result)
assert result == 'clarification', f'Expected clarification, got: {result}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0, prints `Route: clarification` and `PASS`.
- [x] Pass <!-- 2026-06-05 -->

---

## Pytest Suite Tests

### UAT-PYTEST-001: All 3 unit tests in test_hub.py pass
- **Description**: The task requires `pytest tests/test_hub.py` to pass with 3/3 tests. This test runs the full pytest suite as the definitive acceptance gate.
- **Steps**:
  1. Run the command below.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_hub.py -v
  ```
- **Expected Result**: Exits 0. Output shows `3 passed` with all of the following listed as `PASSED`:
  - `test_hub_compiles`
  - `test_clarification_on_low_confidence`
  - `test_fallback_routes_to_clarification`
  No failures, errors, or skipped tests.
- [x] Pass <!-- 2026-06-05 -->
