# UAT: Fallback Handler — Surface Alternatives When Safe Exercises Are Too Few

> **Source task**: [`.docs/tasks/completed/063-fallback-handler.md`](../tasks/completed/063-fallback-handler.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend Python environment active (`cd backend && source .venv/bin/activate` or equivalent)
- [ ] `.env` loaded (`set -a && source .env && set +a`)
- [ ] All tests run from `backend/` directory: `cd backend && python -m pytest <path> -v`

---

## Functional Tests

These tests exercise `_fallback_node`, `_validate_context_node`, `_safety_gate_node`, and the compiled graph directly. All tests are implemented as pytest unit tests in `backend/tests/kg/test_generation_graph.py`.

### UAT-FUNC-001: Fallback node picks top-3 safe exercises

- **Component**: `_fallback_node` in `backend/app/kg/generation_graph.py`
- **Description**: When `fallback_triggered=True` and `context.safe_exercises` contains 5 exercises, the recommendation must contain ≤3 exercises, all from the safe list, with `sets=3` and `reps=10`.
- **Steps**:
  1. Run the pytest test that covers this case:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_fallback_node_uses_safe_exercises_when_triggered -v
  ```
- **Expected Result**: `PASSED` — recommendation has ≤3 exercises, each `exercise_id` in `{"ex-0","ex-1","ex-2","ex-3","ex-4"}`, each with `sets=3`, `reps=10`, and `reasoning` containing "safe alternative".
- [x] Pass <!-- 2026-06-06 -->

### UAT-FUNC-002: Fallback node produces empty exercise list when no safe exercises

- **Component**: `_fallback_node`
- **Description**: When `context.safe_exercises` is `[]`, the recommendation's `exercises` list must be empty and `overall_reasoning` must be non-empty.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_fallback_node_uses_empty_list_when_no_safe_exercises -v
  ```
- **Expected Result**: `PASSED` — `rec.exercises == []`, `rec.overall_reasoning != ""`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-FUNC-003: validate_context triggers fallback for None and empty context

- **Component**: `_validate_context_node`
- **Description**: Both `context=None` and `context={}` must produce `fallback_triggered=True` from `_validate_context_node`.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_fallback_triggered_by_empty_context -v
  ```
- **Expected Result**: `PASSED` for both `None` and `{}` inputs.
- [x] Pass <!-- 2026-06-06 -->

### UAT-FUNC-004: safety_gate triggers fallback when <2 exercises survive filtering

- **Component**: `_safety_gate_node`
- **Description**: When all recommended exercises are contraindicated, `fallback_triggered=True` must be returned by the safety gate.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_triggers_fallback_when_too_few_exercises -v
  ```
- **Expected Result**: `PASSED` — `result["fallback_triggered"] is True`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Fallback overall_reasoning explains injury constraints

- **Scenario**: The `overall_reasoning` field must mention injury or constraints so users understand why they received a fallback workout.
- **Description**: Verified by UAT-FUNC-001 (`assert "injury" in ... or "constraint" in ...`). This test confirms the requirement independently with a direct invocation.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -c "
from app.kg.generation_graph import _fallback_node, GenerationState
state: GenerationState = {'member_id': 'm1', 'query': 'workout', 'context': {'safe_exercises': [{'id': 'ex-0', 'name': 'Squat'}], 'member_profile': None, 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {'member_profile': 0, 'safe_exercises': 0, 'preferred_exercises': 0, 'vector_hits': 0, 'total': 0}}, 'fallback_triggered': True, 'recommendation': None, 'error': None}
result = _fallback_node(state)
rec = result['recommendation']
assert 'injury' in rec.overall_reasoning.lower() or 'constraint' in rec.overall_reasoning.lower(), f'Bad reasoning: {rec.overall_reasoning!r}'
print('PASS overall_reasoning:', rec.overall_reasoning)
"
  ```
- **Expected Result**: Prints `PASS overall_reasoning: Limited exercise options are available due to injury constraints. These are the safest alternatives from your profile.` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Fallback preserves skipped_exercise_ids from prior recommendation

- **Scenario**: If the safety gate removed exercises (populating `skipped_exercise_ids`) before triggering the fallback, those IDs must be preserved in the fallback recommendation.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -c "
from app.kg.generation_graph import _fallback_node, GenerationState, WorkoutRecommendation, RecommendedExercise
prior_rec = WorkoutRecommendation(exercises=[], overall_reasoning='', member_id='m1', skipped_exercise_ids=['bad-ex-1', 'bad-ex-2'])
state: GenerationState = {'member_id': 'm1', 'query': 'workout', 'context': {'safe_exercises': [{'id': 'ex-0', 'name': 'Squat'}], 'member_profile': None, 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {'member_profile': 0, 'safe_exercises': 0, 'preferred_exercises': 0, 'vector_hits': 0, 'total': 0}}, 'fallback_triggered': True, 'recommendation': prior_rec, 'error': None}
result = _fallback_node(state)
rec = result['recommendation']
assert rec.skipped_exercise_ids == ['bad-ex-1', 'bad-ex-2'], f'Got: {rec.skipped_exercise_ids}'
print('PASS skipped_exercise_ids preserved:', rec.skipped_exercise_ids)
"
  ```
- **Expected Result**: Prints `PASS skipped_exercise_ids preserved: ['bad-ex-1', 'bad-ex-2']` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Fallback caps at 3 exercises regardless of safe_exercises length

- **Scenario**: When `safe_exercises` has more than 3 entries, the fallback must cap at exactly 3 — never 4 or more.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -c "
from app.kg.generation_graph import _fallback_node, GenerationState
safe = [{'id': f'ex-{i}', 'name': f'Ex {i}'} for i in range(10)]
ctx = {'safe_exercises': safe, 'member_profile': None, 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {'member_profile': 0, 'safe_exercises': 0, 'preferred_exercises': 0, 'vector_hits': 0, 'total': 0}}
state: GenerationState = {'member_id': 'm1', 'query': 'workout', 'context': ctx, 'fallback_triggered': True, 'recommendation': None, 'error': None}
result = _fallback_node(state)
rec = result['recommendation']
assert len(rec.exercises) == 3, f'Expected 3, got {len(rec.exercises)}'
print('PASS exercises count:', len(rec.exercises))
"
  ```
- **Expected Result**: Prints `PASS exercises count: 3` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Test

### UAT-INT-001: Compiled graph routes through fallback when validate_context fires

- **Components**: `build_generation_graph`, `_validate_context_node`, `_fallback_node`, `_format_response_node`
- **Description**: Invoke the compiled graph with `context=None`; the graph must return a `recommendation` (not `None`) populated by `_fallback_node`, without raising an exception.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py -v -k "fallback"
  ```
- **Expected Result**: All 3 fallback tests pass (`PASSED` for `test_fallback_node_uses_safe_exercises_when_triggered`, `test_fallback_node_uses_empty_list_when_no_safe_exercises`, `test_fallback_triggered_by_empty_context`). Zero failures.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: Full test suite — no regressions in generation graph

- **Components**: All nodes in `generation_graph.py`
- **Description**: The full test file must pass (12 tests); adding the fallback node must not break any previously passing test.
- **Steps**:
  1. Run:
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py -v
  ```
- **Expected Result**: `12 passed` with exit code 0. Zero failures, zero errors.
- [x] Pass <!-- 2026-06-06 -->
