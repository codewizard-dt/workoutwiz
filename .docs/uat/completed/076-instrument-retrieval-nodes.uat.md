# UAT: Instrument Retrieval Sub-Graph Nodes

> **Source task**: [`.docs/tasks/076-instrument-retrieval-nodes.md`](../tasks/076-instrument-retrieval-nodes.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] `backend/` Python environment installed (`pip install -e ".[dev]"` from `backend/`)
- [ ] Working directory for test commands is `backend/`
- [ ] No live Neo4j or OpenAI connection required — all external calls are mocked

---

## Unit Tests (pytest)

This task instruments internal LangGraph graph nodes — there is no standalone HTTP endpoint for
the retrieval graph. All tests run the compiled graph with mocked dependencies and assert on the
`audit_log` that each node appends to state.

### UAT-UNIT-001: All 5 retrieval audit entries are present after graph invocation

- **Test**: `tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries`
- **Description**: Invoke `build_retrieval_graph` with all dependencies mocked. Verify that `audit_log` in the final state contains exactly 5 entries — one for each node — with the required event names.
- **Steps**:
  1. Run the command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v
  ```
- **Expected Result**: Test passes (`PASSED`). The `audit_log` in the result contains exactly 5 entries with events: `retrieval_lookup_member`, `retrieval_injury_traversal`, `retrieval_preference_traversal`, `retrieval_vector_search`, `retrieval_assemble`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: All retrieval audit entries have non-negative latency_ms

- **Test**: `tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries`
- **Description**: Same invocation as UAT-UNIT-001. Verify every entry in `audit_log` has `latency_ms >= 0`.
- **Steps**:
  1. Run the command below — the existing test asserts `latency_ms >= 0` for all 5 entries
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v -s
  ```
- **Expected Result**: Test passes. Assertion `all(e["latency_ms"] >= 0 for e in retrieval_entries)` holds.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: All retrieval audit entries carry user_id

- **Test**: `tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries`
- **Description**: Verify that every audit entry contains a `user_id` field (propagated from the initial state `user_id`).
- **Steps**:
  1. Covered by the same test run as UAT-UNIT-001 — assertion `all("user_id" in e for e in retrieval_entries)` is included
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v
  ```
- **Expected Result**: Test passes. Each of the 5 entries has `user_id` set to `"user-42"` (the value passed in initial state).
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: result_count present on all nodes that produce it

- **Test**: `tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries`
- **Description**: Verify that `result_count` is present on the 4 nodes that produce it: `retrieval_lookup_member`, `retrieval_injury_traversal`, `retrieval_preference_traversal`, `retrieval_vector_search`. The `retrieval_assemble` node uses `input_count`/`output_count` instead.
- **Steps**:
  1. Covered by the same test as UAT-UNIT-001
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v
  ```
- **Expected Result**: Test passes. Each of the 4 listed nodes has `"result_count"` in its audit entry.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-005: Full retrieval test suite passes without regression

- **Test file**: `tests/kg/test_retrieval_graph.py`
- **Description**: Run the entire retrieval graph test file to confirm no existing tests regressed after instrumentation was added.
- **Steps**:
  1. Run the command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py -v
  ```
- **Expected Result**: All tests in the file pass (`PASSED`). No failures or errors.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Vector search failure still produces audit entry with error field

- **Description**: When `get_exercise_vector_store()` raises an exception, `run_vector_search` must catch it and still append an audit entry with `event="retrieval_vector_search"`, `result_count=0`, and an `error` field — the graph must not raise.
- **Steps**:
  1. This is verified by the existing `test_vector_search_failure_does_not_fail_graph` test combined with the audit assertions
  2. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_vector_search_failure_does_not_fail_graph -v
  ```
- **Expected Result**: Test passes. Graph completes without raising. Audit log still accumulates entries from all nodes that ran.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: audit_log accumulates across all 5 nodes (no overwrite)

- **Description**: Each node does `state.get("audit_log", []) + [new_entry]` to append rather than replace. Verify that running the full graph via `UAT-UNIT-001` yields exactly 5 entries (not 1, meaning no node overwrites the list).
- **Steps**:
  1. Covered by `len(retrieval_events) == 5` assertion in UAT-UNIT-001 — if any node overwrote the list, count would be < 5
  2. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_retrieval_graph.py::test_retrieval_graph_audit_log_contains_all_5_entries -v -s 2>&1 | grep -E "PASSED|FAILED|ERROR|audit"
  ```
- **Expected Result**: Output contains `PASSED`. No `FAILED` or `ERROR` lines.
- [x] Pass <!-- 2026-06-06 -->
