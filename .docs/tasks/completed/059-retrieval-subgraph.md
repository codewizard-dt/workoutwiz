# 059 — Retrieval Sub-Graph: LangGraph StateGraph Wrapping Traversal and Vector Search

> **Depends on**: [055-vector-embeddings](055-vector-embeddings.md), [056-injury-traversal-queries](056-injury-traversal-queries.md), [057-preference-feedback-traversal](057-preference-feedback-traversal.md), [058-context-assembler](058-context-assembler.md)
> **Blocks**: none
> **Parallel-safe with**: [049-injury-ingestion](049-injury-ingestion.md), [050-exercise-neo4j-ingestion](050-exercise-neo4j-ingestion.md), [051-member-profile-ingestion](051-member-profile-ingestion.md), [052-ingest-workout-history-neo4j](052-ingest-workout-history-neo4j.md), [053-feedback-ingestion-neo4j](053-feedback-ingestion-neo4j.md), [054-graphrag-adr](054-graphrag-adr.md)

## Objective

Create `backend/app/kg/retrieval_graph.py` — a LangGraph `StateGraph` that orchestrates the full GraphRAG retrieval pipeline as a composable sub-graph — and wire a `KNOWLEDGE_GRAPH` intent route into the existing hub `StateGraph` in `backend/app/agents/hub.py` without modifying any existing COACH / WORKOUT_GENERATE / WORKOUT_LOG paths.

## Approach

The retrieval sub-graph is a `StateGraph` with typed state (`RetrievalState`) and 5 nodes that run sequentially. The context assembler (TASK-058) already does the heavy lifting — the graph's job is to wrap it in the LangGraph execution model so it can be composed with the hub and invoked via `.ainvoke()`.

**Node sequence:**
1. `lookup_member` — calls `get_member_profile()` and writes result to state; raises `ValueError` if member not found
2. `run_injury_traversal` — calls `get_contraindicated_exercise_ids()` and `get_safe_exercises()`, writes to state
3. `run_preference_traversal` — calls `get_preferred_exercises()` and `get_performed_exercises()`, writes to state
4. `run_vector_search` — calls `get_exercise_vector_store().similarity_search()`, writes docs to state
5. `assemble` — calls `assemble_context()` and writes the `ContextSlice` to state as `context`

After `assemble`, the graph hits `END`.

**State design**: `RetrievalState` is a `TypedDict` with optional fields that get populated as nodes run. The final state contains `context: ContextSlice`.

**Hub integration**: Add `KNOWLEDGE_GRAPH` to the `RouteIntent` enum in the shared state module (`backend/app/agents/state.py` or wherever the enum lives — check with Serena). Add a `knowledge_graph_node` to the hub graph that calls `retrieval_graph.ainvoke()`. Add the conditional edge routing `KNOWLEDGE_GRAPH → knowledge_graph_node`. No changes to existing COACH / WORKOUT_GENERATE / WORKOUT_LOG nodes or edges.

**Neo4j driver injection**: The retrieval graph needs an async Neo4j driver. Pass it at graph construction time via a closure: `build_retrieval_graph(driver: AsyncDriver) -> CompiledGraph`. The hub node calls this with the driver from `backend/app/main.py`'s lifespan context.

## Steps

### 1. Inspect the existing hub and state module structure  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on:
- `backend/app/agents/hub.py` — find the hub `StateGraph`, `RouteIntent` enum, and existing node functions
- `backend/app/agents/state.py` (or wherever `RouteIntent` / shared state lives — use `mcp__serena__find_file` with `state.py` in `backend/app/agents/` to locate it)

Note:
1. The exact module path where `RouteIntent` is defined
2. The existing intent values (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK)
3. How the hub graph is built and compiled (look for `StateGraph`, `add_node`, `add_conditional_edges`)
4. How the hub is exported / used in `main.py` or `chat.py`

This determines exactly where to add `KNOWLEDGE_GRAPH` without breaking existing paths.

- [x] `RouteIntent` enum location confirmed — it's `Intent` (StrEnum) in `backend/app/agents/state.py` <!-- Completed: 2026-06-06 -->
- [x] Existing hub node names and edge structure confirmed — nodes: router, clarification, coach, workout_gen, workout_log; routing dict uses string keys <!-- Completed: 2026-06-06 -->
- [x] Hub graph export pattern confirmed — `build_hub_graph()` factory + module-level `hub` compiled instance <!-- Completed: 2026-06-06 -->

### 2. Create `backend/app/kg/retrieval_graph.py`  <!-- agent: general-purpose -->

Create the file using the `Write` tool:

```python
"""
GraphRAG retrieval sub-graph.

A LangGraph StateGraph that orchestrates member profile lookup,
injury-aware filtering, preference traversal, vector search, and
context assembly into a single composable graph.

Usage:
    from backend.app.kg.retrieval_graph import build_retrieval_graph

    graph = build_retrieval_graph(driver)
    result = await graph.ainvoke({"member_id": "...", "query": "build a leg workout"})
    context = result["context"]  # ContextSlice
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, TypedDict

from langgraph.graph import StateGraph, END
from neo4j import AsyncDriver

from backend.app.kg.context_assembler import ContextSlice, assemble_context
from backend.app.kg.traversal import (
    get_member_profile,
    get_safe_exercises,
    get_contraindicated_exercise_ids,
    get_preferred_exercises,
    get_performed_exercises,
)
from backend.app.kg.embeddings import get_exercise_vector_store

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Typed state
# ---------------------------------------------------------------------------

class RetrievalState(TypedDict, total=False):
    """State flowing through the retrieval sub-graph."""
    # Inputs (required)
    member_id: str
    query: str
    # Populated by lookup_member node
    member_profile: dict[str, Any] | None
    # Populated by run_injury_traversal node
    contraindicated_ids: set[str]
    safe_exercises: list[dict[str, Any]]
    # Populated by run_preference_traversal node
    preferred_exercises: list[dict[str, Any]]
    performed_exercises: list[dict[str, Any]]
    # Populated by run_vector_search node
    vector_docs: list[Any]
    # Populated by assemble node (final output)
    context: ContextSlice | None
    # Error message if any node fails non-fatally
    error: str | None


# ---------------------------------------------------------------------------
# Node factory (captures driver in closure)
# ---------------------------------------------------------------------------

def _make_nodes(driver: AsyncDriver):
    """Return node functions bound to the given Neo4j driver."""

    async def lookup_member(state: RetrievalState) -> dict:
        member_id = state["member_id"]
        profile = await get_member_profile(member_id, driver)
        if profile is None:
            raise ValueError(f"Member '{member_id}' not found in Neo4j.")
        return {"member_profile": profile}

    async def run_injury_traversal(state: RetrievalState) -> dict:
        member_id = state["member_id"]
        contraindicated, safe = await asyncio.gather(
            get_contraindicated_exercise_ids(member_id, driver),
            get_safe_exercises(member_id, driver),
        )
        return {"contraindicated_ids": contraindicated, "safe_exercises": safe}

    async def run_preference_traversal(state: RetrievalState) -> dict:
        member_id = state["member_id"]
        preferred, performed = await asyncio.gather(
            get_preferred_exercises(member_id, driver),
            get_performed_exercises(member_id, driver),
        )
        return {"preferred_exercises": preferred, "performed_exercises": performed}

    async def run_vector_search(state: RetrievalState) -> dict:
        query = state.get("query", "")
        try:
            vector_store = get_exercise_vector_store()
            loop = asyncio.get_event_loop()
            docs = await loop.run_in_executor(
                None, lambda: vector_store.similarity_search(query, k=10)
            )
            return {"vector_docs": docs}
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return {"vector_docs": [], "error": str(exc)}

    async def assemble(state: RetrievalState) -> dict:
        member_id = state["member_id"]
        query = state.get("query", "")
        # Delegate to context assembler — it handles dedup and budget
        context = await assemble_context(member_id, query, driver)
        return {"context": context}

    return lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, assemble


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

def build_retrieval_graph(driver: AsyncDriver):
    """
    Build and compile the retrieval sub-graph.

    Args:
        driver: An open neo4j.AsyncDriver instance (injected at build time).

    Returns:
        A compiled LangGraph graph. Invoke with:
            result = await graph.ainvoke({"member_id": "...", "query": "..."})
            context_slice = result["context"]
    """
    lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, assemble = (
        _make_nodes(driver)
    )

    builder = StateGraph(RetrievalState)

    builder.add_node("lookup_member", lookup_member)
    builder.add_node("run_injury_traversal", run_injury_traversal)
    builder.add_node("run_preference_traversal", run_preference_traversal)
    builder.add_node("run_vector_search", run_vector_search)
    builder.add_node("assemble", assemble)

    builder.set_entry_point("lookup_member")
    builder.add_edge("lookup_member", "run_injury_traversal")
    builder.add_edge("run_injury_traversal", "run_preference_traversal")
    builder.add_edge("run_preference_traversal", "run_vector_search")
    builder.add_edge("run_vector_search", "assemble")
    builder.add_edge("assemble", END)

    return builder.compile()
```

- [x] `RetrievalState` TypedDict defined with all fields <!-- Completed: 2026-06-06 -->
- [x] `_make_nodes(driver)` factory returns 5 node functions bound to the driver <!-- Completed: 2026-06-06 -->
- [x] `build_retrieval_graph(driver)` assembles and compiles the `StateGraph` <!-- Completed: 2026-06-06 -->
- [x] Node sequence: `lookup_member → run_injury_traversal → run_preference_traversal → run_vector_search → assemble → END` <!-- Completed: 2026-06-06 -->
- [x] `asyncio.gather()` used within `run_injury_traversal` and `run_preference_traversal` nodes <!-- Completed: 2026-06-06 -->
- [x] `run_vector_search` handles exceptions and sets `error` field on failure (does not raise) <!-- Completed: 2026-06-06 -->

### 3. Add `KNOWLEDGE_GRAPH` intent to the shared state/enum module  <!-- agent: general-purpose -->

Use Serena `find_symbol` to locate the `RouteIntent` enum (or equivalent) in the agents package. Use Serena `replace_content` or `insert_after_symbol` to add `KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"` to the enum, after the existing values.

Do NOT change any existing enum values or their string representations.

- [x] `KNOWLEDGE_GRAPH` value added to `Intent` enum (in `backend/app/agents/state.py`) <!-- Completed: 2026-06-06 -->
- [x] Existing values (COACH, WORKOUT_GENERATE, WORKOUT_LOG, FALLBACK) unchanged <!-- Completed: 2026-06-06 -->

### 4. Add the `knowledge_graph_node` to the hub graph  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `backend/app/agents/hub.py` to understand its structure. Then:

**4a. Add the node function** — insert a new `knowledge_graph_node` async function. This function receives hub state, extracts `member_id` and `message` (the user's query), builds the retrieval graph with the driver from settings/config, invokes it, and writes the `ContextSlice` back to hub state. Pattern:

```python
async def knowledge_graph_node(state: HubState) -> dict:
    """Invoke the GraphRAG retrieval sub-graph for KNOWLEDGE_GRAPH intent."""
    from backend.app.kg.retrieval_graph import build_retrieval_graph
    from backend.app.config import settings
    import neo4j

    member_id = state.get("member_id") or "default-member"  # adjust to actual state key
    query = state.get("messages", [{}])[-1].get("content", "") if state.get("messages") else ""

    async with neo4j.AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
    ) as driver:
        retrieval_graph = build_retrieval_graph(driver)
        result = await retrieval_graph.ainvoke(
            {"member_id": member_id, "query": query}
        )

    return {"kg_context": result.get("context")}
```

Adjust `state.get("member_id")` and the message extraction to match the actual `HubState` field names confirmed in step 1.

**4b. Register the node** — use `add_node("knowledge_graph", knowledge_graph_node)` on the hub builder. Find where other nodes are added with Serena and insert after the last existing `add_node` call.

**4c. Add the conditional edge** — find the `add_conditional_edges` call that routes by intent. Add `RouteIntent.KNOWLEDGE_GRAPH: "knowledge_graph"` (or the equivalent string key) to the routing dict. Do NOT change the routing for COACH, WORKOUT_GENERATE, WORKOUT_LOG, or FALLBACK.

Use Serena's `replace_content` (literal or regex mode) for all edits to `hub.py`.

- [x] `knowledge_graph_node` function added to `backend/app/agents/hub.py` (as `_knowledge_graph_node`) <!-- Completed: 2026-06-06 -->
- [x] Node registered with `add_node("knowledge_graph", _knowledge_graph_node)` <!-- Completed: 2026-06-06 -->
- [x] `KNOWLEDGE_GRAPH` added to the routing dict in `_route_selector` and to `add_conditional_edges`; `knowledge_graph → END` edge added <!-- Completed: 2026-06-06 -->
- [x] No existing node, edge, or routing entry modified <!-- Completed: 2026-06-06 -->

### 5. Write unit tests for the retrieval sub-graph  <!-- agent: general-purpose -->

Create `backend/tests/kg/test_retrieval_graph.py`.

Test cases (all mocked — no live Neo4j):

```python
# test_build_retrieval_graph_returns_compiled_graph
# Call build_retrieval_graph(mock_driver)
# Assert the returned object has an .ainvoke method

# test_retrieval_graph_invokes_assemble_context
# Patch assemble_context to return a fixed ContextSlice
# Patch all traversal functions to return valid data
# Patch get_member_profile to return a dict (member found)
# Call graph.ainvoke({"member_id": "m1", "query": "leg workout"})
# Assert result["context"] is not None

# test_retrieval_graph_raises_when_member_not_found
# Patch get_member_profile to return None
# Assert graph.ainvoke() raises ValueError

# test_vector_search_failure_does_not_fail_graph
# Patch get_exercise_vector_store().similarity_search to raise RuntimeError
# Patch all traversal functions and assemble_context to return valid data
# Assert graph.ainvoke() completes successfully (vector failure is non-fatal)

# test_knowledge_graph_intent_in_route_intent_enum
# Import RouteIntent from the agents state module
# Assert hasattr(RouteIntent, "KNOWLEDGE_GRAPH")
```

- [x] `backend/tests/kg/test_retrieval_graph.py` created with 5 test functions <!-- Completed: 2026-06-06 -->
- [x] All tests use mocks — no live connections <!-- Completed: 2026-06-06 -->
- [x] `test_knowledge_graph_intent_in_route_intent_enum` verifies the enum was updated <!-- Completed: 2026-06-06 -->

### 6. Run the full kg test suite  <!-- agent: general-purpose -->

```bash
set -a && source .env && set +a && cd backend && python -m pytest tests/kg/ -v
```

All kg tests (embeddings, traversal, context_assembler, retrieval_graph) must pass.

Also run a quick import check on hub.py:
```bash
set -a && source .env && set +a && cd backend && python -c "from backend.app.agents.hub import hub_graph; print('hub import OK')"
```

Fix any import errors or test failures.

- [x] All `tests/kg/` tests pass with 0 failures (18/18 passed) <!-- Completed: 2026-06-06 -->
- [x] Hub import check passes without errors <!-- Completed: 2026-06-06 -->

### 7. Update the roadmap  <!-- agent: general-purpose -->

Read `.docs/roadmaps/004-knowledge-graph-coaching-system.md`. Replace the inline placeholder:

```
- [ ] Retrieval sub-graph: LangGraph StateGraph wrapping traversal + vector search
```

with:

```
- [ ] [TASK-059: Retrieval sub-graph — LangGraph StateGraph wrapping traversal and vector search](../tasks/059-retrieval-subgraph.md)
```

Use the `Edit` tool. Update `**Last updated**` to `2026-06-06`.

- [x] Roadmap placeholder replaced with task link (was already present; updated Last updated to 2026-06-06 TASK-059) <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `backend/app/kg/retrieval_graph.py` exists with `RetrievalState`, `_make_nodes()`, and `build_retrieval_graph()` <!-- Completed: 2026-06-06 -->
- [x] `build_retrieval_graph(driver).ainvoke({"member_id": ..., "query": ...})` returns a dict with `context: ContextSlice` <!-- Completed: 2026-06-06 -->
- [x] Node sequence is sequential: `lookup_member → run_injury_traversal → run_preference_traversal → run_vector_search → assemble → END` <!-- Completed: 2026-06-06 -->
- [x] `KNOWLEDGE_GRAPH` added to `Intent` enum; existing values unchanged <!-- Completed: 2026-06-06 -->
- [x] `_knowledge_graph_node` added to hub graph with `add_node` and routing dict updated <!-- Completed: 2026-06-06 -->
- [x] No existing hub node, edge, or routing entry modified <!-- Completed: 2026-06-06 -->
- [x] `backend/tests/kg/test_retrieval_graph.py` with 5 tests, all passing <!-- Completed: 2026-06-06 -->
- [x] All `tests/kg/` tests pass (`pytest tests/kg/ -v` exits 0 — 18/18 passed) <!-- Completed: 2026-06-06 -->
- [x] Hub imports without error after changes <!-- Completed: 2026-06-06 -->
- [x] Roadmap TASK-059 link replaces the inline Phase 4 placeholder <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/059-retrieval-subgraph.uat.md`](../uat/059-retrieval-subgraph.uat.md)
