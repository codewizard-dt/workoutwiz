# UAT: Instrument Generation Sub-Graph Nodes

> **Source task**: [`.docs/tasks/completed/077-instrument-generation-nodes.md`](../../tasks/completed/077-instrument-generation-nodes.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Working directory is `backend/` (or commands are run from the repo root with `cd backend &&`)
- [ ] Python virtualenv is active with dev dependencies installed (`pip install -e ".[dev]"`)
- [ ] `backend/tests/kg/test_generation_graph.py` exists and contains the audit-instrumentation tests

---

## Integration Tests

### UAT-INT-001: safety_gate node appends kg_generation_safety_gate audit entry with violation counts
- **Components**: `_safety_gate_node` in `backend/app/kg/generation_graph.py`, `GenerationState`
- **Flow**: Call `_safety_gate_node` with a state containing one exercise and one contraindicated ID matching that exercise. Verify the returned `audit_log` entry contains the correct event name, latency, exercise counts, and violation count.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_audit_entry_populated -v
  ```
- **Expected Result**: `1 passed` — entry has `event == "kg_generation_safety_gate"`, `exercise_in == 1`, `exercise_out == 0`, `violations_filtered == 1`, `latency_ms >= 0`, `user_id == "m1"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: safety_gate node appends entry with zero violations when no contraindications
- **Components**: `_safety_gate_node` in `backend/app/kg/generation_graph.py`
- **Flow**: Call `_safety_gate_node` with a recommendation whose exercises are all safe (no contraindicated IDs). Verify no exercises are removed and violations_filtered is 0.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_audit_entry_no_violations -v
  ```
- **Expected Result**: `1 passed` — entry has `violations_filtered == 0`, `exercise_in == exercise_out`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: safety_gate node emits skipped entry when fallback already triggered
- **Components**: `_safety_gate_node` in `backend/app/kg/generation_graph.py`
- **Flow**: Call `_safety_gate_node` with `fallback_triggered=True`. The node should emit a skipped audit entry rather than processing exercises.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_safety_gate_skipped_audit_entry -v
  ```
- **Expected Result**: `1 passed` — entry has `event == "kg_generation_safety_gate"`, `skipped == True`, `exercise_in == 0`, `exercise_out == 0`, `violations_filtered == 0`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-004: generation node appends kg_generation_llm audit entry with token and exercise fields
- **Components**: `_generate_workout_node` in `backend/app/kg/generation_graph.py`, `ChatAnthropic` (mocked)
- **Flow**: Call `_generate_workout_node` with a mocked LLM that returns a `WorkoutRecommendation` directly. Verify the audit entry includes event name, model, provider, latency, token fields, and exercise_count.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_generate_workout_node_audit_entry -v
  ```
- **Expected Result**: `1 passed` — entry has `event == "kg_generation_llm"`, `provider == "anthropic"`, `model` is not None, `latency_ms >= 0`, `tokens_in` present, `tokens_out` present, `exercise_count == 1`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-005: fallback_handler node appends kg_generation_fallback audit entry
- **Components**: `_fallback_node` in `backend/app/kg/generation_graph.py`
- **Flow**: Call `_fallback_node` with `fallback_triggered=True` and a context slice containing safe exercises. Verify the audit entry includes event name, latency, fallback_triggered flag, and exercise_count.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_fallback_node_audit_entry_populated -v
  ```
- **Expected Result**: `1 passed` — entry has `event == "kg_generation_fallback"`, `fallback_triggered == True`, `latency_ms >= 0`, `exercise_count >= 0`, `user_id == "m1"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-006: All 3 audit entries present after happy-path generation + safety gate
- **Components**: `_generate_workout_node`, `_safety_gate_node` (both from `backend/app/kg/generation_graph.py`)
- **Flow**: Simulate a complete happy-path run: call the generation node (mocked LLM returning 2 exercises with no contraindicated IDs), then feed the result into the safety gate node. Verify the combined `audit_log` contains entries for both `kg_generation_llm` and `kg_generation_safety_gate`, and all entries have non-negative latency.
- **Steps**:
  1. Run the targeted pytest below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py::test_all_three_audit_entries_present_after_happy_path -v
  ```
- **Expected Result**: `1 passed` — `audit_log` contains events `"kg_generation_llm"` and `"kg_generation_safety_gate"`; every entry has `latency_ms >= 0`
- [x] Pass <!-- 2026-06-06 -->

---

## Full Audit Suite

### UAT-INT-007: All generation graph audit instrumentation tests pass together
- **Components**: All nodes in `backend/app/kg/generation_graph.py`
- **Flow**: Run the complete test module to confirm all audit-instrumentation tests pass without regression against pre-existing tests.
- **Steps**:
  1. Run all tests in the generation graph test module from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_generation_graph.py -v
  ```
- **Expected Result**: All tests pass (`X passed, 0 failed`). The tests `test_safety_gate_audit_entry_populated`, `test_safety_gate_audit_entry_no_violations`, `test_safety_gate_skipped_audit_entry`, `test_generate_workout_node_audit_entry`, `test_fallback_node_audit_entry_populated`, and `test_all_three_audit_entries_present_after_happy_path` are all present and green.
- [x] Pass <!-- 2026-06-06 -->
