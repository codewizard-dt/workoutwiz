# UAT: Graph Traversal Queries — Injury-Aware Exercise Filtering

> **Source task**: [`.docs/tasks/completed/056-injury-traversal-queries.md`](../tasks/completed/056-injury-traversal-queries.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python virtual environment activated with backend dependencies installed (`pip install -e ".[dev]"` from `backend/`)
- [ ] `pytest-asyncio` installed and `asyncio_mode = "auto"` set in `backend/pyproject.toml` under `[tool.pytest.ini_options]`
- [ ] `neo4j` Python package installed (dependency from TASK-041/042)
- [ ] `backend/app/knowledge_graph/traversal.py` exists with `get_contraindicated_exercise_ids`, `get_safe_exercises`, and `get_member_profile`
- [ ] `backend/tests/knowledge_graph/test_traversal.py` exists with 8 test functions

---

## API Tests

> These functions are pure-Python async library functions (not HTTP endpoints). Tests are executed via pytest with AsyncMock — no running server or live Neo4j connection required.

### UAT-API-001: `get_contraindicated_exercise_ids` returns a set of exercise IDs
- **Function**: `get_contraindicated_exercise_ids(member_id, driver)`
- **Description**: Verify the function returns a `set[str]` containing the exercise IDs returned by the Cypher query, and that it is genuinely a `set` (not a list).
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_contraindicated_ids_returns_set -v
  ```
- **Expected Result**: `1 passed` — function returns `{"ex-1", "ex-2"}` which is a `set`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: `get_contraindicated_exercise_ids` returns empty set when member has no injuries
- **Function**: `get_contraindicated_exercise_ids(member_id, driver)`
- **Description**: Verify the function returns an empty `set()` (not `[]`) when the Cypher query returns no rows.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_contraindicated_ids_empty_when_no_injuries -v
  ```
- **Expected Result**: `1 passed` — function returns `set()` not `[]`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: `get_contraindicated_exercise_ids` deduplicates via set construction
- **Function**: `get_contraindicated_exercise_ids(member_id, driver)`
- **Description**: Verify that even if the mock returns duplicate `exercise_id` values (simulating a Cypher DISTINCT miss), the Python set constructor deduplicates them.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_contraindicated_ids_deduplicates -v
  ```
- **Expected Result**: `1 passed` — result is `{"ex-1"}` with `len == 1`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: `get_safe_exercises` returns a list of dicts with required keys
- **Function**: `get_safe_exercises(member_id, driver)`
- **Description**: Verify the function returns a `list` of dicts each containing keys: `id`, `name`, `muscle_groups`, `movement_patterns`, `equipment_required`, `priority_tier`, `is_reps`, `is_duration`, `supports_weight`.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_safe_exercises_returns_list_of_dicts -v
  ```
- **Expected Result**: `1 passed` — list of 2 dicts, each with `id`, `name`, `muscle_groups` keys present
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: `get_safe_exercises` returns empty list when all exercises are contraindicated
- **Function**: `get_safe_exercises(member_id, driver)`
- **Description**: Verify the function returns `[]` (empty list) when the Cypher query returns no rows.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_safe_exercises_empty_when_all_contraindicated -v
  ```
- **Expected Result**: `1 passed` — function returns `[]`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: `get_member_profile` returns a dict with member profile fields
- **Function**: `get_member_profile(member_id, driver)`
- **Description**: Verify the function returns a dict with keys `id`, `name`, `goals`, `equipment`, `availability`, `fitness_level`, `injury_names` when the member exists.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_member_profile_returns_dict -v
  ```
- **Expected Result**: `1 passed` — result is not `None` and `result["id"] == "member-1"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-007: `get_member_profile` returns `None` when member is not found
- **Function**: `get_member_profile(member_id, driver)`
- **Description**: Verify the function returns `None` (not an exception) when `result.single()` returns `None`.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_member_profile_returns_none_when_not_found -v
  ```
- **Expected Result**: `1 passed` — function returns `None`
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-008: `get_member_profile` passes `member_id` as a parameterized keyword argument
- **Function**: `get_member_profile(member_id, driver)`
- **Description**: Verify the Cypher query is called with `member_id` as a keyword parameter (not interpolated into the string), satisfying the acceptance criterion that all queries use parameterized variables.
- **Steps**:
  1. Run the pytest command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py::test_get_member_profile_passes_member_id_as_parameter -v
  ```
- **Expected Result**: `1 passed` — `session.run` call_args contains `"member-abc"`
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Full test suite — all 8 tests pass with no live Neo4j connection
- **Scenario**: Run the entire `test_traversal.py` file to confirm all mocked async tests pass together and none require a live database connection.
- **Steps**:
  1. Ensure no Neo4j instance is running (or do nothing — mocks bypass any connection)
  2. Run the command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_traversal.py -v
  ```
- **Expected Result**: `8 passed` with `0 failed`, `0 errors`. Output shows all 8 test names.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Cypher queries use `$member_id` parameter — no string interpolation
- **Scenario**: Verify the Cypher query strings in `traversal.py` use `$member_id` parameterization, not f-strings or `.format()` calls.
- **Steps**:
  1. Run the command below to check the source for parameterized variables
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && python -c "import ast, sys; src=open('backend/app/knowledge_graph/traversal.py').read(); assert '$member_id' in src and 'f\"' not in src and '.format(' not in src; print('OK: parameterized queries confirmed')"
  ```
- **Expected Result**: Prints `OK: parameterized queries confirmed` with exit code 0
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: `_SAFE_EXERCISES_QUERY` orders by `priority_tier ASC, name ASC`
- **Scenario**: Verify the ordering clause is present in the query — a requirement per acceptance criteria.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz && python -c "from backend.app.knowledge_graph.traversal import _SAFE_EXERCISES_QUERY; assert 'ORDER BY e.priority_tier ASC, e.name ASC' in _SAFE_EXERCISES_QUERY; print('OK: ordering clause confirmed')"
  ```
- **Expected Result**: Prints `OK: ordering clause confirmed` with exit code 0
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Module imports cleanly and all three public functions are importable
- **Components**: `backend/app/knowledge_graph/traversal.py`, Python import system
- **Flow**: Import the module and confirm the three public API functions are present and callable.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import get_contraindicated_exercise_ids, get_safe_exercises, get_member_profile; import inspect; assert all(inspect.iscoroutinefunction(f) for f in [get_contraindicated_exercise_ids, get_safe_exercises, get_member_profile]); print('OK: all three async functions importable')"
  ```
- **Expected Result**: Prints `OK: all three async functions importable` with exit code 0
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: `get_contraindicated_exercise_ids` return type is `set`, `get_safe_exercises` return type is `list`
- **Components**: Both traversal functions, their type contracts
- **Flow**: Run both functions with a mocked driver inline and assert return types match the acceptance criteria.
- **Steps**:
  1. From the `backend/` directory, run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.knowledge_graph.traversal import get_contraindicated_exercise_ids, get_safe_exercises

def make_driver(data):
    r = AsyncMock(); r.data = AsyncMock(return_value=data)
    s = AsyncMock(); s.run = AsyncMock(return_value=r)
    cm = AsyncMock(); cm.__aenter__ = AsyncMock(return_value=s); cm.__aexit__ = AsyncMock(return_value=False)
    d = MagicMock(); d.session = MagicMock(return_value=cm)
    return d

async def run():
    ids = await get_contraindicated_exercise_ids('m1', make_driver([{'exercise_id':'x'}]))
    exs = await get_safe_exercises('m1', make_driver([{'id':'x','name':'Push-up','muscle_groups':[],'movement_patterns':[],'equipment_required':[],'priority_tier':1,'is_reps':True,'is_duration':False,'supports_weight':False}]))
    assert isinstance(ids, set), f'expected set, got {type(ids)}'
    assert isinstance(exs, list), f'expected list, got {type(exs)}'
    print('OK: return types correct')

asyncio.run(run())
"
  ```
- **Expected Result**: Prints `OK: return types correct` with exit code 0
- [x] Pass <!-- 2026-06-06 -->
