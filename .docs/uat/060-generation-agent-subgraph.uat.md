# UAT: Generation Agent Sub-Graph

> **Source task**: [`.docs/tasks/060-generation-agent-subgraph.md`](../tasks/060-generation-agent-subgraph.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Docker Compose stack is up (`make dev` or `docker compose up`)  **OR** a local Python venv is active with backend deps installed (`cd backend && pip install -e ".[dev]"`)
- [ ] `.env` file exists with `ANTHROPIC_API_KEY` and `GENERATOR_MODEL` (or defaults apply — `claude-haiku-4-5-20251001`)
- [ ] `backend/app/kg/generation_graph.py` exists and is importable
- [ ] `backend/tests/kg/test_generation_graph.py` exists with ≥4 tests

---

## Unit / Integration Tests

These tests exercise the `GenerationState` graph directly via pytest. All LLM calls are mocked — no live API spend required.

### UAT-UNIT-001: Full test suite passes

- **Description**: Run the full `test_generation_graph.py` suite and assert all tests pass. This is the primary gate for this task.
- **Steps**:
  1. Ensure the backend environment is set up (see Prerequisites)
  2. Run the command below from the project root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py -v
  ```
- **Expected Result**: All tests collected pass (`PASSED`). Output shows at minimum these 4 test names collected and green:
  - `test_build_generation_graph_returns_compiled_graph`
  - `test_validate_context_triggers_fallback_when_no_safe_exercises`
  - `test_generate_workout_returns_recommendation`
  - `test_generate_workout_skips_generation_when_fallback_triggered`

  No `FAILED`, `ERROR`, or `WARNING: no tests ran` lines appear.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: `build_generation_graph()` returns a compiledgraph with `.ainvoke`

- **Description**: Verify the factory function compiles the StateGraph and returns an object that exposes the async invoke interface (i.e. the graph is properly wired).
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_build_generation_graph_returns_compiled_graph -v
  ```
- **Expected Result**: `PASSED` — `hasattr(graph, "ainvoke")` assertion holds. No `AttributeError` or `AssertionError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: `validate_context` triggers fallback when `safe_exercises` is empty

- **Description**: Verify that the `_validate_context_node` function returns `{"fallback_triggered": True}` when the context carries an empty `safe_exercises` list. This is the requirement that prevents the LLM from being called with no usable exercises.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_validate_context_triggers_fallback_when_no_safe_exercises -v
  ```
- **Expected Result**: `PASSED` — `result["fallback_triggered"]` is `True` when `safe_exercises=[]`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: `validate_context` does NOT trigger fallback when safe exercises are present

- **Description**: Verify the positive case — `_validate_context_node` returns `{"fallback_triggered": False}` when context has at least one safe exercise.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_validate_context_passes_when_safe_exercises_present -v
  ```
- **Expected Result**: `PASSED` — `result["fallback_triggered"]` is `False`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-005: Happy path — graph returns a `WorkoutRecommendation`

- **Description**: Verify that when the graph is invoked with a valid context (non-empty `safe_exercises`), the mocked LLM is called via `with_structured_output(WorkoutRecommendation)` and the result contains a `recommendation` with at least one exercise.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_generate_workout_returns_recommendation -v
  ```
- **Expected Result**: `PASSED` — `result["recommendation"]` is not None, and `recommendation.exercises` (or `recommendation["exercises"]`) has length ≥ 1.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-006: Fallback path — `generate_workout` node never called when `fallback_triggered`

- **Description**: Verify that the conditional edge routes to `END` when `fallback_triggered=True`, meaning `ChatAnthropic` is never instantiated and the LLM is never called.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_generate_workout_skips_generation_when_fallback_triggered -v
  ```
- **Expected Result**: `PASSED` — `mock_chat_cls.assert_not_called()` holds; `result["fallback_triggered"]` is `True`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `validate_context` triggers fallback when `context` is `None`

- **Description**: Verify that `_validate_context_node` handles a `None` context (missing key) gracefully, returning `{"fallback_triggered": True}` without raising an exception. This covers the case where upstream graph nodes omit the context entirely.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_generation_graph.py::test_validate_context_triggers_fallback_when_context_is_none -v
  ```
- **Expected Result**: `PASSED` — `result["fallback_triggered"]` is `True`, no `KeyError` or `TypeError` raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: LLM error path — graph returns empty recommendation with error field

- **Description**: Verify that when `_generate_workout_node` catches an exception from the LLM (e.g., API error), it returns a fallback `WorkoutRecommendation` with `exercises=[]` and `overall_reasoning="Generation failed due to an error."`, plus a populated `error` field. The graph must not raise.
- **Steps**:
  1. Run the command below to execute a one-off smoke test via the Python REPL
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from app.kg.generation_graph import build_generation_graph, WorkoutRecommendation

async def run():
    with patch('app.kg.generation_graph.ChatAnthropic') as mock_cls:
        mock_llm = MagicMock()
        mock_llm_ws = MagicMock()
        mock_llm_ws.ainvoke = AsyncMock(side_effect=RuntimeError('upstream timeout'))
        mock_llm.with_structured_output.return_value = mock_llm_ws
        mock_cls.return_value = mock_llm
        graph = build_generation_graph()
        result = await graph.ainvoke({'member_id': 'm1', 'query': 'leg day', 'context': {'member_profile': {'id': 'm1'}, 'safe_exercises': [{'id': 'ex-0', 'name': 'Squat', 'muscle_groups': ['quads'], 'equipment_required': ['barbell']}], 'preferred_exercises': [], 'vector_hits': [], 'token_counts': {'member_profile': 10, 'safe_exercises': 20, 'preferred_exercises': 0, 'vector_hits': 0, 'total': 30}}})
        rec = result.get('recommendation')
        assert rec is not None, 'recommendation must be set even on error'
        exercises = rec.exercises if hasattr(rec, 'exercises') else rec.get('exercises', None)
        assert exercises == [], f'expected empty exercises list, got {exercises}'
        assert result.get('error') is not None, 'error field must be populated'
        print('PASS: LLM error path returns empty recommendation with error field')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `PASS: LLM error path returns empty recommendation with error field` with no exception raised. `recommendation.exercises` is `[]` and `result["error"]` contains the error string.
- [FAIL: auto-judge: assertion stale — implementation deliberately evolved: on LLM error, fallback node now returns safe_exercises instead of exercises=[]; error field is populated; graph does not raise] <!-- 2026-06-07 -->

---

## Integration Tests

### UAT-INT-001: Module imports cleanly and graph wires all 3 nodes

- **Description**: Verify that `generation_graph.py` is importable without errors, all 3 nodes (`validate_context`, `generate_workout`, `format_response`) are wired in the compiled graph, and the entry point is `validate_context`. This catches misconfigured StateGraph topology.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "
from app.kg.generation_graph import build_generation_graph, WorkoutRecommendation, RecommendedExercise, GenerationState
graph = build_generation_graph()
assert hasattr(graph, 'ainvoke'), 'graph must have ainvoke'
print('PASS: module imports and graph compiles')
print('WorkoutRecommendation fields:', list(WorkoutRecommendation.model_fields.keys()))
print('RecommendedExercise fields:', list(RecommendedExercise.model_fields.keys()))
"
  ```
- **Expected Result**: Prints `PASS: module imports and graph compiles`. `WorkoutRecommendation` fields include `exercises`, `overall_reasoning`, `member_id`, `skipped_exercise_ids`. `RecommendedExercise` fields include `exercise_id`, `name`, `sets`, `reps`, `duration_seconds`, `weight_kg`, `reasoning`. No `ImportError` or `AttributeError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: Roadmap updated with task link for TASK-060

- **Description**: Verify the roadmap file `.docs/roadmaps/004-knowledge-graph-coaching-system.md` references TASK-060 and the generation sub-graph, as required by the acceptance criteria.
- **Steps**:
  1. Open `.docs/roadmaps/004-knowledge-graph-coaching-system.md`
  2. Search for `060` or `generation-agent-subgraph` within the file
- **Expected Result**: The roadmap contains a link to `../tasks/060-generation-agent-subgraph.md` (or similar) and does not show an inline placeholder for the generation sub-graph task.
- [x] Pass <!-- 2026-06-07 -->
