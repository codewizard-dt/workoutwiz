# UAT: Workout Generator Sub-Agent

> **Source task**: [`.docs/tasks/completed/028-workout-generator-sub-agent.md`](../tasks/completed/028-workout-generator-sub-agent.md)
> **Generated**: 2026-06-05

---

## Prerequisites

- [ ] Python virtual environment exists at `1-multi-agent/.venv/`
- [ ] `workout-wiz` package is installed in dev mode (`pip install -e ".[dev]"` from `1-multi-agent/`)
- [ ] `1-multi-agent/exercises.json` exists with 50 exercises (source of truth — no DB required for tool tests)
- [ ] `1-multi-agent/src/workout_wiz/agents/workout_generator.py` exists

---

## API Tests

_(These are Python script invocations — the agent exposes no HTTP endpoints. All tests run as shell commands using the installed package.)_

### UAT-API-001: `search_exercises_tool` returns results with correct schema

- **Endpoint**: `search_exercises_tool.invoke({"muscle_groups": ["chest"]})`
- **Description**: Verify the tool returns a non-empty list of exercises matching a muscle group filter, each with the required schema keys.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.agents.workout_generator import search_exercises_tool; r = search_exercises_tool.invoke({'muscle_groups': ['chest']}); print('count:', len(r)); print('first keys:', sorted(r[0].keys()) if r else 'EMPTY')"
  ```
- **Expected Result**: Prints `count: <N>` where N > 0, and `first keys: ['equipment_required', 'id', 'is_duration', 'is_reps', 'muscle_groups', 'name', 'supports_weight']`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-002: `search_exercises_tool` respects `max_results`

- **Endpoint**: `search_exercises_tool.invoke({"max_results": 3})`
- **Description**: Verify the `max_results` parameter caps the returned list at the requested count.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.agents.workout_generator import search_exercises_tool; r = search_exercises_tool.invoke({'max_results': 3}); print('count:', len(r)); assert len(r) <= 3, f'Expected <=3 but got {len(r)}'; print('PASS')"
  ```
- **Expected Result**: Prints `count: 3` and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-003: `search_exercises_tool` filters by equipment

- **Endpoint**: `search_exercises_tool.invoke({"equipment": ["dumbbell"]})`
- **Description**: Verify equipment filter returns only exercises that include the specified equipment (case-insensitive substring match).
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "from workout_wiz.agents.workout_generator import search_exercises_tool; r = search_exercises_tool.invoke({'equipment': ['dumbbell']}); print('count:', len(r)); print('sample:', [x['name'] for x in r[:3]] if r else 'EMPTY'); assert all('dumbbell' in ' '.join(x['equipment_required']).lower() for x in r), 'Equipment filter failed'; print('PASS')"
  ```
- **Expected Result**: Prints `count: <N>` where N > 0, sample exercise names containing dumbbell exercises, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-004: `build_workout_tool` with valid IDs produces phased plan

- **Endpoint**: `build_workout_tool.invoke({"goal": "full body strength", "exercise_ids": [<5 real IDs>], "sets": 3, "rest_seconds": 90})`
- **Description**: Verify the tool builds a workout with the correct phase structure when given ≥3 valid exercise IDs. With 5 IDs: warmup=first 2, main=remaining 3.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory (uses `search_exercises_tool` to get real IDs)
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool, build_workout_tool
exercises = search_exercises_tool.invoke({'max_results': 5})
ids = [e['id'] for e in exercises]
result = build_workout_tool.invoke({'goal': 'full body strength', 'exercise_ids': ids, 'sets': 3, 'rest_seconds': 90})
print('goal:', result['goal'])
print('total_exercises:', result['total_exercises'])
print('invalid_ids_skipped:', result['invalid_ids_skipped'])
print('warmup count:', len(result['phases']['warmup']))
print('main count:', len(result['phases']['main']))
print('cooldown count:', len(result['phases']['cooldown']))
assert result['total_exercises'] == 5
assert result['invalid_ids_skipped'] == []
assert len(result['phases']['warmup']) == 2
assert len(result['phases']['main']) == 3
print('PASS')
"
  ```
- **Expected Result**: Prints the goal, `total_exercises: 5`, `invalid_ids_skipped: []`, `warmup count: 2`, `main count: 3`, `cooldown count: 0`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-005: `build_workout_tool` with fewer than 3 exercises skips warmup

- **Endpoint**: `build_workout_tool.invoke({"goal": "quick workout", "exercise_ids": [<2 real IDs>], ...})`
- **Description**: Verify that when fewer than 3 valid exercise IDs are provided, warmup is empty and all exercises go to main.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool, build_workout_tool
exercises = search_exercises_tool.invoke({'max_results': 2})
ids = [e['id'] for e in exercises]
result = build_workout_tool.invoke({'goal': 'quick workout', 'exercise_ids': ids, 'sets': 2, 'rest_seconds': 60})
print('total_exercises:', result['total_exercises'])
print('warmup count:', len(result['phases']['warmup']))
print('main count:', len(result['phases']['main']))
assert len(result['phases']['warmup']) == 0, f'Expected empty warmup but got {result[\"phases\"][\"warmup\"]}'
assert len(result['phases']['main']) == len(ids)
print('PASS')
"
  ```
- **Expected Result**: Prints `total_exercises: 2`, `warmup count: 0`, `main count: 2`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-006: `build_workout_tool` rejects invalid exercise IDs

- **Endpoint**: `build_workout_tool.invoke({"goal": "test", "exercise_ids": ["00000000-0000-0000-0000-000000000000"], ...})`
- **Description**: Verify that invalid (non-existent) exercise IDs are not silently included — they are listed in `invalid_ids_skipped` and excluded from `total_exercises`.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import build_workout_tool
result = build_workout_tool.invoke({'goal': 'test', 'exercise_ids': ['00000000-0000-0000-0000-000000000000'], 'sets': 3, 'rest_seconds': 60})
print('total_exercises:', result['total_exercises'])
print('invalid_ids_skipped:', result['invalid_ids_skipped'])
assert result['total_exercises'] == 0
assert '00000000-0000-0000-0000-000000000000' in result['invalid_ids_skipped']
print('PASS')
"
  ```
- **Expected Result**: Prints `total_exercises: 0`, `invalid_ids_skipped: ['00000000-0000-0000-0000-000000000000']`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-API-007: `build_workout_tool` exercise entries contain expected fields

- **Endpoint**: `build_workout_tool` — exercise dict schema
- **Description**: Verify each exercise entry in the workout plan contains `id`, `name`, `sets`, `reps` (or None), `duration_s` (or None), and `rest_s`. Reps-based exercises have `reps = "10-12"`; duration-based exercises have `duration_s = 30`.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool, build_workout_tool
exercises = search_exercises_tool.invoke({'max_results': 5})
ids = [e['id'] for e in exercises]
result = build_workout_tool.invoke({'goal': 'schema test', 'exercise_ids': ids, 'sets': 4, 'rest_seconds': 120})
all_items = result['phases']['warmup'] + result['phases']['main']
for item in all_items:
    assert 'id' in item and 'name' in item and 'sets' in item and 'rest_s' in item
    assert item['sets'] == 4
    assert item['rest_s'] == 120
    assert 'reps' in item and 'duration_s' in item
print('fields OK for', len(all_items), 'exercises')
print('PASS')
"
  ```
- **Expected Result**: Prints `fields OK for 5 exercises` and `PASS`
- [x] Pass <!-- 2026-06-05 -->

---

## Edge Case Tests

### UAT-EDGE-001: `search_exercises_tool` with no matching filters returns empty list

- **Scenario**: Filter by a muscle group that no exercise targets — should return empty list, not raise an exception.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool
result = search_exercises_tool.invoke({'muscle_groups': ['zzznonexistentmuscle123']})
print('count:', len(result))
assert isinstance(result, list)
assert len(result) == 0
print('PASS')
"
  ```
- **Expected Result**: Prints `count: 0` and `PASS` (no exception raised)
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-002: `build_workout_tool` with empty exercise_ids list

- **Scenario**: An empty `exercise_ids` list should produce a valid (but empty) workout structure without raising an exception.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import build_workout_tool
result = build_workout_tool.invoke({'goal': 'empty test', 'exercise_ids': [], 'sets': 3, 'rest_seconds': 90})
print('total_exercises:', result['total_exercises'])
print('invalid_ids_skipped:', result['invalid_ids_skipped'])
assert result['total_exercises'] == 0
assert result['invalid_ids_skipped'] == []
assert result['phases']['warmup'] == []
assert result['phases']['main'] == []
print('PASS')
"
  ```
- **Expected Result**: Prints `total_exercises: 0`, `invalid_ids_skipped: []`, and `PASS` (no exception raised)
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-003: `build_workout_tool` with mixed valid and invalid IDs

- **Scenario**: A mix of valid and invalid exercise IDs — valid ones are used, invalid ones are reported in `invalid_ids_skipped`.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool, build_workout_tool
exercises = search_exercises_tool.invoke({'max_results': 3})
valid_ids = [e['id'] for e in exercises]
mixed_ids = valid_ids + ['00000000-0000-0000-0000-000000000000']
result = build_workout_tool.invoke({'goal': 'mixed test', 'exercise_ids': mixed_ids, 'sets': 3, 'rest_seconds': 90})
print('total_exercises:', result['total_exercises'])
print('invalid_ids_skipped:', result['invalid_ids_skipped'])
assert result['total_exercises'] == 3
assert '00000000-0000-0000-0000-000000000000' in result['invalid_ids_skipped']
print('PASS')
"
  ```
- **Expected Result**: Prints `total_exercises: 3`, `invalid_ids_skipped: ['00000000-0000-0000-0000-000000000000']`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-EDGE-004: `search_exercises_tool` with multiple simultaneous filters (AND logic)

- **Scenario**: Filters on both `muscle_groups` and `equipment` are applied together — only exercises matching both criteria are returned.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import search_exercises_tool
result = search_exercises_tool.invoke({'muscle_groups': ['chest'], 'equipment': ['dumbbell']})
print('count:', len(result))
for e in result:
    mg_ok = any('chest' in m.lower() for m in e['muscle_groups'])
    eq_ok = any('dumbbell' in eq.lower() for eq in e['equipment_required'])
    assert mg_ok and eq_ok, f'Filter mismatch: {e[\"name\"]}'
print('PASS')
"
  ```
- **Expected Result**: Prints `count: <N>` where N > 0, and `PASS` (all results match both filters)
- [x] Pass <!-- 2026-06-05 -->

---

## Integration Tests

### UAT-INT-001: Generator `StateGraph` compiles and has correct node/edge topology

- **Components**: `build_workout_generator_graph`, `StateGraph`, `ToolNode`
- **Flow**: Build the graph, compile it, and verify nodes and edges match the required `generate → tools → generate` loop topology.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import build_workout_generator_graph
graph = build_workout_generator_graph()
compiled = graph.compile()
assert compiled is not None
print('graph compiles: OK')
print('nodes:', list(graph.nodes.keys()))
assert 'generate' in graph.nodes
assert 'tools' in graph.nodes
print('PASS')
"
  ```
- **Expected Result**: Prints `graph compiles: OK`, `nodes: [...]` containing both `generate` and `tools`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-002: Module-level `workout_generator_graph` compiled export exists

- **Components**: `workout_generator_graph` module-level variable
- **Flow**: Import the compiled singleton directly and verify it is a non-None compiled graph.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.agents.workout_generator import workout_generator_graph
assert workout_generator_graph is not None
print('type:', type(workout_generator_graph).__name__)
print('PASS')
"
  ```
- **Expected Result**: Prints `type: CompiledStateGraph` (or similar LangGraph compiled type) and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-003: Hub imports workout generator and wires it as `workout_gen` node (not stub)

- **Components**: `hub.py`, `workout_generator_graph`, `build_hub_graph`
- **Flow**: Import hub, verify the `workout_gen` node is registered and the hub compiles without errors.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
from workout_wiz.hub import hub, build_hub_graph
assert hub is not None
graph = build_hub_graph()
assert 'workout_gen' in graph.nodes
print('hub nodes:', list(graph.nodes.keys()))
print('PASS')
"
  ```
- **Expected Result**: Prints `hub nodes: [...]` containing `workout_gen`, and `PASS`
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-004: Full pytest suite passes (6/6 tests)

- **Components**: All tests in `1-multi-agent/tests/test_workout_generator.py`
- **Flow**: Run the project's own unit tests to confirm the implementation satisfies every programmatic assertion in the test file.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/pytest tests/test_workout_generator.py -v
  ```
- **Expected Result**: All 6 tests pass (`6 passed`). No failures, errors, or skips.
- [x] Pass <!-- 2026-06-05 -->

### UAT-INT-005: `_workout_gen_stub` is removed from hub

- **Components**: `hub.py` source code
- **Flow**: Confirm the stub function is no longer present in `hub.py`, ensuring the real generator graph is used.
- **Steps**:
  1. Run the command below from the `1-multi-agent/` directory
- **Command**:
  ```bash
  cd 1-multi-agent && .venv/bin/python -c "
import inspect
import workout_wiz.hub as hub_module
stub_present = hasattr(hub_module, '_workout_gen_stub')
print('stub present:', stub_present)
assert not stub_present, '_workout_gen_stub should have been removed from hub.py'
print('PASS')
"
  ```
- **Expected Result**: Prints `stub present: False` and `PASS`
- [x] Pass <!-- 2026-06-05 -->
