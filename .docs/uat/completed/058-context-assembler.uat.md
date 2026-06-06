# UAT: Context Assembler — Merge Traversal Results and Vector Hits into Token-Budget Context

> **Source task**: [`.docs/tasks/completed/058-context-assembler.md`](../tasks/completed/058-context-assembler.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Python environment available (`pyenv` or virtualenv with project deps installed)
- [ ] `backend/app/kg/context_assembler.py` exists with all required symbols
- [ ] `backend/tests/kg/test_context_assembler.py` exists with ≥7 test functions
- [ ] No live Neo4j or embedding model required — all tests use mocks
- [ ] Run from the `backend/` directory (or with `set -a && source .env && set +a` for env vars)

---

## Edge Case Tests

### UAT-EDGE-001: Full pytest suite passes with zero failures

- **Scenario**: All 8 unit tests in `test_context_assembler.py` pass against the implemented module
- **Steps**:
  1. Run the command below from the repo root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py -v
  ```
- **Expected Result**: `8 passed` with exit code 0; output shows all test names with `PASSED` status; no `FAILED`, `ERROR`, or `SKIPPED` lines
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: `assemble_context()` returns a valid `ContextSlice` dict with all required keys

- **Scenario**: With mocked traversal and vector search returning fixture data, `assemble_context()` returns a properly structured dict
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_assemble_context_returns_context_slice -v
  ```
- **Expected Result**: `PASSED` — result dict contains keys `member_profile`, `safe_exercises`, `preferred_exercises`, `vector_hits`, `token_counts`; `token_counts["total"]` is greater than 0
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: `assemble_context()` raises `ValueError` when member is not found

- **Scenario**: When `get_member_profile` returns `None`, the function must raise rather than silently return an empty context
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_assemble_context_raises_when_member_not_found -v
  ```
- **Expected Result**: `PASSED` — `ValueError` is raised with message matching `"not found in Neo4j"`; no return value is produced
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-004: Deduplication removes preferred exercises from vector_hits

- **Scenario**: An exercise that appears in `preferred_exercises` must NOT also appear in `vector_hits`, even if the vector store returns it
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_deduplication_removes_preferred_from_vector_hits -v
  ```
- **Expected Result**: `PASSED` — `"ex-1"` (present in preferred) absent from `vector_hits`; `"ex-2"` present in `vector_hits`
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-005: Deduplication filters unsafe exercises out of preferred_exercises

- **Scenario**: Any exercise not present in the safe set must be excluded from `preferred_exercises`, regardless of how it was returned by the traversal
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_deduplication_filters_unsafe_exercises_from_preferred -v
  ```
- **Expected Result**: `PASSED` — `result["preferred_exercises"]` is an empty list when preferred contains only an exercise not present in `safe_exercises`
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-006: Token budget truncates `safe_exercises` to within the 600-token budget

- **Scenario**: When the safe exercise list is large (100 items with padded data), the returned list is shorter than 100 and token count stays within `SAFE_EXERCISES_BUDGET` (600)
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_token_budget_truncates_safe_exercises -v
  ```
- **Expected Result**: `PASSED` — `len(result["safe_exercises"]) < 100` and `result["token_counts"]["safe_exercises"] <= 600`
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-007: `_safe_call()` returns an empty list when the wrapped function raises

- **Scenario**: If any traversal function raises an exception, `_safe_call` absorbs it and returns `[]` instead of propagating
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_safe_call_returns_empty_list_on_exception -v
  ```
- **Expected Result**: `PASSED` — `await _safe_call(raising_fn)` returns `[]`; no exception propagated
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-008: `_estimate_tokens()` returns positive int; empty list yields 1

- **Scenario**: Token estimation uses char approximation: `max(1, len(json.dumps(obj)) // 4)`. An empty list `[]` is 2 chars → `max(1, 0) = 1`.
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_estimate_tokens_approximation -v
  ```
- **Expected Result**: `PASSED` — `_estimate_tokens({"name": "Squat"})` is greater than 0; `_estimate_tokens([])` equals 1
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-009: `_truncate_to_budget()` never exceeds the specified budget

- **Scenario**: Greedy prefix selection stops before exceeding the budget; returned `used` token count is always ≤ budget
- **Steps**:
  1. Run the targeted test:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -m pytest tests/kg/test_context_assembler.py::test_truncate_to_budget_respects_budget -v
  ```
- **Expected Result**: `PASSED` — with 50 items and budget of 100 tokens, `used <= 100`, `len(selected) <= 50`, and every selected item has a positive token estimate
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Module exports all required symbols

- **Scenario**: The module must export all symbols specified in the acceptance criteria: `ContextSlice`, `SectionTokenCounts`, `assemble_context`, `_safe_call`, `_safe_vector_search`, `_estimate_tokens`, `_truncate_to_budget`, plus constants `TOTAL_TOKEN_BUDGET`, `CHARS_PER_TOKEN`, all budget constants
- **Steps**:
  1. Run the command below to import and verify all required symbols exist:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.context_assembler import ContextSlice, SectionTokenCounts, assemble_context, _safe_call, _safe_vector_search, _estimate_tokens, _truncate_to_budget, TOTAL_TOKEN_BUDGET, MEMBER_PROFILE_BUDGET, SAFE_EXERCISES_BUDGET, PREFERRED_EXERCISES_BUDGET, VECTOR_HITS_BUDGET, CHARS_PER_TOKEN; print('All symbols OK')"
  ```
- **Expected Result**: Prints `All symbols OK` with exit code 0; no `ImportError` or `AttributeError`
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: Budget constants match ADR-001 D3 specification

- **Scenario**: The token budget constants must match the values specified in ADR-001 D3: `TOTAL_TOKEN_BUDGET=2048`, `MEMBER_PROFILE_BUDGET=200`, `SAFE_EXERCISES_BUDGET=600`, `PREFERRED_EXERCISES_BUDGET=400`, `VECTOR_HITS_BUDGET=400`, `CHARS_PER_TOKEN=4`
- **Steps**:
  1. Run the command below:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.context_assembler import TOTAL_TOKEN_BUDGET, MEMBER_PROFILE_BUDGET, SAFE_EXERCISES_BUDGET, PREFERRED_EXERCISES_BUDGET, VECTOR_HITS_BUDGET, CHARS_PER_TOKEN; assert TOTAL_TOKEN_BUDGET == 2048; assert MEMBER_PROFILE_BUDGET == 200; assert SAFE_EXERCISES_BUDGET == 600; assert PREFERRED_EXERCISES_BUDGET == 400; assert VECTOR_HITS_BUDGET == 400; assert CHARS_PER_TOKEN == 4; print('Budget constants OK')"
  ```
- **Expected Result**: Prints `Budget constants OK` with exit code 0; `AssertionError` would indicate a mismatch with the ADR specification
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: `ContextSlice` TypedDict has correct key structure

- **Scenario**: `ContextSlice` must have keys `member_profile`, `safe_exercises`, `preferred_exercises`, `vector_hits`, `token_counts`; `SectionTokenCounts` must have keys `member_profile`, `safe_exercises`, `preferred_exercises`, `vector_hits`, `total`
- **Steps**:
  1. Run the command below:
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && python -c "from app.kg.context_assembler import ContextSlice, SectionTokenCounts; cs_keys = set(ContextSlice.__annotations__); stc_keys = set(SectionTokenCounts.__annotations__); assert cs_keys == {'member_profile','safe_exercises','preferred_exercises','vector_hits','token_counts'}, cs_keys; assert stc_keys == {'member_profile','safe_exercises','preferred_exercises','vector_hits','total'}, stc_keys; print('TypedDict structure OK')"
  ```
- **Expected Result**: Prints `TypedDict structure OK` with exit code 0; any missing or extra key causes an `AssertionError`
- [x] Pass <!-- 2026-06-06 -->
