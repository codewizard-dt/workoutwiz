# UAT: Workout Logger Sub-Agent

> **Source task**: [`.docs/tasks/completed/029-workout-logger-sub-agent.md`](../tasks/completed/029-workout-logger-sub-agent.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] `1-multi-agent/.venv` exists and dependencies are installed (`cd 1-multi-agent && pip install -e ".[dev]"` if not)
- [ ] Working directory for all shell commands is `1-multi-agent/`
- [ ] `exercises.json` is present at `1-multi-agent/exercises.json` (50 exercises)
- [ ] No `ANTHROPIC_API_KEY` required — all tests are pure-function (no real LLM calls)

---

## API Tests

*This task introduces a pure Python/LangGraph module with no HTTP endpoints. The "API" under test is the Python module interface: the exported symbols, their signatures, and their runtime behaviour.*

### UAT-API-001: WorkoutLog and LoggedSet schema instantiation

- **Module**: `workout_wiz.agents.workout_logger`
- **Description**: Verify `WorkoutLog` and `LoggedSet` Pydantic models can be instantiated with valid data and expose the required fields.
- **Steps**:
  1. Activate the virtualenv and run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import WorkoutLog, LoggedSet
s = LoggedSet(exercise_name='Barbell Decline Bench Press', sets=3, reps=10, weight_kg=80.0)
log = WorkoutLog(raw_input='3x10 Barbell Decline Bench Press at 80kg', logged_sets=[s])
import json; print(json.dumps({'raw_input': log.raw_input, 'sets': log.logged_sets[0].sets, 'reps': log.logged_sets[0].reps, 'weight_kg': log.logged_sets[0].weight_kg, 'unrecognized': log.unrecognized, 'parse_notes': log.parse_notes}))
"
  ```
- **Expected Result**: Exits 0. Prints JSON with `raw_input` == `"3x10 Barbell Decline Bench Press at 80kg"`, `sets` == `3`, `reps` == `10`, `weight_kg` == `80.0`, `unrecognized` == `[]`, `parse_notes` == `null`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-002: LoggedSet default field values

- **Module**: `workout_wiz.agents.workout_logger.LoggedSet`
- **Description**: Verify optional metric fields default to `None` and `match_confidence` defaults to `0.0`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import LoggedSet
import json
s = LoggedSet(exercise_name='push up')
print(json.dumps({'exercise_id': s.exercise_id, 'match_confidence': s.match_confidence, 'sets': s.sets, 'reps': s.reps, 'weight_kg': s.weight_kg, 'duration_s': s.duration_s, 'distance_m': s.distance_m, 'notes': s.notes}))
"
  ```
- **Expected Result**: Exits 0. Prints JSON with all fields `null` except `match_confidence` which is `0.0`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-003: `_fuzzy_match_exercise` — exact name match

- **Module**: `workout_wiz.agents.workout_logger._fuzzy_match_exercise`
- **Description**: Verify that an exact exercise name resolves to the correct UUID with confidence >= 0.99.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import _fuzzy_match_exercise
from workout_wiz.exercises import get_all_exercises
exercises = get_all_exercises()
exercise_id, confidence = _fuzzy_match_exercise('Barbell Decline Bench Press', exercises)
print(f'id={exercise_id} confidence={confidence:.4f}')
assert exercise_id == '0b3178cf-bf89-45a3-bfb0-27310ef6ef38', f'wrong id: {exercise_id}'
assert confidence >= 0.99, f'confidence too low: {confidence}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0. Prints `id=0b3178cf-bf89-45a3-bfb0-27310ef6ef38 confidence=1.0000` (or >= 0.99) and `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-004: `_fuzzy_match_exercise` — below-threshold name returns None

- **Module**: `workout_wiz.agents.workout_logger._fuzzy_match_exercise`
- **Description**: Verify that a nonsense string with no close match returns `(None, <0.75)`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import _fuzzy_match_exercise
from workout_wiz.exercises import get_all_exercises
exercises = get_all_exercises()
exercise_id, confidence = _fuzzy_match_exercise('xyzzy nonexistent foobar', exercises)
print(f'id={exercise_id} confidence={confidence:.4f}')
assert exercise_id is None, f'expected None, got {exercise_id}'
assert confidence < 0.75, f'expected < 0.75, got {confidence}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0. Prints `id=None` and confidence < 0.75, plus `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-005: `_fuzzy_match_exercise` — empty exercise list returns (None, 0.0)

- **Module**: `workout_wiz.agents.workout_logger._fuzzy_match_exercise`
- **Description**: Verify the guard for an empty exercise list returns `(None, 0.0)` without raising.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import _fuzzy_match_exercise
exercise_id, confidence = _fuzzy_match_exercise('Squat', [])
assert exercise_id is None
assert confidence == 0.0
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-006: `build_workout_logger_graph` compiles without error

- **Module**: `workout_wiz.agents.workout_logger.build_workout_logger_graph`
- **Description**: Verify the graph builder produces a compiled LangGraph that is not None.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import build_workout_logger_graph
g = build_workout_logger_graph().compile()
assert g is not None
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-007: Hub imports and compiles with `workout_logger_graph` wired as `workout_log` node

- **Module**: `workout_wiz.hub`
- **Description**: Verify the hub graph compiles with `workout_logger_graph` (not a stub) wired as the `workout_log` node, and the `_workout_log_stub` symbol is absent.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import hub
print('Hub OK')
import inspect, workout_wiz.hub as h
assert not hasattr(h, '_workout_log_stub'), 'stub should be removed'
from workout_wiz.agents.workout_logger import workout_logger_graph
print('Logger wired')
"
  ```
- **Expected Result**: Exits 0. Prints `Hub OK` then `Logger wired`. No `AssertionError`.
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: `WorkoutLog.unrecognized` defaults to empty list

- **Scenario**: `WorkoutLog` created without explicitly providing `unrecognized` — should default to `[]`, not `None`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_logger import WorkoutLog, LoggedSet
log = WorkoutLog(raw_input='test', logged_sets=[LoggedSet(exercise_name='push up')])
assert log.unrecognized == [], f'expected [], got {log.unrecognized}'
print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: `_fuzzy_match_exercise` threshold is strictly >= 0.75

- **Scenario**: A match with confidence exactly at the boundary (score == 75 out of 100) should be accepted; a score of 74 should return `None`.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`. This directly tests the threshold logic by mocking `rapidfuzz`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from unittest.mock import patch, MagicMock
from workout_wiz.agents.workout_logger import _fuzzy_match_exercise

fake_exercise = MagicMock()
fake_exercise.name = 'Bench Press'
fake_exercise.id = 'fake-uuid-001'

# Score 75 -> confidence 0.75 -> should match
with patch('workout_wiz.agents.workout_logger.fuzz_process') as mock_proc:
    mock_proc.extractOne.return_value = ('Bench Press', 75, 0)
    eid, conf = _fuzzy_match_exercise('bench press', [fake_exercise])
    assert eid == 'fake-uuid-001', f'expected match at 75, got {eid}'

# Score 74 -> confidence 0.74 -> should NOT match
with patch('workout_wiz.agents.workout_logger.fuzz_process') as mock_proc:
    mock_proc.extractOne.return_value = ('Bench Press', 74, 0)
    eid, conf = _fuzzy_match_exercise('bench press', [fake_exercise])
    assert eid is None, f'expected None at 74, got {eid}'
    assert conf == 0.74, f'expected conf 0.74, got {conf}'

print('PASS')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS`.
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: `LoggedSet.exercise_id` stays None if LLM already provided a value (no double-matching)

- **Scenario**: The fuzzy matching loop only runs when `exercise_id is None`. If the LLM pre-populated `exercise_id`, it must not be overwritten.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`. Verifies the guard condition `if logged_set.exercise_id is None` in `_log_node` by inspecting the source.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
from workout_wiz.agents import workout_logger
src = inspect.getsource(workout_logger._log_node)
assert 'if logged_set.exercise_id is None' in src, 'guard condition missing from _log_node'
print('PASS: guard condition present')
"
  ```
- **Expected Result**: Exits 0 and prints `PASS: guard condition present`.
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Full pytest suite — 5/5 pure-function tests pass

- **Components**: `_fuzzy_match_exercise`, `build_workout_logger_graph`, `WorkoutLog`, `LoggedSet`, `get_all_exercises`
- **Flow**: Run the task-specified test file using the virtualenv's pytest; all 5 tests must pass without LLM calls.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_workout_logger.py -v
  ```
- **Expected Result**: Exits 0. Output shows `5 passed` with the following test names all green:
  - `test_logger_graph_compiles`
  - `test_fuzzy_match_exact`
  - `test_fuzzy_match_partial`
  - `test_fuzzy_match_below_threshold`
  - `test_workout_log_schema`
  No tests failed, skipped, or errored.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: Hub still compiles after logger wiring (no regression)

- **Components**: `hub.py`, `workout_logger.py`, `AgentState`, `workout_logger_graph`
- **Flow**: Import the compiled `hub` object end-to-end; confirm `workout_log` node references `workout_logger_graph` and the graph has the expected topology.
- **Steps**:
  1. Run the command below from inside `1-multi-agent/`.
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import hub, build_hub_graph
from workout_wiz.agents.workout_logger import workout_logger_graph
g = build_hub_graph()
compiled = g.compile()
assert compiled is not None
print('Hub OK')
"
  ```
- **Expected Result**: Exits 0 and prints `Hub OK`. No `ImportError`, `AttributeError`, or `LangGraphError`.
- [x] Pass <!-- 2026-06-05 -->
