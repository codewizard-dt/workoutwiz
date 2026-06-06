# 057 — Preference/Feedback Traversal: Surface Highly-Rated and Performed Exercises

> **Depends on**: [056-injury-traversal-queries](056-injury-traversal-queries.md)
> **Blocks**: [058-context-assembler](058-context-assembler.md), [059-retrieval-subgraph](059-retrieval-subgraph.md)
> **Parallel-safe with**: [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md), [054-graphrag-adr](054-graphrag-adr.md), [055-vector-embeddings](055-vector-embeddings.md)

## Objective

Extend `backend/app/kg/traversal.py` (created in TASK-056) with two additional Cypher traversal functions: `get_preferred_exercises()` — exercises rated ≥4 by the member via FeedbackEvent nodes — and `get_performed_exercises()` — exercises the member has previously performed, ordered by recency. These functions complete the graph-side preference signals used by the context assembler in TASK-058.

## Approach

This task extends the existing `traversal.py` module rather than creating a new file — both functions follow the same async driver pattern established in TASK-056. The key traversal paths are:

- **Preferred**: `Member -[HAS_FEEDBACK]-> FeedbackEvent -[RATED]-> Exercise` where `FeedbackEvent.rating >= 4`
  - Returns exercise id, name, muscle_groups, movement_patterns, plus the average rating and count
  - Sorted by average rating DESC, then name ASC
- **Performed**: `Member -[PERFORMED]-> WorkoutSession -[INCLUDED]-> WorkoutSequence -[CONTAINS]-> WorkoutSet -[USES]-> Exercise`
  - Alternative shorter path (check schema): `Member -[PERFORMED]-> WorkoutSession -[INCLUDED]-> Exercise` if INCLUDED goes directly to Exercise
  - Returns exercise id, name, and the most recent `WorkoutSession.started_at` for that exercise
  - Sorted by most recent performance DESC (recency signal)
  - Limit to 20 most recent distinct exercises (avoids overwhelming the context budget)

**Schema verification**: Before writing Cypher, review `.docs/knowledge-graph-schema.md` to confirm the exact edge names and direction between WorkoutSession and Exercise nodes. Use the schema as ground truth — the descriptions above are from memory and may differ from the actual schema.

## Steps

### 1. Review the knowledge graph schema  <!-- agent: general-purpose -->

Read `.docs/knowledge-graph-schema.md` to confirm:
1. The exact edge label from `Member` to `FeedbackEvent` (is it `HAS_FEEDBACK`, or does FeedbackEvent connect differently?)
2. The exact edge from `FeedbackEvent` to `Exercise` (is it `RATED`, `FOR_EXERCISE`, or another label?)
3. The path from `WorkoutSession` to `Exercise` — is it direct (`INCLUDED`) or through intermediate nodes?
4. The property name for the feedback rating on `FeedbackEvent` (is it `rating`, `score`, or another name?)
5. The property name for the session timestamp on `WorkoutSession` (is it `started_at`, `date`, or another name?)

Use these verified names in all Cypher queries in step 2.

- [x] Schema reviewed and edge/property names confirmed for FeedbackEvent and WorkoutSession paths <!-- Completed: 2026-06-06 -->
  - Preferred: `(Member)-[:RATED {rating}]->(Exercise)` — direct relationship, no HAS_FEEDBACK edge
  - Performed: `(Member)-[:PERFORMED]->(WorkoutSession {started_at})-[:INCLUDED]->(Exercise)` — direct
  - Rating property: `r.rating` on the RATED relationship; session timestamp: `ws.started_at`

### 2. Add `get_preferred_exercises()` to `backend/app/kg/traversal.py`  <!-- agent: general-purpose -->

Use Serena's `get_symbols_overview` on `backend/app/kg/traversal.py` to understand the current module structure. Then use `insert_after_symbol` or `replace_content` to append the new query constant and function after the existing content.

Add the Cypher query constant (use verified edge/property names from step 1):

```python
# Exercises the member has rated >= 4, with average rating and count.
# Traversal: Member -[HAS_FEEDBACK]-> FeedbackEvent -[RATED]-> Exercise
_PREFERRED_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})-[:HAS_FEEDBACK]->(fe:FeedbackEvent)-[:RATED]->(e:Exercise)
WHERE fe.rating >= $min_rating
RETURN
    e.id                AS id,
    e.name              AS name,
    e.muscle_groups     AS muscle_groups,
    e.movement_patterns AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier     AS priority_tier,
    avg(fe.rating)      AS avg_rating,
    count(fe)           AS feedback_count
ORDER BY avg_rating DESC, e.name ASC
"""
```

And the function:

```python
async def get_preferred_exercises(
    member_id: str,
    driver: AsyncDriver,
    min_rating: int = 4,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return exercises the member has rated >= min_rating.

    Uses FeedbackEvent nodes to identify exercises the member has positively
    rated. Results are ordered by average rating (DESC), then name (ASC).

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        min_rating: Minimum rating threshold (default: 4, range: 1–5).
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: id, name, muscle_groups,
        movement_patterns, equipment_required, priority_tier,
        avg_rating, feedback_count. Returns [] if no qualifying feedback.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _PREFERRED_EXERCISES_QUERY,
            member_id=member_id,
            min_rating=min_rating,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d preferred exercise(s) (rating >= %d).",
        member_id, len(records), min_rating,
    )
    return records
```

Adjust edge labels and property names to match the verified schema from step 1.

- [x] `_PREFERRED_EXERCISES_QUERY` constant added to `backend/app/knowledge_graph/traversal.py` with correct edge/property names <!-- Completed: 2026-06-06 -->
- [x] `get_preferred_exercises()` function added with correct signature and docstring <!-- Completed: 2026-06-06 -->
- [x] Query uses `$min_rating` parameter (no hard-coded values) <!-- Completed: 2026-06-06 -->
- [x] Results ordered by `avg_rating DESC, name ASC` <!-- Completed: 2026-06-06 -->

### 3. Add `get_performed_exercises()` to `backend/app/kg/traversal.py`  <!-- agent: general-purpose -->

Add the Cypher query constant and function for recently performed exercises. Use verified path from step 1:

```python
# Most recently performed exercises per member (distinct, ordered by recency).
# Traversal: Member -[PERFORMED]-> WorkoutSession -[INCLUDED]-> Exercise
# (adjust intermediate nodes to match actual schema)
_PERFORMED_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})-[:PERFORMED]->(ws:WorkoutSession)-[:INCLUDED]->(e:Exercise)
RETURN DISTINCT
    e.id                AS id,
    e.name              AS name,
    e.muscle_groups     AS muscle_groups,
    e.movement_patterns AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier     AS priority_tier,
    max(ws.started_at)  AS last_performed_at
ORDER BY last_performed_at DESC
LIMIT $limit
"""
```

And the function:

```python
async def get_performed_exercises(
    member_id: str,
    driver: AsyncDriver,
    limit: int = 20,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return the most recently performed exercises for a member.

    Traverses WorkoutSession nodes to find distinct exercises the member
    has performed, ordered by the most recent session date (DESC).

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        limit: Maximum number of distinct exercises to return (default: 20).
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts with keys: id, name, muscle_groups,
        movement_patterns, equipment_required, priority_tier,
        last_performed_at. Returns [] if the member has no workout history.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _PERFORMED_EXERCISES_QUERY,
            member_id=member_id,
            limit=limit,
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d recently performed exercise(s).",
        member_id, len(records),
    )
    return records
```

Adjust edge labels, property names, and intermediate nodes to match the actual schema path from step 1. If the path from WorkoutSession to Exercise is longer (e.g., through WorkoutSequence and WorkoutSet), expand the MATCH pattern accordingly while keeping `DISTINCT e.id` in the RETURN clause.

- [x] `_PERFORMED_EXERCISES_QUERY` constant added with correct traversal path <!-- Completed: 2026-06-06 -->
- [x] `get_performed_exercises()` function added with correct signature and docstring <!-- Completed: 2026-06-06 -->
- [x] Query uses `$limit` parameter <!-- Completed: 2026-06-06 -->
- [x] Results ordered by `last_performed_at DESC` <!-- Completed: 2026-06-06 -->
- [x] `DISTINCT` used to avoid duplicate exercises from multiple sessions <!-- Completed: 2026-06-06 -->

### 4. Write unit tests for the new traversal functions  <!-- agent: general-purpose -->

Add new test cases to `backend/tests/kg/test_traversal.py` (the file created in TASK-056). Use `Read` to inspect the current file first (via `mcp__serena__get_symbols_overview` to see existing test names), then append new tests using Serena's `insert_after_symbol` or append via `replace_content`.

Test cases to add (all using `pytest-asyncio` + `AsyncMock`):

```python
# test_get_preferred_exercises_returns_list
# Mock run().data() to return two dicts with avg_rating and feedback_count
# Call get_preferred_exercises("member-1", mock_driver)
# Assert result is a list of length 2
# Assert each element has key "avg_rating"

# test_get_preferred_exercises_empty_when_no_feedback
# Mock run().data() to return []
# Assert result is []

# test_get_preferred_exercises_uses_min_rating_param
# Mock driver session; capture the call args to session.run()
# Call get_preferred_exercises("member-1", mock_driver, min_rating=5)
# Assert the run() was called with min_rating=5

# test_get_performed_exercises_returns_list
# Mock run().data() to return three dicts with last_performed_at
# Assert result is a list of length 3

# test_get_performed_exercises_empty_when_no_history
# Mock run().data() to return []
# Assert result is []

# test_get_performed_exercises_uses_limit_param
# Capture run() call args
# Call get_performed_exercises("member-1", mock_driver, limit=5)
# Assert run() was called with limit=5
```

- [x] ≥6 new test functions added to `backend/tests/knowledge_graph/test_traversal.py` <!-- Completed: 2026-06-06 -->
- [x] All new tests use `AsyncMock` (asyncio_mode=auto, no explicit decorator needed) <!-- Completed: 2026-06-06 -->
- [x] Tests cover both the happy path (data returned) and empty results <!-- Completed: 2026-06-06 -->

### 5. Run the full kg test suite  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/ -v
```

This runs both `test_traversal.py` (all tests including TASK-056's and new ones) and `test_embeddings.py` (if present from TASK-055). All must pass.

Fix any failures before marking complete.

- [x] All tests in `backend/tests/knowledge_graph/` pass with 0 failures — 14 passed in 0.41s <!-- Completed: 2026-06-06 -->

### 6. Update the roadmap  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md`. Replace the inline placeholder:

```
- [ ] Preference/feedback traversal: surface highly-rated or flagged exercises per member
```

with:

```
- [ ] [TASK-057: Preference/feedback traversal — surface highly-rated and performed exercises](../tasks/057-preference-feedback-traversal.md)
```

Use the `Edit` tool. Update `**Last updated**` to `2026-06-06`.

- [x] Roadmap task link already present; updated `**Last updated**` to 2026-06-06 (TASK-057 complete) <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/traversal.py` now contains all five functions: `get_contraindicated_exercise_ids`, `get_safe_exercises`, `get_member_profile` (from TASK-056), `get_preferred_exercises`, `get_performed_exercises` <!-- Completed: 2026-06-06 -->
- [x] `get_preferred_exercises()` traverses via `(Member)-[:RATED]->(Exercise)` with `r.rating >= min_rating` and returns `avg_rating` per exercise <!-- Completed: 2026-06-06 -->
- [x] `get_performed_exercises()` returns distinct exercises ordered by `last_performed_at DESC` with a configurable `limit` <!-- Completed: 2026-06-06 -->
- [x] All Cypher queries use parameterized variables — no string interpolation <!-- Completed: 2026-06-06 -->
- [x] Edge labels and property names match the actual knowledge graph schema (verified in step 1) <!-- Completed: 2026-06-06 -->
- [x] ≥6 new unit tests added to `backend/tests/knowledge_graph/test_traversal.py`, all passing — 14 total (8 from TASK-056 + 6 new) <!-- Completed: 2026-06-06 -->
- [x] Roadmap TASK-057 link already present in Phase 4; `**Last updated**` refreshed <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/057-preference-feedback-traversal.uat.md`](../uat/057-preference-feedback-traversal.uat.md)
