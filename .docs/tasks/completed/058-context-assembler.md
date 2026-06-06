# 058 — Context Assembler: Merge Traversal Results and Vector Hits into Token-Budget Context

> **Depends on**: [055-vector-embeddings](055-vector-embeddings.md), [057-preference-feedback-traversal](057-preference-feedback-traversal.md)
> **Blocks**: [059-retrieval-subgraph](059-retrieval-subgraph.md)
> **Parallel-safe with**: [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md), [054-graphrag-adr](054-graphrag-adr.md), [056-injury-traversal-queries](056-injury-traversal-queries.md)

## Objective

Create `backend/app/kg/context_assembler.py` with an `assemble_context(member_id, query, driver)` async function that orchestrates all graph traversal and vector search calls, deduplicates results across sources, enforces the 2 048-token context budget defined in ADR-001 D3, and returns a structured context dict ready for injection into the generation agent prompt.

## Approach

The context assembler is the integration point between the graph retrieval layer (traversal.py, embeddings.py) and the generation agent. It has one public function: `assemble_context()`. Internally it:

1. Calls all four traversal functions in parallel (using `asyncio.gather`): `get_member_profile()`, `get_safe_exercises()`, `get_preferred_exercises()`, `get_performed_exercises()`
2. Calls `get_exercise_vector_store().similarity_search(query, k=10)` for semantic hits
3. Deduplicates: preferred and performed exercises are filtered out of vector_hits if already present (dedup key: exercise `id`). Safe exercises set is the authoritative filter — exercises NOT in the safe set are removed from preferred and vector_hits lists.
4. Applies per-section token budgets (from ADR-001 D3):
   - `member_profile`: 200 tokens — serialize as compact JSON, truncate if oversized
   - `safe_exercises`: 600 tokens — include up to N exercises that fit (~10 × 60 tokens each)
   - `preferred_exercises`: 400 tokens — include top-rated first
   - `vector_hits`: 400 tokens — include highest-similarity first
   - Buffer: 448 tokens (not allocated to any section)
5. Returns a `ContextSlice` TypedDict with keys: `member_profile`, `safe_exercises`, `preferred_exercises`, `vector_hits`, `token_counts` (dict of per-section counts)

**Token counting**: Use a simple character-based approximation (1 token ≈ 4 characters) rather than a full tokenizer — fast, dependency-free, good enough for budget enforcement. A constant `CHARS_PER_TOKEN = 4` makes this easy to adjust.

**Error resilience**: If any individual traversal call fails (e.g., Neo4j unavailable), log the error and return an empty list for that section rather than propagating the exception. The assembler must never raise unless `member_profile` itself fails (that's a hard requirement — we need the member to exist).

## Steps

### 1. Define the `ContextSlice` TypedDict in `backend/app/kg/context_assembler.py`  <!-- agent: general-purpose -->

Create the file using the `Write` tool. Start with the TypedDict and constants:

```python
"""
Context assembler for the GraphRAG retrieval layer.

Orchestrates graph traversal + vector search, deduplicates results,
enforces the 2 048-token budget from ADR-001 D3, and returns a
structured context slice for the generation agent.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, TypedDict

from neo4j import AsyncDriver

from backend.app.kg.traversal import (
    get_member_profile,
    get_safe_exercises,
    get_preferred_exercises,
    get_performed_exercises,
)
from backend.app.kg.embeddings import get_exercise_vector_store

logger = logging.getLogger(__name__)

# Token budget constants (ADR-001 D3)
TOTAL_TOKEN_BUDGET = 2048
MEMBER_PROFILE_BUDGET = 200
SAFE_EXERCISES_BUDGET = 600
PREFERRED_EXERCISES_BUDGET = 400
VECTOR_HITS_BUDGET = 400

# Approximation: 1 token ≈ 4 characters (adjust if needed)
CHARS_PER_TOKEN = 4


class SectionTokenCounts(TypedDict):
    member_profile: int
    safe_exercises: int
    preferred_exercises: int
    vector_hits: int
    total: int


class ContextSlice(TypedDict):
    member_profile: dict[str, Any] | None
    safe_exercises: list[dict[str, Any]]
    preferred_exercises: list[dict[str, Any]]
    vector_hits: list[dict[str, Any]]
    token_counts: SectionTokenCounts
```

- [x] File created with `ContextSlice` TypedDict and all budget constants <!-- Completed: 2026-06-06 -->

### 2. Implement the token-budget truncation helper  <!-- agent: general-purpose -->

Add the following helper functions to `backend/app/kg/context_assembler.py`:

```python
def _estimate_tokens(obj: Any) -> int:
    """Estimate the token count of a serializable object using char approximation."""
    try:
        text = json.dumps(obj, default=str)
    except (TypeError, ValueError):
        text = str(obj)
    return max(1, len(text) // CHARS_PER_TOKEN)


def _truncate_to_budget(
    items: list[dict[str, Any]],
    budget_tokens: int,
) -> tuple[list[dict[str, Any]], int]:
    """
    Return the longest prefix of `items` that fits within `budget_tokens`.

    Returns (truncated_list, actual_tokens_used).
    Items are included greedily from the front of the list (caller is
    responsible for ordering by priority before calling this function).
    """
    selected: list[dict[str, Any]] = []
    used = 0
    for item in items:
        cost = _estimate_tokens(item)
        if used + cost > budget_tokens:
            break
        selected.append(item)
        used += cost
    return selected, used
```

- [x] `_estimate_tokens()` implemented using `json.dumps` + `CHARS_PER_TOKEN` <!-- Completed: 2026-06-06 -->
- [x] `_truncate_to_budget()` implemented with greedy prefix selection <!-- Completed: 2026-06-06 -->

### 3. Implement `assemble_context()`  <!-- agent: general-purpose -->

Add the main public function:

```python
async def assemble_context(
    member_id: str,
    query: str,
    driver: AsyncDriver,
    database: str = "neo4j",
    vector_k: int = 10,
) -> ContextSlice:
    """
    Assemble a token-budgeted context slice for the generation agent.

    Orchestrates:
    1. Graph traversal (member profile, safe exercises, preferred, performed)
    2. Vector similarity search
    3. Deduplication (preferred + vector_hits filtered against safe set)
    4. Token budget enforcement per section (ADR-001 D3)

    Args:
        member_id: The Member node's `id` property (UUID string).
        query: The user's workout query (used for vector similarity search).
        driver: An open neo4j.AsyncDriver instance.
        database: Neo4j database name (default: "neo4j").
        vector_k: Number of vector similarity candidates to fetch (default: 10).

    Returns:
        A ContextSlice TypedDict with all sections and token_counts.

    Raises:
        ValueError: If the member is not found in Neo4j (member_profile is None).
    """
    # Step 1: Run all traversals in parallel
    (
        member_profile,
        safe_exercises_raw,
        preferred_raw,
        performed_raw,
    ) = await asyncio.gather(
        get_member_profile(member_id, driver, database=database),
        get_safe_exercises(member_id, driver, database=database),
        _safe_call(get_preferred_exercises, member_id, driver, database=database),
        _safe_call(get_performed_exercises, member_id, driver, database=database),
    )

    if member_profile is None:
        raise ValueError(f"Member '{member_id}' not found in Neo4j knowledge graph.")

    # Step 2: Vector similarity search
    vector_docs = await _safe_vector_search(query, k=vector_k)

    # Step 3: Build the safe exercise ID set for deduplication
    safe_ids: set[str] = {e["id"] for e in safe_exercises_raw}

    # Combine preferred + performed, deduplicated by id, filtered to safe set
    seen_preferred: set[str] = set()
    preferred_deduped: list[dict[str, Any]] = []
    for ex in preferred_raw + performed_raw:
        ex_id = ex.get("id")
        if ex_id and ex_id in safe_ids and ex_id not in seen_preferred:
            preferred_deduped.append(ex)
            seen_preferred.add(ex_id)

    # Filter vector hits to safe set and deduplicate against preferred
    vector_hits_filtered: list[dict[str, Any]] = []
    for doc in vector_docs:
        ex_id = doc.get("id") or (doc.metadata.get("id") if hasattr(doc, "metadata") else None)
        if ex_id and ex_id in safe_ids and ex_id not in seen_preferred:
            vector_hits_filtered.append(
                {"id": ex_id, "name": doc.page_content, "score": doc.metadata.get("score")}
                if hasattr(doc, "page_content")
                else doc
            )

    # Step 4: Apply per-section token budgets
    profile_tokens = _estimate_tokens(member_profile)
    if profile_tokens > MEMBER_PROFILE_BUDGET:
        # Trim to essential fields only
        member_profile = {
            k: member_profile[k]
            for k in ("id", "name", "goals", "equipment", "fitness_level", "injury_names")
            if k in member_profile
        }
        profile_tokens = _estimate_tokens(member_profile)

    safe_truncated, safe_tokens = _truncate_to_budget(safe_exercises_raw, SAFE_EXERCISES_BUDGET)
    preferred_truncated, preferred_tokens = _truncate_to_budget(preferred_deduped, PREFERRED_EXERCISES_BUDGET)
    vector_truncated, vector_tokens = _truncate_to_budget(vector_hits_filtered, VECTOR_HITS_BUDGET)

    total_tokens = profile_tokens + safe_tokens + preferred_tokens + vector_tokens
    logger.info(
        "Context assembled for member %s: profile=%d, safe=%d, preferred=%d, vector=%d, total=%d tokens",
        member_id, profile_tokens, safe_tokens, preferred_tokens, vector_tokens, total_tokens,
    )

    return ContextSlice(
        member_profile=member_profile,
        safe_exercises=safe_truncated,
        preferred_exercises=preferred_truncated,
        vector_hits=vector_truncated,
        token_counts=SectionTokenCounts(
            member_profile=profile_tokens,
            safe_exercises=safe_tokens,
            preferred_exercises=preferred_tokens,
            vector_hits=vector_tokens,
            total=total_tokens,
        ),
    )
```

- [x] `assemble_context()` implemented with all 4 steps (parallel gather, vector search, dedup, budget) <!-- Completed: 2026-06-06 -->
- [x] `asyncio.gather()` used for parallel traversal calls <!-- Completed: 2026-06-06 -->
- [x] Safe ID set used as the deduplication gate for preferred and vector_hits <!-- Completed: 2026-06-06 -->
- [x] `ValueError` raised (not caught) when `member_profile` is None <!-- Completed: 2026-06-06 -->

### 4. Implement error-resilient helper callees  <!-- agent: general-purpose -->

Add the private helpers that make individual traversal and vector calls fault-tolerant:

```python
async def _safe_call(fn, *args, **kwargs) -> list[dict[str, Any]]:
    """Call an async traversal function; return [] on any exception."""
    try:
        return await fn(*args, **kwargs)
    except Exception as exc:
        logger.warning("Traversal function %s failed: %s", fn.__name__, exc)
        return []


async def _safe_vector_search(query: str, k: int) -> list[Any]:
    """Run vector similarity search; return [] if vector store is unavailable."""
    try:
        vector_store = get_exercise_vector_store()
        # Neo4jVector.similarity_search is synchronous — run in thread pool
        loop = asyncio.get_event_loop()
        docs = await loop.run_in_executor(
            None, lambda: vector_store.similarity_search(query, k=k)
        )
        return docs
    except Exception as exc:
        logger.warning("Vector similarity search failed: %s", exc)
        return []
```

Place these helpers above `assemble_context()` in the file (they are called by it).

- [x] `_safe_call()` wraps any traversal function and returns `[]` on exception <!-- Completed: 2026-06-06 -->
- [x] `_safe_vector_search()` wraps vector store similarity search and returns `[]` on exception <!-- Completed: 2026-06-06 -->
- [x] `similarity_search()` (synchronous) is run via `run_in_executor` to avoid blocking the event loop <!-- Completed: 2026-06-06 -->

### 5. Write unit tests for the context assembler  <!-- agent: general-purpose -->

Create `backend/tests/kg/test_context_assembler.py`. Tests must use `AsyncMock` and `unittest.mock.patch` — no live Neo4j or embedding model calls.

Test cases:

```python
# test_assemble_context_returns_context_slice
# Patch all 4 traversal functions to return fixed lists
# Patch _safe_vector_search to return []
# Call assemble_context("m1", "build a leg workout", mock_driver)
# Assert result is a dict with keys: member_profile, safe_exercises,
#   preferred_exercises, vector_hits, token_counts
# Assert token_counts["total"] > 0

# test_assemble_context_raises_when_member_not_found
# Patch get_member_profile to return None
# Assert assemble_context() raises ValueError

# test_deduplication_removes_preferred_from_vector_hits
# Patch traversals: safe_exercises = [{"id": "ex-1", ...}]
#   preferred_raw = [{"id": "ex-1", ...}]   (same as safe)
#   performed_raw = []
# Patch _safe_vector_search to return docs with id="ex-1" and id="ex-2"
# Assert vector_hits in result does NOT contain ex-1 (already in preferred)
# Assert vector_hits contains ex-2 (if ex-2 is in safe set)

# test_deduplication_filters_unsafe_exercises_from_preferred
# safe_exercises = [{"id": "ex-safe"}]
# preferred_raw = [{"id": "ex-unsafe"}]   (not in safe set)
# Assert preferred_exercises in result is empty

# test_token_budget_truncates_safe_exercises
# Patch get_safe_exercises to return 100 large exercise dicts
# Assert len(result["safe_exercises"]) < 100
# Assert result["token_counts"]["safe_exercises"] <= SAFE_EXERCISES_BUDGET

# test_safe_call_returns_empty_list_on_exception
# Define an async fn that raises RuntimeError
# Assert await _safe_call(raising_fn) returns []

# test_estimate_tokens_approximation
# Assert _estimate_tokens({"name": "Squat"}) > 0
# Assert _estimate_tokens([]) == 1  (empty list → "[]" → 2 chars → max(1, 0) = 1)
```

- [x] `backend/tests/kg/test_context_assembler.py` created with ≥7 test functions <!-- Completed: 2026-06-06 -->
- [x] All tests use mocks — no live connections <!-- Completed: 2026-06-06 -->
- [x] `test_deduplication_*` tests verify the dedup logic specifically <!-- Completed: 2026-06-06 -->
- [x] `test_token_budget_truncates_*` verifies budget enforcement <!-- Completed: 2026-06-06 -->

### 6. Run the test suite  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py -v
```

Fix any failures. Common issues:
- Import errors if TASK-055 or TASK-056/057 haven't been run yet — mock the imported modules in the test using `unittest.mock.patch`
- `asyncio.gather` with mixed sync/async → ensure all gathered functions are awaitable

- [x] `pytest tests/kg/test_context_assembler.py` exits with 0 failures <!-- Completed: 2026-06-06 -->

### 7. Update the roadmap  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md`. Replace the inline placeholder:

```
- [ ] Context assembler: merge traversal results + vector hits into a focused, token-efficient prompt context
```

with:

```
- [ ] [TASK-058: Context assembler — merge traversal results and vector hits into token-budget context](../tasks/058-context-assembler.md)
```

Use the `Edit` tool. Update `**Last updated**` to `2026-06-06`.

- [x] Roadmap placeholder replaced with task link <!-- Completed: 2026-06-06 (already linked in roadmap) -->

## Acceptance Criteria

- [x] `backend/app/kg/context_assembler.py` exists with `ContextSlice` TypedDict, `SectionTokenCounts` TypedDict, `assemble_context()`, `_safe_call()`, `_safe_vector_search()`, `_estimate_tokens()`, `_truncate_to_budget()`
- [x] `assemble_context()` uses `asyncio.gather()` for parallel traversal calls
- [x] Deduplication gate: preferred and vector_hits are filtered to the safe exercise ID set
- [x] Exercises appearing in preferred are excluded from vector_hits
- [x] `assemble_context()` raises `ValueError` (not returns None) when member is not found
- [x] Each section is truncated to its ADR-001 D3 token budget
- [x] `token_counts` dict returned with per-section and total counts
- [x] `_safe_call()` and `_safe_vector_search()` return `[]` on exception (never raise)
- [x] `backend/tests/kg/test_context_assembler.py` with ≥7 tests, all passing
- [x] Roadmap TASK-058 link replaces the inline Phase 4 placeholder

---
**UAT**: [`.docs/uat/completed/058-context-assembler.uat.md`](../uat/completed/058-context-assembler.uat.md)
