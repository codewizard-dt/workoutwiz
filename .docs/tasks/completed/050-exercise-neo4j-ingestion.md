# 050 — Exercise Neo4j ingestion

> **Depends on**: [044-neo4j-schema-init-script](completed/044-neo4j-schema-init-script.md)
> **Blocks**: none
> **Parallel-safe with**: [033-critical-path-router-test](033-critical-path-router-test.md), [034-critical-path-generator-test](034-critical-path-generator-test.md)

## Objective

Create `backend/app/knowledge_graph/ingest_exercises.py` — a standalone, idempotent ingestion module that loads all 50 exercises from `.docs/guides/1-multi-agent/exercises.json` into Neo4j as `Exercise` nodes and then wires `(Exercise)-[:CONTRAINDICATED_BY]->(Injury)` edges for every pre-existing active `Injury` node whose `affected_joints` overlaps the exercise's `joints_loaded`. The module is runnable via `python -m app.knowledge_graph.ingest_exercises` and is also importable for use by `seed.py` and future ingestion scripts.

## Approach

`seed.py` already seeds exercises as part of a full bootstrap flow (PostgreSQL + Neo4j together). This module is a focused, independently-runnable alternative that only touches Neo4j. It uses `MERGE` throughout for idempotence. After upserting all Exercise nodes it scans pre-existing `Injury` nodes and merges `CONTRAINDICATED_BY` edges — matching on joint overlap (`ANY(j IN e.joints_loaded WHERE j IN i.affected_joints)`). This Cypher-side approach avoids N×M Python-side iteration for the edge pass.

All field names and types must match the schema in `.docs/knowledge-graph-schema.md` exactly. The `description` and `description_embedding` properties are omitted from this task (populated in Phase 4).

## Steps

### 1. Create `backend/app/knowledge_graph/ingest_exercises.py`  <!-- agent: general-purpose -->

Create the file at `backend/app/knowledge_graph/ingest_exercises.py`.

**Imports and constants:**

```python
"""Standalone exercise ingestion: exercises.json → Neo4j Exercise nodes + CONTRAINDICATED_BY edges."""
from __future__ import annotations

import json
import logging
from pathlib import Path

import neo4j

from app.config import settings

logger = logging.getLogger(__name__)

_EXERCISES_PATH = (
    Path(__file__).resolve().parents[4]
    / ".docs" / "guides" / "1-multi-agent" / "exercises.json"
)
```

**`load_exercises() -> list[dict]` function:**

```python
def load_exercises() -> list[dict]:
    with _EXERCISES_PATH.open() as f:
        return json.load(f)
```

**`ingest_exercises(driver: neo4j.Driver, exercises: list[dict] | None = None) -> int` function:**

- If `exercises` is `None`, call `load_exercises()`.
- Open a single `driver.session()`.
- Run one `MERGE`+`SET` statement per exercise (same field set as `seed_exercises_neo4j` in `seed.py`):
  ```cypher
  MERGE (e:Exercise {id: $id})
  SET e += {
      name: $name,
      muscle_groups: $muscle_groups,
      joints_loaded: $joints_loaded,
      movement_patterns: $movement_patterns,
      equipment_required: $equipment_required,
      is_reps: $is_reps,
      is_duration: $is_duration,
      supports_weight: $supports_weight,
      priority_tier: $priority_tier,
      is_bilateral: $is_bilateral,
      bilateral_pair_id: $bilateral_pair_id,
      side: $side,
      estimated_rep_duration: $estimated_rep_duration
  }
  ```
  Parameters map directly from the JSON dict; use the same defaults as `seed.py`:
  - `muscle_groups`, `joints_loaded`, `movement_patterns`, `equipment_required`: `ex.get(field) or []`
  - `is_reps`: default `True`, `is_duration`: default `False`, `supports_weight`: default `False`
  - `priority_tier`: default `3`, `is_bilateral`: default `True`
  - `bilateral_pair_id`: `str(ex["bilateral_pair_id"]) if ex.get("bilateral_pair_id") else None`
  - `side`: `ex.get("side")`
  - `estimated_rep_duration`: `ex.get("estimated_rep_duration")`
- After the exercise loop, run the joint-overlap edge pass in a single Cypher statement:
  ```cypher
  MATCH (e:Exercise), (i:Injury {status: 'active'})
  WHERE ANY(j IN e.joints_loaded WHERE j IN i.affected_joints)
  MERGE (e)-[:CONTRAINDICATED_BY]->(i)
  ```
- `logger.info("Ingested %d exercises; CONTRAINDICATED_BY edges merged.", len(exercises))`
- Return `len(exercises)`.

Acceptance criteria:
- [x] `ingest_exercises` accepts `driver` and optional `exercises` list <!-- Completed: 2026-06-06 -->
- [x] Uses `MERGE (e:Exercise {id: $id})` — not `CREATE` <!-- Completed: 2026-06-06 -->
- [x] All 13 Exercise properties from the schema are set (id, name, muscle_groups, joints_loaded, movement_patterns, equipment_required, is_reps, is_duration, supports_weight, priority_tier, is_bilateral, bilateral_pair_id, side, estimated_rep_duration) <!-- Completed: 2026-06-06 -->
- [x] Joint-overlap `CONTRAINDICATED_BY` edge pass runs after Exercise upserts <!-- Completed: 2026-06-06 -->
- [x] Returns the count of exercises processed <!-- Completed: 2026-06-06 -->

### 2. Add `__main__` entry point  <!-- agent: general-purpose -->

At the bottom of `ingest_exercises.py`, add:

```python
if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    with neo4j.GraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    ) as _driver:
        count = ingest_exercises(_driver)
    print(f"Done. {count} exercises ingested.")
```

Acceptance criteria:
- [x] Module is runnable as `python -m app.knowledge_graph.ingest_exercises` from `backend/` <!-- Completed: 2026-06-06 -->
- [x] Logs progress to stdout <!-- Completed: 2026-06-06 -->
- [x] Prints final count on success <!-- Completed: 2026-06-06 -->

### 3. Replace `seed_exercises_neo4j` in `seed.py` with a delegation call  <!-- agent: general-purpose -->

In `backend/app/knowledge_graph/seed.py`:

- Add import at the top of the file (after existing imports):
  ```python
  from app.knowledge_graph.ingest_exercises import ingest_exercises
  ```
- Replace the body of `seed_exercises_neo4j` with a single delegation call:
  ```python
  def seed_exercises_neo4j(driver: neo4j.Driver, exercises: list[dict]) -> None:
      """Delegate to the standalone ingestion module."""
      ingest_exercises(driver, exercises)
  ```
  This keeps `seed.py`'s call site (`seed_exercises_neo4j(driver, exercises)`) unchanged while making `ingest_exercises.py` the single source of truth.

Acceptance criteria:
- [x] `seed.py` imports `ingest_exercises` from `app.knowledge_graph.ingest_exercises` <!-- Completed: 2026-06-06 -->
- [x] `seed_exercises_neo4j` body delegates to `ingest_exercises(driver, exercises)` <!-- Completed: 2026-06-06 -->
- [x] `seed.py`'s `main()` call site is unchanged <!-- Completed: 2026-06-06 -->

### 4. Write a minimal smoke test  <!-- agent: general-purpose -->

Create `backend/tests/knowledge_graph/test_ingest_exercises.py`.

Use `unittest.mock.MagicMock` to stub the Neo4j driver — no live Neo4j connection required.

```python
from unittest.mock import MagicMock, call, patch
from app.knowledge_graph.ingest_exercises import ingest_exercises, load_exercises

SAMPLE = [
    {
        "id": "aaaaaaaa-0000-0000-0000-000000000001",
        "name": "Test Squat",
        "muscle_groups": ["quads"],
        "joints_loaded": ["knee"],
        "movement_patterns": ["squat"],
        "equipment_required": [],
        "is_bilateral": True,
        "side": None,
        "priority_tier": 1,
        "is_reps": True,
        "is_duration": False,
        "supports_weight": True,
        "estimated_rep_duration": 1.0,
        "bilateral_pair_id": None,
    }
]


def test_ingest_exercises_calls_merge_and_edge_pass():
    """ingest_exercises runs MERGE for each exercise then the edge pass."""
    mock_session = MagicMock()
    mock_driver = MagicMock()
    mock_driver.session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_driver.session.return_value.__exit__ = MagicMock(return_value=False)

    result = ingest_exercises(mock_driver, SAMPLE)

    assert result == 1
    # session.run called at least twice: 1 MERGE per exercise + 1 edge pass
    assert mock_session.run.call_count >= 2


def test_load_exercises_returns_50():
    """exercises.json contains exactly 50 records."""
    data = load_exercises()
    assert len(data) == 50
    assert all("id" in ex and "joints_loaded" in ex for ex in data)
```

Create `backend/tests/knowledge_graph/__init__.py` (empty) if it does not already exist.

Acceptance criteria:
- [x] `backend/tests/knowledge_graph/__init__.py` exists <!-- Completed: 2026-06-06 -->
- [x] `backend/tests/knowledge_graph/test_ingest_exercises.py` exists <!-- Completed: 2026-06-06 -->
- [x] `test_ingest_exercises_calls_merge_and_edge_pass` passes with mocked driver <!-- Completed: 2026-06-06 -->
- [x] `test_load_exercises_returns_50` passes (reads real `exercises.json`) <!-- Completed: 2026-06-06 -->
- [x] Tests pass with `pytest backend/tests/knowledge_graph/test_ingest_exercises.py` from repo root <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/ingest_exercises.py` exists and is importable <!-- Completed: 2026-06-06 -->
- [x] `ingest_exercises(driver)` loads all 50 exercises from `exercises.json` with `MERGE` (idempotent) <!-- Completed: 2026-06-06 -->
- [x] All 14 Exercise schema properties are set on each node (including `estimated_rep_duration` and `side`) <!-- Completed: 2026-06-06 -->
- [x] `CONTRAINDICATED_BY` edge pass runs after Exercise upserts using Cypher-side joint-overlap matching <!-- Completed: 2026-06-06 -->
- [x] Module runs cleanly as `python -m app.knowledge_graph.ingest_exercises` from `backend/` <!-- Completed: 2026-06-06 -->
- [x] `seed.py`'s `seed_exercises_neo4j` delegates to `ingest_exercises` (no duplicated logic) <!-- Completed: 2026-06-06 -->
- [x] Smoke tests pass: mocked-driver test + exercises.json count assertion <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/050-exercise-neo4j-ingestion.uat.md`](../uat/050-exercise-neo4j-ingestion.uat.md)
