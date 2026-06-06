# UAT: Feedback Ingestion — FeedbackEvent Nodes + Edges in Neo4j

> **Source task**: [`.docs/tasks/053-feedback-ingestion-neo4j.md`](../tasks/053-feedback-ingestion-neo4j.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python virtual environment activated (`source .venv/bin/activate` from `backend/`)
- [ ] `backend/` is the working directory for all `python -m` commands
- [ ] `pytest` and `pytest-asyncio` are installed (`pip install -e ".[dev]"` from `backend/`)
- [ ] Environment variables set: `DATABASE_URL`, `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD` (use `set -a && source ../.env && set +a` from `backend/`)
- [ ] `backend/app/knowledge_graph/ingest_feedback.py` exists

---

## Static / Import Tests

### UAT-STATIC-001: Module Is Importable Without Error

- **Description**: Verify `ingest_all_feedback` can be imported from `app.knowledge_graph.ingest_feedback` with no syntax or import errors.
- **Steps**:
  1. From the `backend/` directory with the virtualenv active, run the command below.
- **Command**:
  ```bash
  python -c 'from app.knowledge_graph.ingest_feedback import ingest_all_feedback; print(type(ingest_all_feedback))'
  ```
- **Expected Result**: Prints `<class 'function'>` with exit code 0. No `ImportError`, `ModuleNotFoundError`, or `SyntaxError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-002: Return Type Annotation Is `int`

- **Description**: Verify `ingest_all_feedback` is annotated to return `int` (required by the task's acceptance criteria).
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'import inspect, typing; from app.knowledge_graph.ingest_feedback import ingest_all_feedback; hints = typing.get_type_hints(ingest_all_feedback); print(hints.get("return"))'
  ```
- **Expected Result**: Prints `<class 'int'>` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-003: All Three Context-Type Cypher Constants Are Present

- **Description**: Verify the module defines the expected Cypher constants for all three `context_type` branches: `_EDGE_EXERCISE_ABOUT`, `_EDGE_MEMBER_RATED`, `_EDGE_WORKOUT_ABOUT`, and `_EDGE_SET_ABOUT`.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'import app.knowledge_graph.ingest_feedback as m; names = ["_EDGE_EXERCISE_ABOUT","_EDGE_MEMBER_RATED","_EDGE_WORKOUT_ABOUT","_EDGE_SET_ABOUT"]; missing = [n for n in names if not hasattr(m, n)]; print("MISSING:", missing) if missing else print("ALL PRESENT")'
  ```
- **Expected Result**: Prints `ALL PRESENT` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-STATIC-004: `__main__` Entry Point Uses `asyncio.run`

- **Description**: Verify the `__main__` block in `ingest_feedback.py` calls `asyncio.run(...)`, satisfying the task requirement.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'import ast, pathlib; src = pathlib.Path("app/knowledge_graph/ingest_feedback.py").read_text(); tree = ast.parse(src); calls = [ast.dump(n) for n in ast.walk(tree) if isinstance(n, ast.Call)]; found = any("asyncio" in c and "run" in c for c in calls); print("asyncio.run FOUND" if found else "asyncio.run MISSING")'
  ```
- **Expected Result**: Prints `asyncio.run FOUND` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

---

## Unit Tests

### UAT-UNIT-001: All Four Unit Tests Pass

- **Description**: Verify the four unit tests in `backend/tests/knowledge_graph/test_ingest_feedback.py` all pass — no real Neo4j or PostgreSQL connections required.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -m pytest tests/knowledge_graph/test_ingest_feedback.py -v
  ```
- **Expected Result**: Exit code 0. All four tests pass:
  - `test_exercise_context_writes_rated_edge` — PASSED
  - `test_workout_context_writes_about_session` — PASSED
  - `test_set_context_merges_set_node` — PASSED
  - `test_idempotent_merge_on_match` — PASSED
  No failures, no errors, no skips.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: EXERCISE Context Writes Both `ABOUT→Exercise` and `RATED` Edge

- **Description**: Confirm that the `test_exercise_context_writes_rated_edge` test specifically asserts that both `[:ABOUT]->(e)` and `[:RATED]->(e)` Cypher patterns are sent to the Neo4j session mock when `context_type=EXERCISE`.
- **Steps**:
  1. From `backend/`, run the command below targeting only this test.
- **Command**:
  ```bash
  python -m pytest tests/knowledge_graph/test_ingest_feedback.py::test_exercise_context_writes_rated_edge -v
  ```
- **Expected Result**: Exit code 0. Test PASSED. This confirms the `EXERCISE` branch writes the denormalized `(Member)-[:RATED]->(Exercise)` edge in addition to `(FeedbackEvent)-[:ABOUT]->(Exercise)`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: WORKOUT Context Writes `ABOUT→WorkoutSession` and No `RATED` Edge

- **Description**: Confirm that the `WORKOUT` context branch writes only the `[:ABOUT]->(ws)` edge and does NOT emit a `[:RATED]->` Cypher pattern.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -m pytest tests/knowledge_graph/test_ingest_feedback.py::test_workout_context_writes_about_session -v
  ```
- **Expected Result**: Exit code 0. Test PASSED.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: SET Context Merges a `Set` Node

- **Description**: Confirm that the `SET` context branch emits `MERGE (s:Set {id: ...})` Cypher.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -m pytest tests/knowledge_graph/test_ingest_feedback.py::test_set_context_merges_set_node -v
  ```
- **Expected Result**: Exit code 0. Test PASSED.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-005: Idempotent Re-Run Does Not Produce Bare `CREATE`

- **Description**: Confirm that running `_upsert_feedback_batch` twice with the same row never emits a bare `CREATE` statement — all writes use `MERGE` with `ON MATCH SET`.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -m pytest tests/knowledge_graph/test_ingest_feedback.py::test_idempotent_merge_on_match -v
  ```
- **Expected Result**: Exit code 0. Test PASSED. The assertion `bare_create = [q for q in queries if q.strip().startswith("CREATE")]` is empty, confirming all Cypher uses `MERGE`.
- [x] Pass <!-- 2026-06-06 -->

---

## Schema Tests

### UAT-SCHEMA-001: `Set` Uniqueness Constraint Exists in `init_schema.py`

- **Description**: Verify that the `CONSTRAINTS` list in `init_schema.py` includes a `Set.id IS UNIQUE` constraint with the `IF NOT EXISTS` guard, as required by the task.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'from app.knowledge_graph.init_schema import CONSTRAINTS; match = [c for c in CONSTRAINTS if "Set" in c and "s.id IS UNIQUE" in c and "IF NOT EXISTS" in c]; print("SET CONSTRAINT FOUND:", len(match), "entry/entries") if match else print("SET CONSTRAINT MISSING")'
  ```
- **Expected Result**: Prints `SET CONSTRAINT FOUND: 1 entry/entries` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: `ingest_all_feedback` Is Wired into the Seed Entry Point

- **Description**: Verify that `app.knowledge_graph.seed` imports `ingest_all_feedback` and calls it in its `main()` flow, satisfying the task's Step 3 acceptance criteria.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'import inspect; from app.knowledge_graph import seed; src = inspect.getsource(seed); print("ingest_all_feedback CALLED" if "ingest_all_feedback" in src else "ingest_all_feedback MISSING")'
  ```
- **Expected Result**: Prints `ingest_all_feedback CALLED` with exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: `python -m app.knowledge_graph.ingest_feedback` Runs Without Import Errors (Dry Run)

- **Description**: Verify the `__main__` block can be entered without import errors. With no real database connection, the script may exit with a connection error — that is acceptable. What matters is no `ImportError`, `ModuleNotFoundError`, or `SyntaxError`.
- **Steps**:
  1. From `backend/`, run the command below. The `|| true` ensures the shell returns 0 regardless of the connection error so we can inspect stderr.
  2. Confirm stderr contains no `ImportError` or `ModuleNotFoundError`.
- **Command**:
  ```bash
  python -m app.knowledge_graph.ingest_feedback 2>&1 | head -5
  ```
- **Expected Result**: The first few lines of output show either `Ingested N FeedbackEvent nodes` (if a live DB is available) or a database/Neo4j connection error. No `ImportError`, `ModuleNotFoundError`, or `SyntaxError` appears in the output.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: `python -m app.knowledge_graph.seed` Runs Without Import Errors (Dry Run)

- **Description**: Verify `seed.py` can be invoked as a module entry point without import or syntax errors (dry run — a connection error to Postgres/Neo4j is acceptable).
- **Steps**:
  1. From `backend/`, run the command below.
  2. Confirm no `ImportError`, `ModuleNotFoundError`, or `SyntaxError` appears.
- **Command**:
  ```bash
  python -m app.knowledge_graph.seed 2>&1 | head -5
  ```
- **Expected Result**: Output begins with either a seed progress log line or a DB connection error. No Python import or syntax errors.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `_upsert_feedback_batch` Handles Empty Row List Without Error

- **Description**: Verify that calling `_upsert_feedback_batch` with an empty list produces no errors and does not attempt any Neo4j writes.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c '
import asyncio
from unittest.mock import AsyncMock, MagicMock
from app.knowledge_graph.ingest_feedback import _upsert_feedback_batch

async def run():
    session = MagicMock()
    session.execute_write = AsyncMock()
    await _upsert_feedback_batch(session, [])
    print("execute_write call count:", session.execute_write.call_count)

asyncio.run(run())
'
  ```
- **Expected Result**: Prints `execute_write call count: 0` with exit code 0. No exception raised.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: `context_type` Value Is Serialised as String in FeedbackEvent Node

- **Description**: Verify that the Cypher sent to Neo4j stores `context_type` as a plain string (e.g., `"exercise"`) not as an enum object, confirming the `str(_row.context_type)` coercion in `_upsert_feedback_batch`.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c '
import asyncio, uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock
from app.models.feedback import ExerciseFeedback, FeedbackContextType
from app.knowledge_graph.ingest_feedback import _upsert_feedback_batch

recorded = []

async def fake_execute_write(fn):
    class FakeTx:
        async def run(self, q, **kw):
            recorded.append((q, kw))
    await fn(FakeTx())

async def run():
    row = MagicMock(spec=ExerciseFeedback)
    row.id = uuid.uuid4()
    row.user_id = uuid.uuid4()
    row.exercise_id = uuid.uuid4()
    row.workout_id = None
    row.workout_set_id = None
    row.rating = 3
    row.feedback_text = None
    row.context_type = FeedbackContextType.EXERCISE
    row.created_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    session = MagicMock()
    session.execute_write = fake_execute_write
    await _upsert_feedback_batch(session, [row])
    ct_values = [kw.get("context_type") for q, kw in recorded if "context_type" in kw]
    print("context_type param type:", type(ct_values[0]).__name__ if ct_values else "NOT FOUND")
    print("context_type value:", ct_values[0] if ct_values else "NOT FOUND")

asyncio.run(run())
'
  ```
- **Expected Result**: Prints `context_type param type: str` and `context_type value: exercise` (or `FeedbackContextType.EXERCISE` if StrEnum serialises as its string value). Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: `FeedbackEvent` Cypher Uses `MERGE` with `ON CREATE SET` and `ON MATCH SET`

- **Description**: Verify the `_MERGE_FEEDBACK_EVENT` Cypher constant contains both `ON CREATE SET` and `ON MATCH SET` clauses, confirming idempotency at the node level.
- **Steps**:
  1. From `backend/`, run the command below.
- **Command**:
  ```bash
  python -c 'from app.knowledge_graph.ingest_feedback import _MERGE_FEEDBACK_EVENT as q; print("ON CREATE SET:", "ON CREATE SET" in q); print("ON MATCH SET:", "ON MATCH SET" in q); print("MERGE:", q.strip().startswith("MERGE"))'
  ```
- **Expected Result**: All three lines print `True`:
  ```
  ON CREATE SET: True
  ON MATCH SET: True
  MERGE: True
  ```
- [x] Pass <!-- 2026-06-06 -->
