# UAT: Conditional Edge Routing Integration Tests

> **Source task**: [`.docs/tasks/025-conditional-edge-routing.md`](../tasks/025-conditional-edge-routing.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Working directory is `1-multi-agent/`
- [ ] Python virtual environment is available at `1-multi-agent/.venv/`
- [ ] Package installed in editable mode: `cd 1-multi-agent && .venv/bin/pip install -e .` (or already installed)
- [ ] `1-multi-agent/tests/test_routing_integration.py` exists with 6 test functions
- [ ] No `ANTHROPIC_API_KEY` required — all tests mock the LLM layer

---

## Integration Tests

### UAT-INT-001: All routing integration tests pass

- **Components**: `hub` compiled `StateGraph`, `_route_selector` conditional edge, `_clarification_node`, `_coach_stub`, `_workout_gen_stub`, `_workout_log_stub`, `Intent` enum, `RouteDecision` model
- **Flow**: Run the full pytest suite for `test_routing_integration.py` to confirm all 6 routing paths are exercised end-to-end via the compiled hub graph with mocked LLMs.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py -v
  ```
- **Expected Result**: All 6 tests collected and pass (`6 passed` in the summary line). Exit code 0. No errors, no warnings about missing mocks or import failures.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: COACH intent (confidence ≥ 0.6) dispatches to coach branch

- **Scenario**: Hub receives `Intent.COACH` with confidence `0.9` — must route to the coach sub-agent stub, not clarification.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_coach_intent_dispatches_to_coach -v
  ```
- **Expected Result**: `PASSED`. Last message in state contains `"coach"` or `"stub"` (case-insensitive).
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: WORKOUT_GENERATE intent dispatches to workout_gen branch

- **Scenario**: Hub receives `Intent.WORKOUT_GENERATE` with confidence `0.85` — must route to the workout generator sub-agent stub.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_workout_generate_dispatches_correctly -v
  ```
- **Expected Result**: `PASSED`. Last message contains `"workout_gen"` or `"stub"` (case-insensitive).
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: WORKOUT_LOG intent dispatches to workout_log branch

- **Scenario**: Hub receives `Intent.WORKOUT_LOG` with confidence `0.92` — must route to the workout logger sub-agent stub.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_workout_log_dispatches_correctly -v
  ```
- **Expected Result**: `PASSED`. Last message contains `"workout_log"` or `"stub"` (case-insensitive).
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: FALLBACK intent routes to clarification node

- **Scenario**: Hub receives `Intent.FALLBACK` with confidence `0.7` — must route to `_clarification_node`, which produces a rephrase prompt.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_fallback_routes_to_clarification -v
  ```
- **Expected Result**: `PASSED`. Last message contains `"rephrase"`, `"sure"`, or `"help"` (case-insensitive). The clarification node response is: `"I'm not sure what you're asking…Could you rephrase your request?"`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-005: Low confidence (< 0.6) routes to clarification regardless of intent

- **Scenario**: Hub receives `Intent.COACH` but with confidence `0.4` — the `_route_selector` strict `< 0.6` threshold must override the intent and dispatch to clarification.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_low_confidence_routes_to_clarification -v
  ```
- **Expected Result**: `PASSED`. Last message contains `"rephrase"`, `"sure"`, or `"help"` (case-insensitive) — confirming clarification fired, not the coach stub.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-006: Confidence exactly 0.6 routes to the intent (strict boundary)

- **Scenario**: Hub receives `Intent.COACH` with confidence exactly `0.6`. The `_route_selector` condition is `rd.confidence < 0.6` (strict less-than), so confidence `0.6` must route to the coach stub — **not** to clarification.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/pytest tests/test_routing_integration.py::test_boundary_confidence_0_6_routes_to_intent -v
  ```
- **Expected Result**: `PASSED`. Last message contains `"coach"` or `"stub"` (case-insensitive) — confirms `0.6` is NOT treated as low-confidence.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-007: _route_selector uses strict less-than operator

- **Scenario**: Verify source code of `_route_selector` in `hub.py` uses `< 0.6` (not `<= 0.6`) for the confidence threshold.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/1-multi-agent && .venv/bin/python -c "import inspect, workout_wiz.hub as h; src = inspect.getsource(h); assert '< 0.6' in src and '<= 0.6' not in src, 'Wrong threshold operator'; print('OK: strict < 0.6 confirmed')"
  ```
- **Expected Result**: Prints `OK: strict < 0.6 confirmed`. No `AssertionError`.
- [x] Pass <!-- 2026-06-05 -->
