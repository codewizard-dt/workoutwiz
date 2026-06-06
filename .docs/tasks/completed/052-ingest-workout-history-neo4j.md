# 052 — Workout history ingestion into Neo4j

> **Depends on**: [044-neo4j-schema-init-script](completed/044-neo4j-schema-init-script.md), [042-neo4j-python-dependencies](completed/042-neo4j-python-dependencies.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](completed/033-critical-path-router-test.md), [034-critical-path-generator-test](completed/034-critical-path-generator-test.md)

## Objective

Create `backend/app/knowledge_graph/ingest_workout_history.py` — an idempotent ingestion module that reads synthetic workout session data and loads it into Neo4j as `WorkoutSession` nodes with `(Member)-[:PERFORMED]->(WorkoutSession)` and `(WorkoutSession)-[:INCLUDED]->(Exercise)` edges, following the schema defined in `.docs/knowledge-graph-schema.md`.

## Approach

The module exposes a single public function `ingest_workout_history(driver, sessions)` where `sessions` is a list of plain dicts matching the shape produced by the Phase 2 seed generator. All Cypher uses `MERGE` so the function is idempotent — re-running it never creates duplicate nodes or edges. A `__main__` entry point reads Neo4j credentials from `app.config.settings` and invokes the function with the synthetic sessions payload embedded in the seed module, making it runnable as `python -m app.knowledge_graph.ingest_workout_history`.

The session dict shape expected as input:

```python
{
    "id": str,            # UUID for the WorkoutSession node
    "member_id": str,     # UUID matching an existing Member node
    "started_at": str,    # ISO-8601 datetime string (UTC)
    "ended_at": str,      # ISO-8601 datetime string (UTC), nullable
    "exercises": [
        {
            "exercise_id": str,   # UUID matching an existing Exercise node
            "sets": int,
            "reps": list[int] | None,
            "weight_kg": float | None,
            "duration_s": list[int] | None,
        },
        ...
    ],
}
```

This shape is produced by `seed_workout_history_neo4j` in `backend/app/knowledge_graph/seed.py` and is the canonical contract between Phase 2 (seed generation) and Phase 3 (ingestion).

## Steps

### 1. Create ingest_workout_history.py  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/ingest_workout_history.py` with the following structure:

**Module-level constants / logger:**

```python
import logging
import uuid
from typing import Any

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)
```

**`_merge_session(tx, session: dict[str, Any]) -> None`** — private transaction function:

- Runs `MERGE (ws:WorkoutSession {id: $id}) SET ws += {started_at: $started_at, ended_at: $ended_at}` to upsert the session node.
- Runs `MATCH (m:Member {id: $member_id}) MATCH (ws:WorkoutSession {id: $session_id}) MERGE (m)-[:PERFORMED]->(ws)` to create the PERFORMED edge.
- For each exercise in `session["exercises"]`:
  - Runs `MATCH (ws:WorkoutSession {id: $session_id}) MATCH (e:Exercise {id: $exercise_id}) MERGE (ws)-[r:INCLUDED]->(e) SET r += {sets: $sets, reps: $reps, weight_kg: $weight_kg, duration_s: $duration_s}` to upsert the INCLUDED edge with performance properties.
- All three operations run within the same write transaction so they succeed or fail atomically.

**`ingest_workout_history(driver: neo4j.Driver, sessions: list[dict[str, Any]]) -> int`** — public function:

- Accepts a driver and list of session dicts.
- For each session, opens a write transaction and calls `_merge_session`.
- Returns the count of sessions processed.
- Logs a summary line at `INFO` level: `"Ingested N workout sessions into Neo4j."`.
- Raises `ValueError` if `sessions` is empty (guards against silent no-ops from bad upstream data).

**`__main__` block:**

- Imports `seed_workout_history_neo4j` from `app.knowledge_graph.seed` — NO: instead, directly imports `PERSONAS` and calls the existing `seed.py` helper functions to obtain a list of session dicts.
- Actually: the `__main__` block should call `ingest_workout_history` with a minimal synthetic payload for smoke-testing. It connects using `settings.neo4j_uri`, `settings.neo4j_user`, `settings.neo4j_password`, calls `neo4j.GraphDatabase.driver(...)`, invokes `ingest_workout_history`, then closes the driver.
- Log output and clean exit on success; raise on failure.

Concrete implementation notes:
- Use `neo4j.GraphDatabase.driver(uri, auth=(user, password))` from `app.config.settings`.
- All Cypher uses `MERGE` with `SET r +=` for edge properties to ensure idempotency.
- `weight_kg` and `duration_s` default to `None` if absent from the dict.
- Log each batch at `DEBUG` level: `"Processing session {session_id} for member {member_id}"`.

- [x] `backend/app/knowledge_graph/ingest_workout_history.py` exists
- [x] `_merge_session(tx, session)` private function is implemented
- [x] `ingest_workout_history(driver, sessions) -> int` is exported
- [x] All Cypher statements use `MERGE` (idempotent)
- [x] `PERFORMED` edge is created between Member and WorkoutSession
- [x] `INCLUDED` edge is created between WorkoutSession and Exercise with `sets`, `reps`, `weight_kg`, `duration_s` properties
- [x] `__main__` block is present and runnable

### 2. Wire ingest_workout_history into seed.py  <!-- agent: general-purpose -->

Update `backend/app/knowledge_graph/seed.py` to refactor `seed_workout_history_neo4j` so it delegates to `ingest_workout_history`:

- Import `ingest_workout_history` from `app.knowledge_graph.ingest_workout_history`.
- Refactor `seed_workout_history_neo4j` to: (a) build the list of session dicts in the existing format, then (b) call `ingest_workout_history(driver, sessions)` instead of writing Cypher inline.
- This removes duplicated Cypher from `seed.py` and proves the ingestion module works end-to-end via the existing seed pipeline.

The session dict format built inside `seed_workout_history_neo4j` (already generates the right shape):

```python
session = {
    "id": session_id,
    "member_id": member_id,
    "started_at": started_at.isoformat(),
    "ended_at": ended_at.isoformat(),
    "exercises": [
        {
            "exercise_id": str(ex["id"]),
            "sets": props["sets"],
            "reps": props["reps"],
            "weight_kg": props.get("weight_kg"),
            "duration_s": props.get("duration_s"),
        }
        for ex in chosen
    ],
}
```

- [x] `seed.py` imports `ingest_workout_history` from the new module
- [x] `seed_workout_history_neo4j` builds session dicts then delegates to `ingest_workout_history`
- [x] Inline Cypher for WorkoutSession / PERFORMED / INCLUDED is removed from `seed.py`
- [x] `seed.py` still functions end-to-end (no regression in the seed pipeline)

### 3. Add module to knowledge_graph __init__.py  <!-- agent: general-purpose -->

Export `ingest_workout_history` from `backend/app/knowledge_graph/__init__.py` so callers can do:

```python
from app.knowledge_graph import ingest_workout_history
```

- [x] `backend/app/knowledge_graph/__init__.py` exports `ingest_workout_history`

### 4. Write unit tests  <!-- agent: general-purpose -->

Create `backend/tests/knowledge_graph/test_ingest_workout_history.py`:

- `test_ingest_empty_raises_value_error`: call `ingest_workout_history(mock_driver, [])` and assert `ValueError` is raised.
- `test_merge_session_cypher_calls`: use `unittest.mock.MagicMock` for `tx`; call `_merge_session(tx, sample_session)` directly and assert `tx.run` was called at least 3 times (session node, PERFORMED edge, at least one INCLUDED edge).
- `test_ingest_returns_count`: mock the driver session context manager; call `ingest_workout_history(mock_driver, [sample_session])` and assert return value is 1.
- `test_idempotent_cypher_uses_merge`: inspect the `call_args_list` on the mock `tx.run` and assert every Cypher string contains `MERGE`.

Place in `backend/tests/knowledge_graph/` (create `__init__.py` for the sub-package if it doesn't exist).

- [x] `backend/tests/knowledge_graph/test_ingest_workout_history.py` exists
- [x] `test_ingest_empty_raises_value_error` passes
- [x] `test_merge_session_cypher_calls` passes
- [x] `test_ingest_returns_count` passes
- [x] `test_idempotent_cypher_uses_merge` passes
- [x] All 4 tests pass with `pytest backend/tests/knowledge_graph/test_ingest_workout_history.py`

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/ingest_workout_history.py` exists and is valid Python
- [x] `ingest_workout_history(driver, sessions) -> int` is importable from `app.knowledge_graph`
- [x] All Cypher uses `MERGE` — running the function twice produces the same graph state
- [x] `(Member)-[:PERFORMED]->(WorkoutSession)` edges are created with correct directionality
- [x] `(WorkoutSession)-[:INCLUDED]->(Exercise)` edges carry `sets`, `reps`, `weight_kg`, `duration_s` properties
- [x] `seed_workout_history_neo4j` in `seed.py` delegates to `ingest_workout_history` (no duplicate Cypher)
- [x] Module is runnable as `python -m app.knowledge_graph.ingest_workout_history` from `backend/`
- [x] All 4 unit tests pass

---
**UAT**: [`.docs/uat/052-ingest-workout-history-neo4j.uat.md`](../uat/052-ingest-workout-history-neo4j.uat.md)
