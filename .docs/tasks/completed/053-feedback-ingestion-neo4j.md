# 053 — Feedback ingestion: FeedbackEvent nodes + edges to Exercise, WorkoutSession, and Set

> **Depends on**: [044-neo4j-schema-init-script](completed/044-neo4j-schema-init-script.md), [042-neo4j-python-dependencies](completed/042-neo4j-python-dependencies.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Implement `backend/app/knowledge_graph/ingest_feedback.py` to load `ExerciseFeedback` rows from PostgreSQL into Neo4j as `FeedbackEvent` nodes with edges to `Exercise`, `WorkoutSession`, and `Set` nodes, and also write the denormalized `(Member)-[:RATED]->(Exercise)` relationship used for fast preference traversal.

## Approach

Read all `ExerciseFeedback` rows from the PostgreSQL `exercise_feedback` table using SQLAlchemy (async session). For each row, MERGE a `FeedbackEvent` node in Neo4j keyed on `id`, then create directed edges based on `context_type`:

- `exercise` → `(FeedbackEvent)-[:ABOUT]->(Exercise)` + `(Member)-[:RATED]->(Exercise)` (denormalized copy)
- `workout` → `(FeedbackEvent)-[:ABOUT]->(WorkoutSession)`
- `set` → `(FeedbackEvent)-[:ABOUT]->(Set)`

All Cypher uses `MERGE ... ON CREATE SET ... ON MATCH SET ...` so the script is idempotent. A `__main__` entry point allows running as `python -m app.knowledge_graph.ingest_feedback` from `backend/`.

The `Set` node is a thin Neo4j node keyed on `workout_set_id` (UUID). It does not need to carry heavy properties — downstream GraphRAG only traverses from `Member → WorkoutSession → Set → FeedbackEvent` to surface feedback context.

## Steps

### 1. Create ingest_feedback.py module  <!-- agent: general-purpose -->

Create `backend/app/knowledge_graph/ingest_feedback.py`.

Top-level imports:
```python
import asyncio
import uuid
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import select
from neo4j import AsyncGraphDatabase
from app.config import settings
from app.models.feedback import ExerciseFeedback, FeedbackContextType
```

**Function `ingest_all_feedback(pg_session: AsyncSession, neo4j_driver) -> int`**:

1. Query all `ExerciseFeedback` rows:
   ```python
   result = await pg_session.execute(select(ExerciseFeedback))
   rows = result.scalars().all()
   ```

2. Open a Neo4j async session and call `_upsert_feedback_batch(neo4j_session, rows)`.

3. Return total count of rows processed.

**Function `_upsert_feedback_batch(neo4j_session, rows: list[ExerciseFeedback]) -> None`**:

For each row, run these Cypher statements in a single write transaction:

**Step A — MERGE the FeedbackEvent node:**
```cypher
MERGE (f:FeedbackEvent {id: $id})
ON CREATE SET
  f.rating = $rating,
  f.feedback_text = $feedback_text,
  f.context_type = $context_type,
  f.created_at = $created_at
ON MATCH SET
  f.rating = $rating,
  f.feedback_text = $feedback_text
```
Parameters: `id` (str), `rating` (int), `feedback_text` (str|None), `context_type` (str), `created_at` (ISO datetime str).

**Step B — Edge based on context_type:**

- If `context_type == FeedbackContextType.EXERCISE`:
  ```cypher
  MATCH (f:FeedbackEvent {id: $feedback_id})
  MATCH (e:Exercise {id: $exercise_id})
  MERGE (f)-[:ABOUT]->(e)
  ```
  Then write the denormalized `RATED` edge:
  ```cypher
  MATCH (m:Member {id: $member_id})
  MATCH (e:Exercise {id: $exercise_id})
  MERGE (m)-[r:RATED]->(e)
  ON CREATE SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
  ON MATCH SET r.rating = $rating, r.feedback_text = $feedback_text, r.created_at = $created_at
  ```

- If `context_type == FeedbackContextType.WORKOUT`:
  ```cypher
  MATCH (f:FeedbackEvent {id: $feedback_id})
  MATCH (ws:WorkoutSession {id: $workout_id})
  MERGE (f)-[:ABOUT]->(ws)
  ```

- If `context_type == FeedbackContextType.SET`:
  ```cypher
  MERGE (s:Set {id: $workout_set_id})
  WITH s
  MATCH (f:FeedbackEvent {id: $feedback_id})
  MERGE (f)-[:ABOUT]->(s)
  ```

Use a helper `_run_write_tx(tx, cypher, params)` to keep the transaction logic DRY.

**`__main__` block:**
```python
if __name__ == "__main__":
    async def _main():
        engine = create_async_engine(settings.database_url)
        driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )
        async with AsyncSession(engine) as pg_session:
            count = await ingest_all_feedback(pg_session, driver)
            print(f"Ingested {count} FeedbackEvent nodes")
        await driver.close()
    asyncio.run(_main())
```

Acceptance:
- [x] `backend/app/knowledge_graph/ingest_feedback.py` exists
- [x] `ingest_all_feedback(pg_session, neo4j_driver)` is importable and returns `int`
- [x] `_upsert_feedback_batch` runs all Cypher via write transactions
- [x] All three `context_type` branches are handled (`exercise`, `workout`, `set`)
- [x] `(Member)-[:RATED]->(Exercise)` edge is written for `exercise` context
- [x] `__main__` block is present and uses `asyncio.run` <!-- Completed: 2026-06-06 -->

### 2. Add Set node constraint to init_schema.py  <!-- agent: general-purpose -->

The `Set` node introduced in this task needs a uniqueness constraint. Add to the `CONSTRAINTS` list in `backend/app/knowledge_graph/init_schema.py`:

```python
"CREATE CONSTRAINT set_id IF NOT EXISTS FOR (s:Set) REQUIRE s.id IS UNIQUE",
```

Insert after the existing `workout_session_id` constraint line.

Acceptance:
- [x] `init_schema.py` CONSTRAINTS list includes a `Set.id IS UNIQUE` constraint with `IF NOT EXISTS` <!-- Completed: 2026-06-06 -->

### 3. Wire ingest_feedback into the seed loader  <!-- agent: general-purpose -->

Locate the existing seed loader script. Check `backend/app/knowledge_graph/` for a `seed.py` or `seed_loader.py`. If one exists, import and call `ingest_all_feedback` from it. If no seed loader exists yet, create a minimal `backend/app/knowledge_graph/seed.py` with:

```python
"""
Seed loader: runs all Neo4j ingestion steps in dependency order.
Run with: python -m app.knowledge_graph.seed
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from neo4j import AsyncGraphDatabase
from app.config import settings
from app.knowledge_graph.ingest_feedback import ingest_all_feedback

async def run_seed():
    engine = create_async_engine(settings.database_url)
    driver = AsyncGraphDatabase.driver(
        settings.neo4j_uri,
        auth=(settings.neo4j_user, settings.neo4j_password),
    )
    async with AsyncSession(engine) as pg_session:
        count = await ingest_all_feedback(pg_session, driver)
        print(f"[seed] FeedbackEvent: {count} nodes ingested")
    await driver.close()

if __name__ == "__main__":
    asyncio.run(run_seed())
```

Acceptance:
- [x] `ingest_all_feedback` is callable from a seed entry point (either existing `seed.py` updated, or new `seed.py` created)
- [x] `python -m app.knowledge_graph.seed` runs without import errors (dry run with empty DB acceptable) <!-- Completed: 2026-06-06 -->

### 4. Write unit tests  <!-- agent: general-purpose -->

Create `backend/tests/knowledge_graph/test_ingest_feedback.py`.

Test the Cypher generation logic by mocking the Neo4j driver and asserting that:

1. **`test_exercise_context_writes_rated_edge`**: Given a `FeedbackEvent` row with `context_type=EXERCISE`, verify the mock Neo4j session receives both the `MERGE (f)-[:ABOUT]->(e)` Cypher and the `MERGE (m)-[r:RATED]->(e)` Cypher.

2. **`test_workout_context_writes_about_session`**: Given `context_type=WORKOUT`, verify only the `MERGE (f)-[:ABOUT]->(ws)` Cypher is written (no RATED edge).

3. **`test_set_context_merges_set_node`**: Given `context_type=SET` and a non-null `workout_set_id`, verify `MERGE (s:Set {id: ...})` appears in the executed Cypher.

4. **`test_idempotent_merge_on_match`**: Verify that running `_upsert_feedback_batch` twice with the same row does not raise and produces `MERGE ... ON MATCH SET` patterns (not `CREATE`).

Use `unittest.mock.AsyncMock` for the Neo4j async session and transaction. Keep tests fast — no real database connections.

Acceptance:
- [x] `backend/tests/knowledge_graph/test_ingest_feedback.py` exists
- [x] All 4 test functions are present
- [x] Tests use `AsyncMock` — no real Neo4j or Postgres connections
- [x] `pytest backend/tests/knowledge_graph/test_ingest_feedback.py` exits 0 <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/ingest_feedback.py` exists and is valid Python
- [x] `ingest_all_feedback(pg_session, neo4j_driver) -> int` is importable from `app.knowledge_graph.ingest_feedback`
- [x] All three `context_type` branches (`exercise`, `workout`, `set`) produce the correct Neo4j Cypher
- [x] `exercise` context writes both `(FeedbackEvent)-[:ABOUT]->(Exercise)` and `(Member)-[:RATED]->(Exercise)`
- [x] All Cypher uses `MERGE` (idempotent — safe to re-run)
- [x] `Set` node uniqueness constraint added to `init_schema.py`
- [x] Script runnable as `python -m app.knowledge_graph.ingest_feedback` from `backend/`
- [x] 4 unit tests pass with no real database connections <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/053-feedback-ingestion-neo4j.uat.md`](../uat/053-feedback-ingestion-neo4j.uat.md)
