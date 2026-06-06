# 056 — Graph Traversal Queries: Injury-Aware Exercise Filtering

> **Depends on**: [054-graphrag-adr](054-graphrag-adr.md)
> **Blocks**: [058-context-assembler](058-context-assembler.md), [059-retrieval-subgraph](059-retrieval-subgraph.md)
> **Parallel-safe with**: [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md), [055-vector-embeddings](055-vector-embeddings.md)

## Objective

Implement `backend/app/kg/traversal.py` with Cypher queries that traverse the `Member → HAS_INJURY → Injury → CONTRAINDICATED_BY → Exercise` path to produce a list of exercises that are safe for a given member, and a companion set of contraindicated exercise IDs for use in the Phase 5 injury safety gate.

## Approach

This task implements the injury-filtering half of the GraphRAG retrieval layer. The traversal pattern uses the graph schema defined in TASK-043 and seeded by tasks 049–051. Two public functions are exposed:

- `get_safe_exercises(member_id, driver)` — returns all Exercise nodes that are NOT in the member's contraindicated set, with fields needed for context assembly (id, name, muscle_groups, movement_patterns, equipment_required, priority_tier).
- `get_contraindicated_exercise_ids(member_id, driver)` — returns the set of exercise IDs that ARE contraindicated for this member's active injuries (used by the Phase 5 safety gate to validate generated workouts).

Both functions use the async Neo4j driver directly (not LangChain) for precise Cypher control. The traversal depth follows ADR-001 D1's decision — queries are written as explicit multi-hop Cypher rather than variable-length paths, for predictable performance.

The module is also responsible for `get_member_profile(member_id, driver)` — a lightweight query that fetches a member's goals, equipment, and availability for inclusion in the context slice (used by the context assembler in TASK-058).

## Steps

### 1. Verify the `backend/app/kg/` package exists  <!-- agent: general-purpose -->

Use `mcp__serena__list_dir` on `backend/app/` to confirm `kg/` is present. If TASK-055 has not been run yet, create `backend/app/kg/__init__.py` as an empty file using the `Write` tool.

- [x] `backend/app/kg/__init__.py` exists — NOTE: actual package is `backend/app/knowledge_graph/` (existing convention); `traversal.py` placed there <!-- Completed: 2026-06-06 -->

### 2. Create `backend/app/kg/traversal.py`  <!-- agent: general-purpose -->

Create the file using the `Write` tool with the following implementation:

```python
"""
Graph traversal queries for the GraphRAG retrieval layer.

Provides injury-aware exercise filtering and member profile lookup
via direct Cypher queries against the Neo4j knowledge graph.
"""

from __future__ import annotations

import logging
from typing import Any

import neo4j
from neo4j import AsyncDriver, AsyncSession

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cypher queries
# ---------------------------------------------------------------------------

# All exercises contraindicated for a member's active injuries.
# Traversal: Member -[HAS_INJURY]-> Injury -[CONTRAINDICATED_BY]-> Exercise
_CONTRAINDICATED_IDS_QUERY = """
MATCH (m:Member {id: $member_id})-[:HAS_INJURY]->(inj:Injury)-[:CONTRAINDICATED_BY]->(e:Exercise)
RETURN DISTINCT e.id AS exercise_id
"""

# All exercises NOT contraindicated for the member.
# Uses WHERE NOT EXISTS subquery pattern for clarity and index use.
_SAFE_EXERCISES_QUERY = """
MATCH (m:Member {id: $member_id})
MATCH (e:Exercise)
WHERE NOT EXISTS {
    MATCH (m)-[:HAS_INJURY]->(inj:Injury)-[:CONTRAINDICATED_BY]->(e)
}
RETURN
    e.id              AS id,
    e.name            AS name,
    e.muscle_groups   AS muscle_groups,
    e.movement_patterns AS movement_patterns,
    e.equipment_required AS equipment_required,
    e.priority_tier   AS priority_tier,
    e.is_reps         AS is_reps,
    e.is_duration     AS is_duration,
    e.supports_weight AS supports_weight
ORDER BY e.priority_tier ASC, e.name ASC
"""

# Member profile: goals, equipment, availability, active injuries.
_MEMBER_PROFILE_QUERY = """
MATCH (m:Member {id: $member_id})
OPTIONAL MATCH (m)-[:HAS_INJURY]->(inj:Injury)
RETURN
    m.id              AS id,
    m.name            AS name,
    m.goals           AS goals,
    m.equipment       AS equipment,
    m.availability    AS availability,
    m.fitness_level   AS fitness_level,
    collect(DISTINCT inj.name) AS injury_names
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def get_contraindicated_exercise_ids(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> set[str]:
    """
    Return the set of exercise IDs that are contraindicated for this member.

    Used by the Phase 5 injury safety gate to validate generated workouts.
    Returns an empty set if the member has no recorded injuries.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A set of exercise UUID strings.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _CONTRAINDICATED_IDS_QUERY, member_id=member_id
        )
        records = await result.data()

    ids = {r["exercise_id"] for r in records}
    logger.debug(
        "Member %s has %d contraindicated exercise(s).", member_id, len(ids)
    )
    return ids


async def get_safe_exercises(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> list[dict[str, Any]]:
    """
    Return all exercises that are NOT contraindicated for this member.

    Results are ordered by priority_tier ASC (lower = higher priority),
    then alphabetically by name.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A list of dicts, each containing:
            id, name, muscle_groups, movement_patterns,
            equipment_required, priority_tier, is_reps,
            is_duration, supports_weight
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _SAFE_EXERCISES_QUERY, member_id=member_id
        )
        records = await result.data()

    logger.debug(
        "Member %s: %d safe exercise(s) found.", member_id, len(records)
    )
    return records


async def get_member_profile(
    member_id: str,
    driver: AsyncDriver,
    database: str = "neo4j",
) -> dict[str, Any] | None:
    """
    Return a member's profile: goals, equipment, availability, injuries.

    Used by the context assembler (TASK-058) to populate the member
    profile section of the retrieval context slice.

    Args:
        member_id: The Member node's `id` property (UUID string).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").

    Returns:
        A dict with keys: id, name, goals, equipment, availability,
        fitness_level, injury_names. Returns None if the member is not found.
    """
    async with driver.session(database=database) as session:
        result = await session.run(
            _MEMBER_PROFILE_QUERY, member_id=member_id
        )
        record = await result.single()

    if record is None:
        logger.warning("Member %s not found in Neo4j.", member_id)
        return None

    return dict(record)
```

- [x] `backend/app/knowledge_graph/traversal.py` created with all three functions: `get_contraindicated_exercise_ids`, `get_safe_exercises`, `get_member_profile` <!-- Completed: 2026-06-06 -->
- [x] `_CONTRAINDICATED_IDS_QUERY` traverses `Member -[HAS_INJURY]-> Injury <-[CONTRAINDICATED_BY]- Exercise` (corrected edge direction per ingest_injuries.py: Exercise→Injury) <!-- Completed: 2026-06-06 -->
- [x] `_SAFE_EXERCISES_QUERY` uses `WHERE NOT EXISTS` subquery to exclude contraindicated exercises <!-- Completed: 2026-06-06 -->
- [x] `_MEMBER_PROFILE_QUERY` collects injury names via `OPTIONAL MATCH` <!-- Completed: 2026-06-06 -->
- [x] All functions accept `member_id: str`, `driver: AsyncDriver`, `database: str = "neo4j"` <!-- Completed: 2026-06-06 -->

### 3. Write unit tests for traversal queries  <!-- agent: general-purpose -->

Create `backend/tests/kg/test_traversal.py`. Ensure `backend/tests/kg/__init__.py` exists (TASK-055 may have created it; check with `mcp__serena__list_dir` on `backend/tests/kg/` before creating).

All tests must mock the Neo4j driver — do not require a live connection.

Test cases to implement using `pytest` + `unittest.mock.AsyncMock`:

```python
# test_get_contraindicated_ids_returns_set
# Mock driver.session().__aenter__().run().data() to return
#   [{"exercise_id": "ex-1"}, {"exercise_id": "ex-2"}]
# Assert get_contraindicated_exercise_ids("member-1", mock_driver)
#   returns {"ex-1", "ex-2"}

# test_get_contraindicated_ids_empty_when_no_injuries
# Mock run().data() to return []
# Assert result is set() (empty set)

# test_get_safe_exercises_returns_list_of_dicts
# Mock run().data() to return two exercise dicts
# Assert get_safe_exercises("member-1", mock_driver) returns a list of length 2
# Assert each element has keys: id, name, muscle_groups

# test_get_safe_exercises_empty_when_all_contraindicated
# Mock run().data() to return []
# Assert result is []

# test_get_member_profile_returns_dict
# Mock run().single() to return a mock record that converts to dict
# Assert get_member_profile("member-1", mock_driver) is not None
# Assert result["id"] == "member-1"

# test_get_member_profile_returns_none_when_not_found
# Mock run().single() to return None
# Assert get_member_profile("member-1", mock_driver) is None
```

Use `pytest-asyncio` with `@pytest.mark.asyncio` on each test. The `backend/pyproject.toml` should already have `pytest-asyncio` as a dev dependency (added by earlier tasks); if not, add it.

- [x] `backend/tests/knowledge_graph/__init__.py` exists (already present from prior tasks) <!-- Completed: 2026-06-06 -->
- [x] `backend/tests/knowledge_graph/test_traversal.py` created with 8 test functions <!-- Completed: 2026-06-06 -->
- [x] All tests use `AsyncMock` for the Neo4j driver — no live connection required <!-- Completed: 2026-06-06 -->
- [x] All tests run under `asyncio_mode = "auto"` (set in pyproject.toml; explicit decorator not required) <!-- Completed: 2026-06-06 -->

### 4. Run the test suite  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_traversal.py -v
```

Fix any failures. Common issues:
- `pytest-asyncio` not installed → `pip install -e ".[dev]"`
- `asyncio_mode` not set → check `backend/pyproject.toml` for `[tool.pytest.ini_options]` `asyncio_mode = "auto"` or add `@pytest.mark.asyncio` decorator explicitly
- `neo4j` package not installed → already a dependency from TASK-041/042; verify with `pip show neo4j`

- [x] `pytest tests/knowledge_graph/test_traversal.py` exits with 0 failures — 8 passed in 0.28s <!-- Completed: 2026-06-06 -->

### 5. Update the roadmap  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md`. Replace the inline placeholder:

```
- [ ] Graph traversal queries: injury-aware filtering (Member → HAS_INJURY → joints_loaded → Exercise → CONTRAINDICATED_BY)
```

with:

```
- [ ] [TASK-056: Graph traversal queries — injury-aware exercise filtering](../tasks/056-injury-traversal-queries.md)
```

Use the `Edit` tool. Update `**Last updated**` to `2026-06-06`.

- [x] Roadmap already had task link; updated `**Last updated**` to 2026-06-06 (TASK-056 complete) <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/knowledge_graph/traversal.py` exists with `get_contraindicated_exercise_ids`, `get_safe_exercises`, `get_member_profile`
- [x] `get_safe_exercises` returns exercises ordered by `priority_tier ASC, name ASC`
- [x] `get_contraindicated_exercise_ids` returns a `set[str]` (not a list)
- [x] `get_member_profile` returns `None` (not an exception) when member is not found
- [x] All three Cypher queries use parameterized variables (`$member_id`) — no string interpolation
- [x] `backend/tests/knowledge_graph/test_traversal.py` exists with 8 mocked async tests, all passing
- [x] Roadmap TASK-056 link already present in Phase 4; `**Last updated**` refreshed

---
**UAT**: [`.docs/uat/056-injury-traversal-queries.uat.md`](../uat/056-injury-traversal-queries.uat.md)
