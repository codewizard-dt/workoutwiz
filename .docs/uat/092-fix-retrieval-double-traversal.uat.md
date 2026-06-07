# UAT: Eliminate Double-Traversal in retrieval_graph.assemble

> **Source task**: [`.docs/tasks/092-fix-retrieval-double-traversal.md`](../tasks/092-fix-retrieval-double-traversal.md)
> **Generated**: 2026-06-07

---

## Prerequisites

- [ ] `backend/.venv` exists (`make install` has been run at least once)
- [ ] Working directory is the repository root

---

## Test Suite Tests

This task is a pure backend refactor — there are no API endpoint changes and no UI
changes. The observable surface is entirely the pytest test suite. All tests below
run against the two affected test files: `backend/tests/kg/test_retrieval_graph.py`
and `backend/tests/kg/test_context_assembler.py`.

---

### UAT-SUITE-001: Core kg test files pass (17/17)

- **Description**: Verify that the two directly-affected test files pass cleanly, confirming the new `assemble_context_from_parts` helper and the refactored `assemble` node both work correctly.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py backend/tests/kg/test_context_assembler.py -v
  ```
- **Expected Result**: All tests pass (`17 passed`); zero failures, zero errors. Exit code 0.
- [ ] Pass

---

### UAT-SUITE-002: Full kg test suite passes (73/75)

- **Description**: Verify that the full `tests/kg/` suite reaches the required pass rate. The 2 pre-existing failures are in `test_tools.py` and are unrelated to this task — they are a patch-target mismatch that existed before this work.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/ -v
  ```
- **Expected Result**: At least 73 tests pass; exactly 2 failures allowed, both must be located in `test_tools.py`. Exit code 1 (due to known pre-existing failures) is acceptable provided the failure count and file location match.
- [ ] Pass

---

### UAT-SUITE-003: No redundant traversal calls — `test_assemble_node_does_not_re_run_traversals` passes

- **Description**: Regression gate: the `assemble` node must read from `RetrievalState` and never re-invoke any traversal function. Each of `get_member_profile`, `get_safe_exercises`, `get_preferred_exercises`, `get_performed_exercises`, `get_avoided_exercises` must be called exactly once per graph invocation.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py::test_assemble_node_does_not_re_run_traversals -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass

---

### UAT-SUITE-004: SNOMED provenance stitching — `test_assemble_node_output_equivalence_and_provenance_stitch` passes

- **Description**: Verify that the `assemble` node stitches `contraindicated_provenance` from `state["contraindicated_provenance"]` onto the returned `ContextSlice`, and that the assembled `ContextSlice` fields (member_profile, safe_exercises, token_counts) match the fixture values.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py::test_assemble_node_output_equivalence_and_provenance_stitch -v
  ```
- **Expected Result**: `1 passed`. Exit code 0. The test asserts `context["contraindicated_provenance"] == [{"snomed_code": "123", "exercise_id": "ex-1"}]`.
- [ ] Pass

---

### UAT-SUITE-005: `assemble_context_from_parts` never touches the driver — `test_assemble_context_from_parts_does_not_touch_driver` passes

- **Description**: Verify that `assemble_context_from_parts` is a pure helper that does not call `get_member_profile`, `get_safe_exercises`, `_safe_call`, or `_safe_vector_search` — i.e., it performs no Neo4j or vector-store I/O.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_context_assembler.py::test_assemble_context_from_parts_does_not_touch_driver -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass

---

### UAT-SUITE-006: `assemble_context()` backward-compatible vector-only fallback — `test_assemble_context_returns_vector_only_when_member_not_found` passes

- **Description**: Verify that the public `assemble_context()` wrapper still returns a vector-only `ContextSlice` (not a `ValueError`) when the member is not found in Neo4j. This corrects a pre-existing wrong assertion and must pass after the task.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_context_assembler.py::test_assemble_context_returns_vector_only_when_member_not_found -v
  ```
- **Expected Result**: `1 passed`. Exit code 0. The test asserts `result["member_profile"] == {}`, `result["preferred_exercises"] == []`, `result["token_counts"]["member_profile"] == 0`, `result["token_counts"]["preferred_exercises"] == 0`.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: `assemble_context_from_parts` deduplication — preferred exercises excluded from vector hits

- **Description**: Verify that exercises appearing in `preferred_exercises` are not duplicated in `vector_hits` — the dedup logic must filter vector hits against `seen_preferred`.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_context_assembler.py::test_deduplication_removes_preferred_from_vector_hits -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass

---

### UAT-EDGE-002: `assemble_context_from_parts` deduplication — unsafe exercises excluded from preferred list

- **Description**: Verify that exercises not in `safe_exercises` are filtered out of `preferred_exercises` even if they arrive in the `preferred_exercises` input list.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_context_assembler.py::test_deduplication_filters_unsafe_exercises_from_preferred -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass

---

## Integration Tests

### UAT-INT-001: Full graph invocation returns ContextSlice via state threading

- **Description**: Verify the happy-path end-to-end flow: `build_retrieval_graph` → `ainvoke` → each node populates `RetrievalState` → `assemble` reads from state → `context` is returned. Confirms the graph compiles, nodes are wired correctly, and `assemble_context_from_parts` is invoked (not the old `assemble_context`).
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py::test_retrieval_graph_invokes_assemble_context -v
  ```
- **Expected Result**: `1 passed`. Exit code 0. The test asserts `result["context"]["member_profile"]["id"] == "m1"`.
- [ ] Pass

---

### UAT-INT-002: Graph returns vector-only context when member not found

- **Description**: Verify that when `lookup_member` finds no profile, the full graph still completes and returns a vector-only `ContextSlice` (empty member_profile, empty preferred_exercises) rather than raising.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py::test_retrieval_graph_returns_vector_only_when_member_not_found -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass

---

### UAT-INT-003: Audit log contains all 5 entries after full graph invocation

- **Description**: Verify that after a full graph invocation, `state["audit_log"]` contains exactly 5 entries — one per node: `retrieval_lookup_member`, `retrieval_injury_traversal`, `retrieval_preference_traversal`, `retrieval_vector_search`, `retrieval_assemble`. Confirms no node was skipped or doubled.
- **Steps**:
  1. Run the command below as-is from the repository root
- **Command**:
  ```bash
  backend/.venv/bin/pytest backend/tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v
  ```
- **Expected Result**: `1 passed`. Exit code 0.
- [ ] Pass
