# UAT: Critical-Path Test 2 — Graph Retrieval Returns Member-Relevant Context

> **Source task**: [`.docs/tasks/completed/069-critical-path-test-graph-retrieval.md`](../tasks/completed/069-critical-path-test-graph-retrieval.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend Python environment is active (virtualenv / Poetry shell in `backend/`)
- [ ] `pytest` and `pytest-asyncio` are installed (`pip install pytest pytest-asyncio`)
- [ ] `backend/tests/test_kg_critical_graph_retrieval.py` exists with 5 test functions
- [ ] Environment variables loaded: `set -a && source .env && set +a`

---

## Integration Tests

### UAT-INT-001: All 5 Critical-Path Tests Pass

- **Components**: `backend/tests/test_kg_critical_graph_retrieval.py`, `app.kg.context_assembler.assemble_context`
- **Flow**: Run the full test module and verify all 5 assertions hold — feedback-rated preferred exercises surfaced, history-performed exercises surfaced, contraindicated exercises excluded, vector hits filtered to safe set, and token count is positive.
- **Steps**:
  1. From the repo root, run the command below as-is
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/test_kg_critical_graph_retrieval.py -v
  ```
- **Expected Result**: `5 passed` with exit code 0. All 5 test names printed with `PASSED`:
  - `test_preferred_exercises_surfaced_from_feedback`
  - `test_performed_exercises_surfaced_from_history`
  - `test_contraindicated_exercise_not_in_safe_exercises`
  - `test_vector_hits_filtered_to_safe_set`
  - `test_context_slice_has_positive_token_count`
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Preferred Exercise Filtered When Not in Safe Set

- **Scenario**: `get_preferred_exercises` returns an exercise whose ID is absent from `get_safe_exercises` — the assembler must exclude it from `preferred_exercises`.
- **Steps**:
  1. This is covered by `test_contraindicated_exercise_not_in_safe_exercises` in the module. Confirm the test name appears as `PASSED` in the output from UAT-INT-001.
- **Expected Result**: `test_contraindicated_exercise_not_in_safe_exercises` is `PASSED`. The assertion `UNSAFE_EX_ID not in safe_ids` and `UNSAFE_EX_ID not in preferred_ids` both hold.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Token Count Is Positive Even With Minimal Profile

- **Scenario**: `assemble_context` is called with a sparse member profile and no exercises in any list — `token_counts.total` must still be > 0 because the member profile itself contributes tokens.
- **Steps**:
  1. Confirm the test name `test_context_slice_has_positive_token_count` appears as `PASSED` in the output from UAT-INT-001.
- **Expected Result**: `test_context_slice_has_positive_token_count` is `PASSED`. The assertion `ctx["token_counts"]["total"] > 0` holds.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Test File Has Exactly 5 Test Functions

- **Scenario**: Acceptance criteria require ≥5 tests. Verify the module contains exactly the required tests (no missing or extra functions that would indicate an incomplete implementation).
- **Steps**:
  1. Run the command below as-is
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_kg_critical_graph_retrieval.py --collect-only -q
  ```
- **Expected Result**: Output lists exactly 5 test items. No collection errors.
- [x] Pass <!-- 2026-06-06 -->
