# UAT: Preference/Feedback Traversal — Surface Highly-Rated and Performed Exercises

> **Source task**: [`.docs/tasks/completed/057-preference-feedback-traversal.md`](../tasks/completed/057-preference-feedback-traversal.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python virtual environment activated in `backend/`
- [ ] `pytest` and `pytest-asyncio` installed (`pip install -e ".[dev]"` or equivalent)
- [ ] `backend/app/knowledge_graph/traversal.py` exists with all five traversal functions

---

## Unit Tests

### UAT-UNIT-001: Run the full knowledge_graph test suite
- **Description**: Verify all 14 unit tests in `backend/tests/knowledge_graph/test_traversal.py` pass — 8 from TASK-056 plus 6 new ones from this task.
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/ -v
  ```
- **Expected Result**: All 14 tests collected and pass with `0 failed`. Exit code 0. Output includes `test_get_preferred_exercises_returns_list PASSED`, `test_get_preferred_exercises_empty_when_no_feedback PASSED`, `test_get_preferred_exercises_uses_min_rating_param PASSED`, `test_get_performed_exercises_returns_list PASSED`, `test_get_performed_exercises_empty_when_no_history PASSED`, `test_get_performed_exercises_uses_limit_param PASSED`.
- [x] Pass <!-- 2026-06-06 -->

---

## Static / Structural Tests

### UAT-STATIC-001: `traversal.py` exports all five traversal functions
- **Description**: Verify the module contains all five functions required by the acceptance criteria.
- **Steps**:
  1. Run the command below — it imports the module and prints the five symbol names
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import get_contraindicated_exercise_ids, get_safe_exercises, get_member_profile, get_preferred_exercises, get_performed_exercises; print('all five functions present')"
  ```
- **Expected Result**: Prints `all five functions present` with exit code 0. No `ImportError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-002: `get_preferred_exercises` Cypher uses parameterized `$min_rating`
- **Description**: Verify the query uses a named parameter (no hard-coded integer) for the rating threshold.
- **Steps**:
  1. Run the command below to inspect the query constant
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PREFERRED_EXERCISES_QUERY; assert '$min_rating' in _PREFERRED_EXERCISES_QUERY, 'FAIL: $min_rating not parameterized'; print('OK: $min_rating is parameterized')"
  ```
- **Expected Result**: Prints `OK: $min_rating is parameterized`. No `AssertionError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-003: `get_preferred_exercises` Cypher uses correct edge label `[:RATED]`
- **Description**: Verify the preferred-exercises query traverses `(Member)-[:RATED]->(Exercise)` as confirmed in the schema (direct relationship, no intermediate FeedbackEvent node).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PREFERRED_EXERCISES_QUERY; assert ':RATED' in _PREFERRED_EXERCISES_QUERY, 'FAIL: :RATED edge not found'; print('OK: :RATED edge present')"
  ```
- **Expected Result**: Prints `OK: :RATED edge present`. No `AssertionError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-004: `get_preferred_exercises` Cypher returns `avg_rating` and `feedback_count`
- **Description**: Verify the query aggregates rating and count (as required by the return-shape spec).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PREFERRED_EXERCISES_QUERY; assert 'avg_rating' in _PREFERRED_EXERCISES_QUERY and 'feedback_count' in _PREFERRED_EXERCISES_QUERY, 'FAIL: missing aggregates'; print('OK: avg_rating and feedback_count present')"
  ```
- **Expected Result**: Prints `OK: avg_rating and feedback_count present`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-005: `get_performed_exercises` Cypher uses parameterized `$limit`
- **Description**: Verify the performed-exercises query uses `$limit` parameter (no hard-coded integer).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PERFORMED_EXERCISES_QUERY; assert '$limit' in _PERFORMED_EXERCISES_QUERY, 'FAIL: $limit not parameterized'; print('OK: $limit is parameterized')"
  ```
- **Expected Result**: Prints `OK: $limit is parameterized`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-006: `get_performed_exercises` Cypher uses `DISTINCT` and `last_performed_at`
- **Description**: Verify the query returns distinct exercises ordered by recency.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PERFORMED_EXERCISES_QUERY; assert 'DISTINCT' in _PERFORMED_EXERCISES_QUERY and 'last_performed_at' in _PERFORMED_EXERCISES_QUERY, 'FAIL: DISTINCT or last_performed_at missing'; print('OK: DISTINCT and last_performed_at present')"
  ```
- **Expected Result**: Prints `OK: DISTINCT and last_performed_at present`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-007: `get_performed_exercises` Cypher traverses via `[:PERFORMED]` and `[:INCLUDED]`
- **Description**: Verify the performed-exercises query uses the schema-confirmed path `(Member)-[:PERFORMED]->(WorkoutSession)-[:INCLUDED]->(Exercise)`.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PERFORMED_EXERCISES_QUERY; assert ':PERFORMED' in _PERFORMED_EXERCISES_QUERY and ':INCLUDED' in _PERFORMED_EXERCISES_QUERY, 'FAIL: traversal path wrong'; print('OK: :PERFORMED and :INCLUDED edges present')"
  ```
- **Expected Result**: Prints `OK: :PERFORMED and :INCLUDED edges present`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `get_preferred_exercises` default `min_rating` is 4
- **Description**: Verify the function signature defaults `min_rating` to 4, not any other value.
- **Steps**:
  1. Run the command below to inspect the function's default parameter
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "import inspect; from app.knowledge_graph.traversal import get_preferred_exercises; sig = inspect.signature(get_preferred_exercises); assert sig.parameters['min_rating'].default == 4, f'FAIL: default is {sig.parameters[\"min_rating\"].default}'; print('OK: min_rating default is 4')"
  ```
- **Expected Result**: Prints `OK: min_rating default is 4`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: `get_performed_exercises` default `limit` is 20
- **Description**: Verify the function signature defaults `limit` to 20 (the context-budget cap in the spec).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "import inspect; from app.knowledge_graph.traversal import get_performed_exercises; sig = inspect.signature(get_performed_exercises); assert sig.parameters['limit'].default == 20, f'FAIL: default is {sig.parameters[\"limit\"].default}'; print('OK: limit default is 20')"
  ```
- **Expected Result**: Prints `OK: limit default is 20`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: `get_preferred_exercises` `ORDER BY` sorts by `avg_rating DESC` then name `ASC`
- **Description**: Verify the Cypher sort order matches the spec (highest-rated first, ties broken alphabetically).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PREFERRED_EXERCISES_QUERY; q = _PREFERRED_EXERCISES_QUERY; assert 'avg_rating DESC' in q and 'e.name ASC' in q, 'FAIL: sort order wrong'; print('OK: ORDER BY avg_rating DESC, e.name ASC')"
  ```
- **Expected Result**: Prints `OK: ORDER BY avg_rating DESC, e.name ASC`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-004: `get_performed_exercises` `ORDER BY` sorts by `last_performed_at DESC`
- **Description**: Verify the query sorts most-recent-first.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph.traversal import _PERFORMED_EXERCISES_QUERY; assert 'last_performed_at DESC' in _PERFORMED_EXERCISES_QUERY, 'FAIL: sort order wrong'; print('OK: ORDER BY last_performed_at DESC')"
  ```
- **Expected Result**: Prints `OK: ORDER BY last_performed_at DESC`.
- [x] Pass <!-- 2026-06-06 -->
