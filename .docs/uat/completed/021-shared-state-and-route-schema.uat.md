# UAT: Shared Typed State and Route Schema

> **Source task**: [`.docs/tasks/021-shared-state-and-route-schema.md`](../tasks/021-shared-state-and-route-schema.md)
> **Generated**: 2026-06-04

---

## Prerequisites

- [ ] Working directory: `1-multi-agent/` (all commands below assume this cwd)
- [ ] Python virtual environment exists at `1-multi-agent/.venv/`
- [ ] Package installed in editable mode: `.venv/bin/pip show workout-wiz` shows the package
- [ ] `1-multi-agent/src/workout_wiz/state.py` exists
- [ ] `1-multi-agent/tests/test_state.py` exists
- [ ] `1-multi-agent/tests/__init__.py` exists

---

## Unit Tests (Smoke Test Suite)

### UAT-UNIT-001: All Three Pytest Tests Pass
- **Description**: Verify that the three smoke tests in `tests/test_state.py` all pass, confirming `RouteDecision` validation, `Intent` enum values, and field types are correct.
- **Steps**:
  1. From the repo root, run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_state.py -v
  ```
- **Expected Result**: Exit code 0. Output contains `3 passed`. All three tests listed: `test_route_decision_valid PASSED`, `test_route_decision_confidence_bounds PASSED`, `test_intent_values PASSED`.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: Module Imports Without Error
- **Description**: Verify that `AgentState`, `RouteDecision`, and `Intent` can be imported from `workout_wiz.state` with no import errors (all dependencies — langgraph, pydantic, typing_extensions — are available).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import AgentState, RouteDecision, Intent; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`. No traceback or ImportError.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: RouteDecision Rejects Confidence Above 1.0
- **Description**: Verify that the `confidence` field enforces `le=1.0` — a value of `1.5` must raise a Pydantic `ValidationError`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import RouteDecision, Intent; from pydantic import ValidationError; rd = RouteDecision(intent=Intent.COACH, confidence=1.5, reasoning='too high'); print('ERROR: no exception raised')"
  ```
- **Expected Result**: Exit code 1 (unhandled exception) OR the script prints nothing and raises a `ValidationError` traceback. The `print('ERROR: ...')` line must NOT appear in stdout, confirming that instantiation failed before reaching it.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: RouteDecision Rejects Confidence Below 0.0
- **Description**: Verify that the `confidence` field enforces `ge=0.0` — a negative value must raise a Pydantic `ValidationError`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import RouteDecision, Intent; rd = RouteDecision(intent=Intent.COACH, confidence=-0.1, reasoning='too low'); print('ERROR: no exception raised')"
  ```
- **Expected Result**: Exit code 1 (unhandled exception) with a `ValidationError` traceback. The `print('ERROR: ...')` line must NOT appear in stdout.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: Intent Enum Has Exactly Four Members
- **Description**: Verify that `Intent` contains exactly COACH, WORKOUT_GENERATE, WORKOUT_LOG, and FALLBACK — no more, no fewer.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import Intent; members = {e.value for e in Intent}; expected = {'COACH','WORKOUT_GENERATE','WORKOUT_LOG','FALLBACK'}; assert members == expected, f'Got {members}'; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-005: Intent Enum Values Are Strings (JSON-serializable)
- **Description**: Verify that `Intent` inherits from `str`, making its values usable as plain strings for JSON serialization.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import Intent; import json; val = json.dumps(Intent.COACH); assert val == '\"COACH\"', f'Unexpected: {val}'; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-006: AgentState messages Field Uses add_messages Reducer
- **Description**: Verify that `AgentState.messages` is annotated with `add_messages`, which LangGraph uses to accumulate rather than overwrite message history.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import AgentState; from langgraph.graph.message import add_messages; import typing; hints = typing.get_type_hints(AgentState, include_extras=True); ann = hints['messages']; meta = typing.get_args(ann); assert add_messages in meta, f'add_messages not in metadata: {meta}'; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-007: AgentState Contains All Required Fields
- **Description**: Verify that `AgentState` declares all five required fields: `messages`, `route_decision`, `user_id`, `session_id`, `audit_log`.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import AgentState; import typing; keys = set(typing.get_type_hints(AgentState, include_extras=True).keys()); required = {'messages','route_decision','user_id','session_id','audit_log'}; assert required.issubset(keys), f'Missing: {required - keys}'; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-008: RouteDecision Accepts Boundary Confidence Values (0.0 and 1.0)
- **Description**: Verify that the exact boundary values `0.0` and `1.0` are accepted by the `confidence` field (inclusive bounds).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import RouteDecision, Intent; r1 = RouteDecision(intent=Intent.FALLBACK, confidence=0.0, reasoning='min bound'); r2 = RouteDecision(intent=Intent.COACH, confidence=1.0, reasoning='max bound'); assert r1.confidence == 0.0; assert r2.confidence == 1.0; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`. No `ValidationError` raised.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-009: RouteDecision Field Descriptions Are Present
- **Description**: Verify that all three fields on `RouteDecision` have non-empty `description` values (required for LLM grounding via `with_structured_output()`).
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "from workout_wiz.state import RouteDecision; schema = RouteDecision.model_json_schema(); props = schema['properties']; missing = [f for f in ('intent','confidence','reasoning') if not props.get(f,{}).get('description','')]; assert not missing, f'Missing descriptions: {missing}'; print('OK')"
  ```
- **Expected Result**: Exit code 0. Stdout is exactly `OK`.
- [x] Pass <!-- 2026-06-05 -->
