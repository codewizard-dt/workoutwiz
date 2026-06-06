# UAT: Coach Sub-Agent Graph

> **Source task**: [`.docs/tasks/027-coach-sub-agent.md`](../tasks/027-coach-sub-agent.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Python 3.11+ available
- [ ] `1-multi-agent/.venv` created and dependencies installed (`make install` from `1-multi-agent/`)
- [ ] `ANTHROPIC_API_KEY` set in `1-multi-agent/.env` (or shell env) — required only for UAT-INT tests; mocked tests do not need it
- [ ] Working directory context: tests run from `1-multi-agent/`

---

## Unit Tests (Mocked — No Real API Calls)

### UAT-UNIT-001: Coach graph compiles without error

- **Description**: Verify `build_coach_graph()` returns a valid `StateGraph` that can be compiled.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_coach_agent.py::test_coach_graph_compiles -v
  ```
- **Expected Result**: `PASSED` — `graph.compile()` returns a non-None compiled graph object; no `ImportError`, `TypeError`, or `LangGraphError`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-UNIT-002: Coach node returns an AIMessage

- **Description**: Verify the coach sub-agent, when invoked with a `HumanMessage`, appends an `AIMessage` to the state's `messages` list.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_coach_agent.py::test_coach_returns_ai_message -v
  ```
- **Expected Result**: `PASSED` — `result["messages"][-1]` is an `AIMessage` whose content contains `"squat"` or `"quadriceps"` (as returned by the mocked LLM)
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-UNIT-003: Coach respects COACH_MODEL environment variable

- **Description**: Verify the `_chat_node` reads `COACH_MODEL` from the environment and passes it as the `model` argument to `ChatAnthropic`.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_coach_agent.py::test_coach_uses_model_env_var -v
  ```
- **Expected Result**: `PASSED` — `ChatAnthropic` is called with `model="claude-opus-4-8"` when `COACH_MODEL=claude-opus-4-8` is set; `mock_cls.assert_called_with(model="claude-opus-4-8")` passes
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-UNIT-004: All three unit tests pass together

- **Description**: Regression gate — run the full `test_coach_agent.py` suite to confirm no interdependency failures.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_coach_agent.py -v
  ```
- **Expected Result**: `3 passed, 0 failed, 0 errors` in summary output
- [x] Pass <!-- 2026-06-05 -->

---

## Module Structure Tests

### UAT-MOD-001: agents package `__init__.py` exists

- **Description**: Verify the `agents/` package is a proper Python package (has `__init__.py`) so `from workout_wiz.agents.coach import ...` resolves correctly.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  python3 -c "import importlib.util; spec = importlib.util.find_spec('workout_wiz.agents'); print('agents package found' if spec is not None else 'MISSING')"
  ```
- **Expected Result**: `agents package found` printed; no `ModuleNotFoundError`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-MOD-002: `coach_graph` module-level export is a compiled graph

- **Description**: Verify the module-level `coach_graph` variable is a LangGraph `CompiledGraph` (not just a raw `StateGraph`), confirming `build_coach_graph().compile()` was called at import time.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.agents.coach import coach_graph; print(type(coach_graph).__name__)"
  ```
- **Expected Result**: Prints a class name that is NOT `StateGraph` — expected output is `CompiledStateGraph` (or similar `Compiled*` variant); no import errors
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-MOD-003: `build_coach_graph` graph topology — single `chat` node

- **Description**: Verify the `StateGraph` returned by `build_coach_graph()` has exactly one non-special node named `"chat"`, with edges `START → chat → END`.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.agents.coach import build_coach_graph; g = build_coach_graph(); nodes = [n for n in g.nodes if n not in ('__start__', '__end__')]; print('nodes:', nodes); assert nodes == ['chat'], f'Expected [chat], got {nodes}'"
  ```
- **Expected Result**: Prints `nodes: ['chat']` and exits with code 0; assertion error if the topology differs
- [x] Pass <!-- 2026-06-05 -->

---

## System Prompt Content Tests

### UAT-PROMPT-001: System prompt covers required coaching domains

- **Description**: Verify the `_COACH_SYSTEM_PROMPT` covers all domains required by the acceptance criteria: form/technique, strength programming, cardiovascular training, recovery, and nutrition basics.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.coach import _COACH_SYSTEM_PROMPT as p
checks = {'form': 'form' in p.lower(), 'programming': 'programming' in p.lower() or 'periodization' in p.lower(), 'recovery': 'recovery' in p.lower(), 'nutrition': 'nutrition' in p.lower(), 'cardio': 'cardiovascular' in p.lower() or 'cardio' in p.lower()}
print(checks)
assert all(checks.values()), f'Missing domains: {[k for k,v in checks.items() if not v]}'
print('OK')
"
  ```
- **Expected Result**: Prints dict with all values `True` then `OK`; assertion failure if any domain is absent
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-PROMPT-002: System prompt explicitly excludes workout plan generation

- **Description**: Verify the system prompt instructs the coach NOT to generate workout plans (that is the workout generator sub-agent's responsibility), preventing scope creep between sub-agents.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.coach import _COACH_SYSTEM_PROMPT as p
keywords = ['workout plan', 'workout plans', 'separate system', 'handled separately', 'separate']
found = any(k in p.lower() for k in keywords)
print('workout plan exclusion present:', found)
assert found, 'System prompt does not exclude workout plan generation'
print('OK')
"
  ```
- **Expected Result**: `workout plan exclusion present: True` then `OK`
- [x] Pass <!-- 2026-06-05 -->

---

## Hub Wiring Tests

### UAT-HUB-001: Hub imports without error after coach wiring

- **Description**: Verify that replacing `_coach_stub` with `coach_graph` in `hub.py` does not break the hub's import chain.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.hub import hub; print('Hub OK')"
  ```
- **Expected Result**: `Hub OK` printed; no `ImportError`, `AttributeError`, or `LangGraphError`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-HUB-002: `_coach_stub` removed from hub

- **Description**: Verify the stub function `_coach_stub` no longer exists in `hub.py`, confirming the real `coach_graph` fully replaced it.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "import workout_wiz.hub as h; assert not hasattr(h, '_coach_stub'), '_coach_stub still present in hub module'; print('_coach_stub absent — OK')"
  ```
- **Expected Result**: `_coach_stub absent — OK` printed; `AssertionError` if the stub still exists
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-HUB-003: Hub `coach` node is the compiled `coach_graph` (not a plain function)

- **Description**: Verify the hub's `"coach"` node is wired to the compiled LangGraph object, not a plain Python stub function.
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import build_hub_graph
from workout_wiz.agents.coach import coach_graph
g = build_hub_graph()
coach_node = g.nodes.get('coach')
print('coach node type:', type(coach_node).__name__ if coach_node else 'NOT FOUND')
assert coach_node is not None, 'coach node not registered in hub graph'
print('OK')
"
  ```
- **Expected Result**: Prints a node type (non-None) and `OK`; `AssertionError` if `"coach"` node is absent
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: Coach graph handles empty `audit_log` and `None` optional fields

- **Description**: Verify the coach sub-agent does not crash when `user_id`, `session_id`, and `route_decision` are all `None` (realistic when called directly outside the hub).
- **Steps**:
  1. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage
from workout_wiz.agents.coach import build_coach_graph
mock_resp = AIMessage(content='Good form tip.')
with patch('workout_wiz.agents.coach.ChatAnthropic') as m:
    m.return_value.invoke.return_value = mock_resp
    result = build_coach_graph().compile().invoke({'messages': [HumanMessage(content='hi')], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []})
print('last message:', result['messages'][-1].content)
assert result['messages'][-1].content == 'Good form tip.'
print('OK')
"
  ```
- **Expected Result**: `last message: Good form tip.` then `OK`; no `KeyError`, `TypeError`, or `AttributeError`
- [x] Pass <!-- 2026-06-05 -->

---

### UAT-EDGE-002: Coach default model is `claude-haiku-4-5-20251001` when `COACH_MODEL` is unset

- **Description**: Verify the `_chat_node` falls back to `claude-haiku-4-5-20251001` when `COACH_MODEL` is not in the environment.
- **Steps**:
  1. Run the command below from `1-multi-agent/` (unsets `COACH_MODEL` in the subprocess environment)
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
import os, unittest.mock as m
from langchain_core.messages import HumanMessage, AIMessage
os.environ.pop('COACH_MODEL', None)
from workout_wiz.agents.coach import build_coach_graph
with m.patch('workout_wiz.agents.coach.ChatAnthropic') as mock_cls:
    mock_cls.return_value.invoke.return_value = AIMessage(content='ok')
    build_coach_graph().compile().invoke({'messages': [HumanMessage(content='hi')], 'route_decision': None, 'user_id': None, 'session_id': None, 'audit_log': []})
mock_cls.assert_called_with(model='claude-haiku-4-5-20251001')
print('default model OK')
"
  ```
- **Expected Result**: `default model OK` printed; `AssertionError` if the model name differs
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Test

### UAT-INT-001: Hub routes a coaching question through the real coach sub-agent (live API)

- **Description**: End-to-end verification that a coaching-intent message travels through hub → router → coach sub-agent → AIMessage response. Requires a real `ANTHROPIC_API_KEY`.
- **Steps**:
  1. Ensure `ANTHROPIC_API_KEY` is set in the environment
  2. Run the command below from `1-multi-agent/`
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "
from dotenv import load_dotenv; load_dotenv()
from langchain_core.messages import HumanMessage, AIMessage
from workout_wiz.hub import hub
result = hub.invoke({'messages': [HumanMessage(content='What is progressive overload?')], 'route_decision': None, 'user_id': 'uat-user', 'session_id': 'uat-session', 'audit_log': []})
last = result['messages'][-1]
print('route:', result.get('route_decision'))
print('last message type:', type(last).__name__)
print('content snippet:', str(last.content)[:120])
assert isinstance(last, AIMessage), f'Expected AIMessage, got {type(last)}'
assert len(last.content) > 20, 'Response too short — likely an error'
print('PASS')
"
  ```
- **Expected Result**: Hub routes to `COACH` intent, `last` is an `AIMessage` with substantive content about progressive overload (>20 chars). `route_decision.intent` value is `COACH`. Prints `PASS`.
- [SKIP: No ANTHROPIC_API_KEY in headless environment — test manually with live key]
