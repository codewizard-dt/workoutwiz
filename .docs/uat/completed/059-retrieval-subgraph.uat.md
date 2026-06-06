# UAT: Retrieval Sub-Graph — LangGraph StateGraph Wrapping Traversal and Vector Search

> **Source task**: [`.docs/tasks/059-retrieval-subgraph.md`](../tasks/059-retrieval-subgraph.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python environment available with backend dependencies installed (`cd backend && pip install -e ".[dev]"`)
- [ ] `backend/app/kg/retrieval_graph.py` exists
- [ ] `backend/app/agents/hub.py` and `backend/app/agents/state.py` are present
- [ ] `backend/tests/kg/test_retrieval_graph.py` exists

---

## API Tests

_No HTTP endpoints were introduced or modified by this task. The retrieval sub-graph is an internal LangGraph component invoked from within the hub — it has no direct REST surface. Functional verification is covered by the unit test suite below._

---

## Unit / Module Tests

### UAT-UNIT-001: Full pytest suite for retrieval graph passes
- **Description**: Run the kg test suite and confirm all 5 retrieval-graph tests pass with zero failures.
- **Steps**:
  1. Run the command below from the repository root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py -v
  ```
- **Expected Result**: All 5 tests collected and pass (`5 passed`); exit code 0. Tests: `test_build_retrieval_graph_returns_compiled_graph`, `test_retrieval_graph_invokes_assemble_context`, `test_retrieval_graph_raises_when_member_not_found`, `test_vector_search_failure_does_not_fail_graph`, `test_knowledge_graph_intent_in_route_intent_enum`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: Full kg test suite passes (all tests, not just retrieval graph)
- **Description**: Confirm the full `tests/kg/` suite passes — embeddings, traversal, context_assembler, and retrieval_graph tests all green.
- **Steps**:
  1. Run the command below from the repository root
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/ -v
  ```
- **Expected Result**: All kg tests pass (`18 passed` or more); exit code 0; no failures or errors.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: `lookup_member` node raises ValueError for unknown member
- **Description**: When `get_member_profile` returns `None`, the retrieval graph's `lookup_member` node must raise `ValueError` with a message referencing the member ID — it must not silently continue or return a partial state.
- **Scenario**: `graph.ainvoke({"member_id": "missing-member", "query": "..."})` when member does not exist in Neo4j.
- **Steps**:
  1. This is covered by `test_retrieval_graph_raises_when_member_not_found` in `backend/tests/kg/test_retrieval_graph.py`.
  2. Run the specific test:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_raises_when_member_not_found -v
  ```
- **Expected Result**: Test passes. The test asserts that `graph.ainvoke({"member_id": "missing-member", ...})` raises `ValueError` (or a subclass). Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Vector search failure is non-fatal — graph completes with `error` field set
- **Description**: When `get_exercise_vector_store().similarity_search()` raises `RuntimeError`, the `run_vector_search` node must catch the exception, set `vector_docs: []` and `error: <str>` on state, and allow the graph to continue to `assemble` and complete successfully.
- **Scenario**: Simulated vector store failure during `run_vector_search` node execution.
- **Steps**:
  1. This is covered by `test_vector_search_failure_does_not_fail_graph` in `backend/tests/kg/test_retrieval_graph.py`.
  2. Run the specific test:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py::test_vector_search_failure_does_not_fail_graph -v
  ```
- **Expected Result**: Test passes. The test asserts `result["context"] is not None` and `result.get("error") is not None`. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: `build_retrieval_graph` returns a compiled graph with `.ainvoke`
- **Description**: `build_retrieval_graph(driver)` must return a compiled LangGraph object that exposes a callable `.ainvoke` method — confirming the `StateGraph` compiles without error.
- **Components**: `backend/app/kg/retrieval_graph.py` — `build_retrieval_graph`, `StateGraph`, `RetrievalState`
- **Steps**:
  1. Run the specific test:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py::test_build_retrieval_graph_returns_compiled_graph -v
  ```
- **Expected Result**: Test passes. The compiled graph has `.ainvoke` as a callable attribute. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: `KNOWLEDGE_GRAPH` intent in `Intent` enum — hub routing is wired
- **Description**: `Intent.KNOWLEDGE_GRAPH` must exist with value `"KNOWLEDGE_GRAPH"` in `backend/app/agents/state.py`, and `Intent.KNOWLEDGE_GRAPH` must map to the `"knowledge_graph"` node in `_route_selector` in `hub.py`.
- **Components**: `backend/app/agents/state.py` (`Intent` enum), `backend/app/agents/hub.py` (`_route_selector`, `build_hub_graph`)
- **Flow**:
  1. Enum contains `KNOWLEDGE_GRAPH = "KNOWLEDGE_GRAPH"` (no other values changed)
  2. `_route_selector` maps `Intent.KNOWLEDGE_GRAPH` → `"knowledge_graph"`
  3. `build_hub_graph` registers `knowledge_graph` node and adds `knowledge_graph → END` edge
- **Steps**:
  1. Run the enum test:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py::test_knowledge_graph_intent_in_route_intent_enum -v
  ```
  2. Run the hub import check:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -c "from app.agents.hub import hub; print('hub import OK')"
  ```
- **Expected Result**: Pytest test passes. Hub import prints `hub import OK` with no errors. Exit code 0 for both.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: Full happy-path — retrieval graph assembles a `ContextSlice`
- **Description**: When all dependencies (member profile lookup, traversal, vector search, context assembler) return valid data, `graph.ainvoke({"member_id": "m1", "query": "leg workout"})` must return a state dict containing `context` with a non-`None` `ContextSlice` whose `member_profile["id"]` equals the input `member_id`.
- **Components**: `build_retrieval_graph`, `_make_nodes`, `assemble_context`, all traversal functions
- **Flow**:
  1. `lookup_member` → returns `member_profile`
  2. `run_injury_traversal` → returns `contraindicated_ids` + `safe_exercises`
  3. `run_preference_traversal` → returns `preferred_exercises` + `performed_exercises`
  4. `run_vector_search` → returns `vector_docs`
  5. `assemble` → calls `assemble_context(member_id, query, driver)` → returns `ContextSlice`
- **Steps**:
  1. Run the specific test:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && set -a && source ../.env && set +a && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_invokes_assemble_context -v
  ```
- **Expected Result**: Test passes. `result["context"]` is not `None`; `result["context"]["member_profile"]["id"]` equals `"m1"`. Exit code 0.
- [x] Pass <!-- 2026-06-06 -->
