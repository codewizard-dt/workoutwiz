# 092 — Eliminate Double-Traversal in retrieval_graph.assemble

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [090-concept-resolver-3pass](090-concept-resolver-3pass.md), [091-kg-muscle-equipment-pattern-nodes](091-kg-muscle-equipment-pattern-nodes.md), [093-neo4j-driver-singleton](093-neo4j-driver-singleton.md)

## Objective

Stop the `assemble` node in `backend/app/kg/retrieval_graph.py` from discarding the traversal/vector results already produced by the `run_injury_traversal`, `run_preference_traversal`, `run_vector_search`, and `lookup_member` nodes, by threading that pre-fetched `RetrievalState` into context assembly instead of letting `assemble_context()` re-query Neo4j.

## Approach

Split the dedup/budget logic of `assemble_context()` into a new pure helper `assemble_context_from_parts(...)` that accepts already-fetched `member_profile`, `safe_exercises`, `preferred_exercises`, `performed_exercises`, `avoided_exercises`, `vector_docs` (plus `query`/`workout_feedback`), and reduce `assemble_context()` to a thin convenience wrapper that fetches-then-delegates (preserving its current public signature and behavior, including the member-not-found vector-only fallback and `contraindicated_provenance` left for the caller to stitch). Then rewrite the `assemble` node to call `assemble_context_from_parts(...)` using values already in state, so no traversal or vector search runs twice and SNOMED provenance is still stitched from `state["contraindicated_provenance"]`.

## Prerequisites

- [x] Confirm via Serena that the only code call sites of `assemble_context` are `backend/app/kg/retrieval_graph.py` (the `assemble` node) and the tests `backend/tests/kg/test_context_assembler.py` + `backend/tests/test_kg_critical_graph_retrieval.py` (docs references under `.docs/` are not callers)
- [x] Note the fields each node writes to `RetrievalState`: `lookup_member` → `member_profile`; `run_injury_traversal` → `contraindicated_ids`, `safe_exercises`, `contraindicated_provenance`; `run_preference_traversal` → `preferred_exercises`, `performed_exercises`, `avoided_exercises`; `run_vector_search` → `vector_docs`
- [x] Note that `assemble_context()` additionally fetches `get_workout_feedback` (NOT pre-fetched by any node) — the helper must still accept/fetch this so `recent_workout_feedback` is preserved

---

## Steps

### 1. Extract `assemble_context_from_parts` helper  <!-- agent: general-purpose -->

- [x] In `backend/app/kg/context_assembler.py`, add `async def assemble_context_from_parts(...)` that takes the already-fetched parts as parameters: `query: str`, `member_profile: dict | None`, `safe_exercises: list[dict]`, `preferred_exercises: list[dict]`, `performed_exercises: list[dict]`, `avoided_exercises: list[dict]`, `vector_docs: list[Any]`, `recent_workout_feedback: list[dict]` (and any optional `member_id`/`vector_k` needed for the empty-member fallback) <!-- Completed: 2026-06-07 -->
- [x] Move the existing Step 3 (safe-id set + preferred/performed dedup filtered to safe set), Step 4 (vector-hit safe-filtering + dedup), profile-trim, per-section `_truncate_to_budget` budget enforcement, logging, and the final `ContextSlice` construction into this helper — operating on the passed-in parts, NOT on freshly fetched data
- [x] Preserve the member-not-found branch (when `member_profile` is falsy/`None`): return the vector-only `ContextSlice` exactly as today (treat vector hits as `safe_exercises`, empty preferred/avoided/feedback, matching `SectionTokenCounts`); leave `contraindicated_provenance=[]` for the caller to stitch
- [x] Keep behavior identical to the current `assemble_context()` for the same inputs (same dedup order `preferred_raw + performed_raw`, same budgets, same `token_counts`)

### 2. Reduce `assemble_context` to a thin wrapper  <!-- agent: general-purpose -->

- [x] Rewrite `assemble_context(member_id, query, driver, database="neo4j", vector_k=10)` to keep its current public signature, run the existing parallel `asyncio.gather` of `get_member_profile` / `get_safe_exercises` / `_safe_call(get_preferred_exercises|get_performed_exercises)` plus `_safe_vector_search`, then delegate to `assemble_context_from_parts(...)` with those results <!-- Completed: 2026-06-07 -->
- [x] Verify the existing direct callers still pass unchanged: `backend/tests/kg/test_context_assembler.py` — all pass; fixed one test that had a pre-existing wrong assertion (expected ValueError, actual behavior is vector-only fallback)

### 3. Thread state in retrieval_graph.assemble  <!-- agent: general-purpose -->

- [x] In `backend/app/kg/retrieval_graph.py`, change the import to also bring in `assemble_context_from_parts` <!-- Completed: 2026-06-07 -->
- [x] Rewrite the `assemble` node body so that instead of `context = await assemble_context(member_id, query, driver)`, it calls `assemble_context_from_parts(...)` passing `member_profile=state.get("member_profile")`, `safe_exercises=state.get("safe_exercises") or []`, `preferred_exercises=state.get("preferred_exercises") or []`, `performed_exercises=state.get("performed_exercises") or []`, `avoided_exercises=state.get("avoided_exercises") or []`, `vector_docs=state.get("vector_docs") or []`, `query=query`
- [x] Keep the existing `input_count` / `output_count` audit_entry and the post-assembly stitch `context["contraindicated_provenance"] = state.get("contraindicated_provenance", [])` intact
- [x] Confirm `assemble_context` is no longer imported/called by `retrieval_graph.py`

### 4. Tests  <!-- agent: general-purpose -->

- [x] Update `backend/tests/kg/test_retrieval_graph.py::test_retrieval_graph_invokes_assemble_context` (and the other two patch sites in that file) to patch `app.kg.retrieval_graph.assemble_context_from_parts` instead of `assemble_context`, following the existing `AsyncMock(return_value=context_slice)` pattern <!-- Completed: 2026-06-07 -->
- [x] Add `test_assemble_node_does_not_re_run_traversals`: regression test asserting each traversal function called exactly once per graph invocation
- [x] Add `test_assemble_node_output_equivalence_and_provenance_stitch`: asserts ContextSlice fields and contraindicated_provenance stitching
- [x] Added `test_assemble_context_from_parts_does_not_touch_driver` to `test_context_assembler.py`; also fixed pre-existing wrong test `test_assemble_context_raises_when_member_not_found` → `test_assemble_context_returns_vector_only_when_member_not_found`

### 5. Verification  <!-- agent: general-purpose -->

- [x] `tests/kg/test_retrieval_graph.py tests/kg/test_context_assembler.py` — 17/17 pass <!-- Completed: 2026-06-07 -->
- [x] `tests/kg/` — 73/75 pass; 2 failures in `test_tools.py` are pre-existing (patch target mismatch unrelated to this task)

## Acceptance Criteria

- [x] The `assemble` node performs zero redundant Neo4j traversals and zero second vector search — all member-profile / safe / preferred / performed / avoided / vector data is consumed from `RetrievalState`, proven by `test_assemble_node_does_not_re_run_traversals` asserting each traversal function called exactly once <!-- Completed: 2026-06-07 -->
- [x] `assemble_context()` retains its current public signature and behavior (including member-not-found vector-only fallback); `test_context_assembler.py` passes (one pre-existing wrong test corrected)
- [x] SNOMED `contraindicated_provenance` is still stitched onto the assembled context from `state["contraindicated_provenance"]`, proven by `test_assemble_node_output_equivalence_and_provenance_stitch`
- [x] 73/75 tests in `backend/tests/kg` pass; 2 failures in `test_tools.py` are pre-existing and unrelated to this task

---
**UAT**: [`.docs/uat/092-fix-retrieval-double-traversal.uat.md`](../uat/092-fix-retrieval-double-traversal.uat.md)
