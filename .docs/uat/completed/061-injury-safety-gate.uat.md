# UAT: Injury Safety Gate — Post-Generation Validation

> **Source task**: [`.docs/tasks/completed/061-injury-safety-gate.md`](../tasks/completed/061-injury-safety-gate.md)
> **Generated**: 2026-06-06

This feature adds `_safety_gate_node` to `backend/app/kg/generation_graph.py`, wired between `generate_workout` and `format_response`. It removes contraindicated exercises post-generation and triggers fallback when too few safe exercises survive.

There are no HTTP endpoints or UI components introduced by this task — all tests are Python unit/integration tests executed via `pytest`.

---

## Prerequisites

- [x] Working directory is the repo root
- [x] Python virtual environment is active (`backend/.venv`) or available via the Makefile
- [x] `.env` file is present at the repo root with `ANTHROPIC_API_KEY` set (required for LangGraph compile, not called in unit tests)
- [x] `cd backend && python -m pytest --collect-only tests/kg/test_generation_graph.py` exits 0 and lists 9 tests

---

## Unit Tests: `_safety_gate_node` direct invocation

### UAT-UNIT-001: Safety gate removes a contraindicated exercise and records it in skipped_exercise_ids

- **Description**: When `context.contraindicated_ids` contains an exercise ID that is in the LLM's recommendation, the gate must remove it from `exercises`, add it to `skipped_exercise_ids`, and append the removal note to `overall_reasoning`.
- **Steps**:
  1. Run the pytest command below from the repo root — it targets the single test that covers this acceptance criterion
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_removes_contraindicated_exercise -v
  ```
- **Expected Result**: `PASSED` — the test asserts that `ex-0` is absent from `final_rec.exercises`, present in `final_rec.skipped_exercise_ids`, and that `"(Removed 1 contraindicated exercise(s).)"` appears in `final_rec.overall_reasoning`
- [x] Pass

---

### UAT-UNIT-002: Safety gate leaves a clean recommendation unchanged

- **Description**: When no exercise IDs in the recommendation appear in `context.contraindicated_ids`, the gate must not modify `exercises` or `skipped_exercise_ids`, and must not set `fallback_triggered`.
- **Steps**:
  1. Run the pytest command below from the repo root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_passes_clean_recommendation -v
  ```
- **Expected Result**: `PASSED` — the test asserts `fallback_triggered` is not `True` and `recommendation.exercises` is unchanged when the contraindicated IDs don't match any exercise in the recommendation
- [x] Pass

---

### UAT-UNIT-003: Safety gate triggers fallback when ≤1 exercise survives

- **Description**: When filtering leaves fewer than 2 safe exercises, `fallback_triggered` must be set to `True` so the fallback handler (TASK-063) can pick it up.
- **Steps**:
  1. Run the pytest command below from the repo root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_triggers_fallback_when_too_few_exercises -v
  ```
- **Expected Result**: `PASSED` — the test asserts `result["fallback_triggered"] is True` after filtering removes the only exercise, leaving 0 survivors
- [x] Pass

---

### UAT-UNIT-004: Safety gate is a no-op when fallback_triggered is already True

- **Description**: If the upstream `validate_context` node has already set `fallback_triggered=True`, the gate must skip all filtering logic and return an empty dict (no mutation).
- **Steps**:
  1. Run the inline Python snippet below from the repo root. It directly exercises the early-exit branch of `_safety_gate_node`.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node, WorkoutRecommendation, RecommendedExercise
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'contraindicated_ids': ['ex-1'], 'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': WorkoutRecommendation(exercises=[RecommendedExercise(exercise_id='ex-1', name='X', sets=3, reps=10, reasoning='r')], overall_reasoning='ok', member_id='m1'),
    'fallback_triggered': True,
    'error': None,
}
result = _safety_gate_node(state)
assert result == {}, f'Expected empty dict, got {result}'
print('PASS: safety gate is a no-op when fallback_triggered=True')
"
  ```
- **Expected Result**: Prints `PASS: safety gate is a no-op when fallback_triggered=True` with exit code 0
- [x] Pass

---

### UAT-UNIT-005: Safety gate is a no-op when recommendation is None

- **Description**: If `recommendation` is `None` (e.g., LLM call failed), the gate must skip all filtering logic and return an empty dict.
- **Steps**:
  1. Run the inline Python snippet below from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'contraindicated_ids': ['ex-1'], 'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': None,
    'fallback_triggered': False,
    'error': None,
}
result = _safety_gate_node(state)
assert result == {}, f'Expected empty dict, got {result}'
print('PASS: safety gate is a no-op when recommendation is None')
"
  ```
- **Expected Result**: Prints `PASS: safety gate is a no-op when recommendation is None` with exit code 0
- [x] Pass

---

## Integration Tests: graph topology

### UAT-INT-001: `build_generation_graph` wires safety_gate between generate_workout and format_response

- **Description**: The compiled graph must include the `safety_gate` node and route `generate_workout → safety_gate → format_response`. This validates the task's wiring requirement at the graph-structure level.
- **Steps**:
  1. Run the inline Python snippet below from the repo root — it inspects the compiled graph's node set.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import build_generation_graph
graph = build_generation_graph()
nodes = set(graph.get_graph().nodes.keys())
assert 'safety_gate' in nodes, f'safety_gate not in graph nodes: {nodes}'
print('PASS: safety_gate node present in compiled graph')
print('Nodes:', nodes)
"
  ```
- **Expected Result**: Prints `PASS: safety_gate node present in compiled graph` and lists the node names (must include `validate_context`, `generate_workout`, `safety_gate`, `format_response`) with exit code 0
- [x] Pass

---

### UAT-INT-002: Full test suite for generation_graph passes (all 9 tests)

- **Description**: All unit tests in `test_generation_graph.py` — including the 3 new safety gate tests — must pass together without regressions.
- **Steps**:
  1. Run the full test module from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py -v
  ```
- **Expected Result**: `9 passed` — all tests green, no failures, no errors
- [x] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Safety gate handles empty contraindicated_ids list gracefully

- **Description**: When `contraindicated_ids` is present but empty (`[]`), no exercises should be removed and fallback should not be triggered (assumes ≥2 exercises in the recommendation).
- **Steps**:
  1. Run the inline Python snippet below from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node, WorkoutRecommendation, RecommendedExercise
exercises = [
    RecommendedExercise(exercise_id='ex-1', name='A', sets=3, reps=10, reasoning='r1'),
    RecommendedExercise(exercise_id='ex-2', name='B', sets=3, reps=12, reasoning='r2'),
]
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'contraindicated_ids': [], 'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': WorkoutRecommendation(exercises=exercises, overall_reasoning='ok', member_id='m1'),
    'fallback_triggered': False,
    'error': None,
}
result = _safety_gate_node(state)
assert result.get('fallback_triggered') is not True, 'Should not trigger fallback with 2 safe exercises'
assert 'recommendation' not in result or len(result['recommendation'].exercises) == 2
print('PASS: empty contraindicated_ids list — no exercises removed, no fallback')
"
  ```
- **Expected Result**: Prints `PASS: empty contraindicated_ids list — no exercises removed, no fallback` with exit code 0
- [x] Pass

---

### UAT-EDGE-002: Safety gate handles context with no contraindicated_ids key at all

- **Description**: When `context` dict has no `contraindicated_ids` key (not just empty — absent entirely), the gate must treat it as an empty set and not crash.
- **Steps**:
  1. Run the inline Python snippet below from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node, WorkoutRecommendation, RecommendedExercise
exercises = [
    RecommendedExercise(exercise_id='ex-1', name='A', sets=3, reps=10, reasoning='r1'),
    RecommendedExercise(exercise_id='ex-2', name='B', sets=3, reps=12, reasoning='r2'),
]
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': WorkoutRecommendation(exercises=exercises, overall_reasoning='ok', member_id='m1'),
    'fallback_triggered': False,
    'error': None,
}
result = _safety_gate_node(state)
assert result.get('fallback_triggered') is not True
print('PASS: missing contraindicated_ids key handled gracefully — no crash, no fallback')
"
  ```
- **Expected Result**: Prints `PASS: missing contraindicated_ids key handled gracefully — no crash, no fallback` with exit code 0
- [x] Pass

---

### UAT-EDGE-003: Safety gate removes multiple contraindicated exercises and counts correctly

- **Description**: When multiple exercises are contraindicated, all must be removed, all IDs recorded in `skipped_exercise_ids`, and the removal note must state the correct count.
- **Steps**:
  1. Run the inline Python snippet below from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node, WorkoutRecommendation, RecommendedExercise
exercises = [
    RecommendedExercise(exercise_id='bad-1', name='A', sets=3, reps=10, reasoning='r'),
    RecommendedExercise(exercise_id='bad-2', name='B', sets=3, reps=10, reasoning='r'),
    RecommendedExercise(exercise_id='safe-1', name='C', sets=3, reps=10, reasoning='r'),
    RecommendedExercise(exercise_id='safe-2', name='D', sets=3, reps=10, reasoning='r'),
]
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'contraindicated_ids': ['bad-1', 'bad-2'], 'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': WorkoutRecommendation(exercises=exercises, overall_reasoning='Solid workout.', member_id='m1'),
    'fallback_triggered': False,
    'error': None,
}
result = _safety_gate_node(state)
rec = result['recommendation']
ids = [e.exercise_id for e in rec.exercises]
assert 'bad-1' not in ids and 'bad-2' not in ids, f'Contraindicated exercises still present: {ids}'
assert 'bad-1' in rec.skipped_exercise_ids and 'bad-2' in rec.skipped_exercise_ids
assert '(Removed 2 contraindicated exercise(s).)' in rec.overall_reasoning
assert result.get('fallback_triggered') is not True, 'Should not fallback — 2 safe exercises remain'
print('PASS: 2 contraindicated exercises removed, count correct, no fallback with 2 survivors')
"
  ```
- **Expected Result**: Prints `PASS: 2 contraindicated exercises removed, count correct, no fallback with 2 survivors` with exit code 0
- [x] Pass

---

### UAT-EDGE-004: Exactly 1 surviving exercise triggers fallback

- **Description**: The fallback threshold is `< 2`. When exactly 1 exercise survives (not 0), `fallback_triggered` must still be `True`.
- **Steps**:
  1. Run the inline Python snippet below from the repo root.
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import _safety_gate_node, WorkoutRecommendation, RecommendedExercise
exercises = [
    RecommendedExercise(exercise_id='bad-1', name='A', sets=3, reps=10, reasoning='r'),
    RecommendedExercise(exercise_id='safe-1', name='B', sets=3, reps=10, reasoning='r'),
]
state = {
    'member_id': 'm1',
    'query': 'test',
    'context': {'contraindicated_ids': ['bad-1'], 'safe_exercises': [], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {}},
    'recommendation': WorkoutRecommendation(exercises=exercises, overall_reasoning='ok', member_id='m1'),
    'fallback_triggered': False,
    'error': None,
}
result = _safety_gate_node(state)
assert result.get('fallback_triggered') is True, f'Expected fallback_triggered=True with 1 survivor, got {result}'
print('PASS: exactly 1 survivor triggers fallback_triggered=True')
"
  ```
- **Expected Result**: Prints `PASS: exactly 1 survivor triggers fallback_triggered=True` with exit code 0
- [x] Pass
