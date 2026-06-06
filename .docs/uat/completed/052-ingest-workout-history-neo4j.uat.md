# UAT: Workout History Ingestion into Neo4j

> **Source task**: [`.docs/tasks/052-ingest-workout-history-neo4j.md`](../tasks/052-ingest-workout-history-neo4j.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Docker is running and `docker compose up neo4j` has been executed from the project root
- [ ] Neo4j is healthy: `docker compose ps neo4j` shows `healthy` (or wait for the healthcheck to pass — up to 50 seconds)
- [ ] Backend Python environment is activated: `cd backend && source .venv/bin/activate` (or equivalent)
- [ ] Environment variables are loaded: `set -a && source ../.env && set +a` from `backend/`
- [ ] Neo4j schema has been initialised (task 044 prerequisite): the `Member` and `Exercise` constraints/indexes exist
- [ ] `backend/app/knowledge_graph/ingest_workout_history.py` exists (task deliverable)

---

## Unit Tests

### UAT-UNIT-001: All four unit tests pass

- **Description**: Run the full unit-test suite for the ingestion module. All four tests must pass using mocked neo4j objects — no live Neo4j connection required.
- **Steps**:
  1. Activate the backend virtual environment and change to `backend/`
  2. Run the pytest command below as-is
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_ingest_workout_history.py -v
  ```
- **Expected Result**: All 4 tests collected and pass:
  - `test_ingest_empty_raises_value_error` — PASSED
  - `test_merge_session_cypher_calls` — PASSED
  - `test_ingest_returns_count` — PASSED
  - `test_idempotent_cypher_uses_merge` — PASSED

  Exit code 0; no failures.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Empty sessions list raises ValueError

- **Scenario**: Passing an empty list to `ingest_workout_history` must raise `ValueError` to guard against silent no-ops from bad upstream data.
- **Description**: Verifies the guard clause `if not sessions: raise ValueError("sessions list must not be empty")` fires correctly. Covered by `test_ingest_empty_raises_value_error` but cross-verified here at the Python REPL level.
- **Steps**:
  1. From `backend/` with the venv active and env loaded, launch a Python shell:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph import ingest_workout_history; from unittest.mock import MagicMock; ingest_workout_history(MagicMock(), [])"
     ```
- **Expected Result**: Process exits with a `ValueError` traceback containing the message `sessions list must not be empty`. Exit code non-zero.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: All Cypher statements use MERGE (idempotency guarantee)

- **Scenario**: Re-running `_merge_session` with the same session dict must not create duplicate nodes or edges — verified by inspecting every `tx.run` call and asserting `MERGE` is present.
- **Description**: Mirrors `test_idempotent_cypher_uses_merge`. Covered by unit tests; this entry documents the requirement so it is visible in the UAT record.
- **Steps**:
  1. Confirm `test_idempotent_cypher_uses_merge` passed in UAT-UNIT-001 above.
  2. Optionally, run the single test in isolation:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_ingest_workout_history.py::test_idempotent_cypher_uses_merge -v
     ```
- **Expected Result**: `test_idempotent_cypher_uses_merge` PASSED. Every Cypher string passed to `tx.run` contains the keyword `MERGE`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Session with no exercises does not crash

- **Scenario**: A session dict with `"exercises": []` is valid input. No INCLUDED edges should be created, but the WorkoutSession node and PERFORMED edge must still be written.
- **Description**: The `__main__` smoke session uses `exercises: []` — this edge case must not raise. Verifies `for exercise in session.get("exercises", [])` handles an empty list gracefully.
- **Steps**:
  1. Run the command:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "
from unittest.mock import MagicMock
from app.knowledge_graph.ingest_workout_history import _merge_session
import uuid
from datetime import datetime, timezone
tx = MagicMock()
session = {'id': str(uuid.uuid4()), 'member_id': str(uuid.uuid4()), 'started_at': datetime.now(tz=timezone.utc).isoformat(), 'ended_at': None, 'exercises': []}
_merge_session(tx, session)
print('tx.run call count:', tx.run.call_count)
assert tx.run.call_count == 2, f'Expected 2 calls (node + PERFORMED), got {tx.run.call_count}'
print('PASS')
"
     ```
- **Expected Result**: Prints `tx.run call count: 2` and `PASS`. No exception raised. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Module is importable from app.knowledge_graph

- **Description**: Verifies that `ingest_workout_history` is exported from `backend/app/knowledge_graph/__init__.py` via `__all__` and can be imported with `from app.knowledge_graph import ingest_workout_history`.
- **Steps**:
  1. Run the command:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "from app.knowledge_graph import ingest_workout_history; print('imported:', ingest_workout_history.__module__)"
     ```
- **Expected Result**: Prints `imported: app.knowledge_graph.ingest_workout_history`. Exit code 0. No `ImportError`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: seed_workout_history_neo4j delegates to ingest_workout_history (no inline Cypher)

- **Description**: Verifies that `seed.py` no longer contains inline Cypher for `WorkoutSession`, `PERFORMED`, or `INCLUDED` — all ingestion is delegated to `ingest_workout_history`. Confirms no code regression in the delegation refactor.
- **Steps**:
  1. Run the pattern search:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -c "
import ast, pathlib
src = pathlib.Path('app/knowledge_graph/seed.py').read_text()
assert 'WorkoutSession' not in src or 'ingest_workout_history' in src, 'seed.py has WorkoutSession Cypher but does not call ingest_workout_history'
assert 'MERGE (ws:WorkoutSession' not in src, 'seed.py still contains inline WorkoutSession MERGE Cypher'
assert 'MERGE (m)-[:PERFORMED]' not in src, 'seed.py still contains inline PERFORMED MERGE Cypher'
assert 'MERGE (ws)-[r:INCLUDED]' not in src, 'seed.py still contains inline INCLUDED MERGE Cypher'
print('PASS: seed.py delegates to ingest_workout_history, no inline Cypher')
"
     ```
- **Expected Result**: Prints `PASS: seed.py delegates to ingest_workout_history, no inline Cypher`. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: Module runs as __main__ against live Neo4j (smoke test)

- **Description**: Verifies the `__main__` entry point connects to Neo4j, calls `ingest_workout_history` with a synthetic smoke session (no exercises), and exits cleanly. Requires a running Neo4j instance. A `Member` node matching the smoke session's random `member_id` does NOT need to exist — the PERFORMED edge `MATCH` will simply not create an edge, but the `WorkoutSession` node will be MERGEd successfully.
- **Prerequisites**: Neo4j running (see Prerequisites section above), env vars loaded.
- **Steps**:
  1. From `backend/` with venv active and env loaded, run:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m app.knowledge_graph.ingest_workout_history
     ```
- **Expected Result**: Process exits with code 0. Log output contains a line matching `Ingested 1 workout sessions into Neo4j.` No exception or traceback.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-004: ingest_workout_history returns correct count

- **Description**: Verifies the function return value equals the number of session dicts passed in — confirmed by `test_ingest_returns_count`, cross-verified here.
- **Steps**:
  1. Confirm `test_ingest_returns_count` passed in UAT-UNIT-001.
  2. Optionally, run in isolation:
     ```bash
     cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/knowledge_graph/test_ingest_workout_history.py::test_ingest_returns_count -v
     ```
- **Expected Result**: `test_ingest_returns_count` PASSED. The function returns `1` when called with a list of one session dict.
- [x] Pass <!-- 2026-06-06 -->
