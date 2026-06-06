# 062 — Explainability Tool: Why Was This Exercise Skipped?

> **Depends on**: [060-generation-agent-subgraph](060-generation-agent-subgraph.md)
> **Blocks**: [065-kg-fastapi-router](065-kg-fastapi-router.md)
> **Parallel-safe with**: [061-injury-safety-gate](061-injury-safety-gate.md), [063-fallback-handler](063-fallback-handler.md)

## Objective

Create `backend/app/kg/explainability.py` with an async `explain_skipped_exercise(member_id, exercise_id, driver) -> str` function that traverses the Neo4j graph to produce a human-readable reason chain for why an exercise was skipped (e.g., "Squats were excluded because you have knee tendinopathy, which contraindicates exercises loading the knee joint.").

## Approach

The reason chain is built from Neo4j traversal:
1. Find injuries for the member: `(m:Member)-[:HAS_INJURY]->(i:Injury)`
2. Find contraindication edges from the exercise: `(e:Exercise)-[:CONTRAINDICATED_BY]->(i:Injury)`
3. Intersect the two sets of injuries to find which injury caused the skip.
4. Return a natural-language sentence from the graph data.

If no contraindication is found, return `"This exercise was not recommended due to insufficient context."` (graceful fallback).

**Cypher query:**
```cypher
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury)<-[:CONTRAINDICATED_BY]-(e:Exercise {id: $exercise_id})
RETURN e.name AS exercise_name, collect(i.name) AS injury_names
```

**Return format:** `"'{exercise_name}' was skipped because it is contraindicated for: {comma-joined injury names}."`

## Steps

### 1. Inspect Neo4j schema and traversal patterns  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/knowledge_graph/traversal.py` to confirm field names on `Injury` and `Exercise` nodes (especially `name`, `id`). Check `ingest_injuries.py` for the `CONTRAINDICATED_BY` relationship direction.

- [x] Node property names and relationship direction confirmed <!-- Completed: 2026-06-06 -->

### 2. Create `backend/app/kg/explainability.py`  <!-- agent: general-purpose -->

Use the `Write` tool:

```python
"""Explainability: traverse Neo4j to explain why an exercise was skipped."""
import logging
from neo4j import AsyncDriver

logger = logging.getLogger(__name__)

async def explain_skipped_exercise(
    member_id: str,
    exercise_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> str:
    """Return a human-readable reason why the exercise was excluded for this member."""
    query = """
    MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(i:Injury)<-[:CONTRAINDICATED_BY]-(e:Exercise {id: $exercise_id})
    RETURN e.name AS exercise_name, collect(i.name) AS injury_names
    """
    async with driver.session(database=database) as session:
        result = await session.run(query, member_id=member_id, exercise_id=exercise_id)
        record = await result.single()
    
    if not record or not record["injury_names"]:
        return "This exercise was not included due to insufficient context."
    
    exercise_name = record["exercise_name"]
    injuries = ", ".join(record["injury_names"])
    return f"'{exercise_name}' was skipped because it is contraindicated for: {injuries}."
```

- [x] `backend/app/kg/explainability.py` created <!-- Completed: 2026-06-06 -->

### 3. Write unit tests `backend/tests/kg/test_explainability.py`  <!-- agent: general-purpose -->

Tests (mocked Neo4j session):
- `test_explain_returns_injury_reason`: mock `session.run` to return a record with exercise_name and injury_names; assert returned string contains the injury name.
- `test_explain_returns_fallback_when_no_contraindication`: mock `session.run` to return None; assert fallback string returned.
- `test_explain_returns_fallback_when_no_injuries`: mock to return record with empty injury_names list.

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_explainability.py -v
```

- [x] Tests pass <!-- Completed: 2026-06-06 -->

### 4. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 5 explainability placeholder with `[TASK-062: Explainability tool...](../tasks/062-explainability-tool.md)`.

- [x] Roadmap updated <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/kg/explainability.py` with `explain_skipped_exercise(member_id, exercise_id, driver) -> str`
- [x] Returns `"'{name}' was skipped because it is contraindicated for: {injuries}."` format
- [x] Returns graceful fallback string (not raises) when no contraindication found
- [x] ≥3 tests passing

---
**UAT**: [`.docs/uat/062-explainability-tool.uat.md`](../uat/062-explainability-tool.uat.md)
