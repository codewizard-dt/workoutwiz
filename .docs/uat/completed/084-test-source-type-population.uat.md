# UAT: Test source_type/source_id Population

> **Source task**: [`.docs/tasks/084-test-source-type-population.md`](../tasks/084-test-source-type-population.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend running with pytest configured
- [ ] Python 3.12+ with pytest installed in virtual environment
- [ ] `backend/tests/kg/test_generation_graph.py` contains all 6 source type tests
- [ ] Database seeded with exercise data from `exercises.json`

---

## Unit Tests: Source Type Population

### UAT-TEST-001: Verify all 6 source type test functions exist
- **Test Target**: `backend/tests/kg/test_generation_graph.py`
- **Description**: Verify that all required test functions for source type population exist and are discoverable
- **Steps**:
  1. Run the test discovery command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py --collect-only -q | grep -E "(test_enrich_recommendation_with_safe_set_source|test_enrich_recommendation_with_preferred_source|test_enrich_recommendation_with_vector_search_source|test_enrich_recommendation_with_mixed_sources|test_fallback_node_populates_source_fields|test_all_exercises_have_source_fields)"
  ```
- **Expected Result**: All 6 test functions are listed in the output
- [ ] Pass

### UAT-TEST-002: SAFE_SET source type test passes
- **Test Target**: `test_enrich_recommendation_with_safe_set_source()`
- **Description**: Verify exercises from safe_exercises context get source_type=SAFE_SET and source_id starts with "safe_"
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_safe_set_source -v
  ```
- **Expected Result**: Test passes; output shows `PASSED`
- [ ] Pass

### UAT-TEST-003: PREFERRED source type test passes
- **Test Target**: `test_enrich_recommendation_with_preferred_source()`
- **Description**: Verify exercises from preferred_exercises context get source_type=PREFERRED and source_id starts with "preferred_"
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_preferred_source -v
  ```
- **Expected Result**: Test passes; output shows `PASSED`
- [ ] Pass

### UAT-TEST-004: VECTOR_SEARCH source type test passes
- **Test Target**: `test_enrich_recommendation_with_vector_search_source()`
- **Description**: Verify exercises from vector_hits context get source_type=VECTOR_SEARCH and source_id starts with "vector_"
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_vector_search_source -v
  ```
- **Expected Result**: Test passes; output shows `PASSED`
- [ ] Pass

### UAT-TEST-005: Mixed sources test passes
- **Test Target**: `test_enrich_recommendation_with_mixed_sources()`
- **Description**: Verify a single recommendation can have exercises from multiple sources (SAFE_SET, PREFERRED, VECTOR_SEARCH) and each gets correct source_type and source_id
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_mixed_sources -v
  ```
- **Expected Result**: Test passes; output shows `PASSED` and validates all 3 exercise sources
- [ ] Pass

### UAT-TEST-006: FALLBACK source type test passes
- **Test Target**: `test_fallback_node_populates_source_fields()`
- **Description**: Verify exercises from fallback handler get source_type=FALLBACK and source_id starts with "fallback_"
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_fallback_node_populates_source_fields -v
  ```
- **Expected Result**: Test passes; output shows `PASSED` and validates all fallback exercises have valid source fields
- [ ] Pass

### UAT-TEST-007: All exercises have source fields regression test passes
- **Test Target**: `test_all_exercises_have_source_fields()`
- **Description**: Verify that after enrichment, all exercises in a recommendation must have source_type set to one of the 4 valid enum values (SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK)
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_all_exercises_have_source_fields -v
  ```
- **Expected Result**: Test passes; output shows `PASSED` and validates all exercises have source_type in {SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK}
- [ ] Pass

---

## Integration Tests: Source Type Coverage

### UAT-INT-001: All 24 generation_graph tests pass
- **Test Target**: Full `tests/kg/test_generation_graph.py` suite
- **Description**: Verify all 24 tests in the generation graph test suite pass, including the 6 source type tests and 18 other tests covering generation, safety gates, fallback, and audit logging
- **Steps**:
  1. Run the command below to execute the full test suite
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py -v
  ```
- **Expected Result**: All 24 tests pass; output shows `24 passed in X.XXs`
- [ ] Pass

### UAT-INT-002: Source type tests cover all 4 enum values
- **Test Target**: All 6 source type tests combined
- **Description**: Verify that together, the 6 source type tests exercise all 4 valid enum values
  - SAFE_SET: covered by `test_enrich_recommendation_with_safe_set_source()` and `test_enrich_recommendation_with_mixed_sources()`
  - PREFERRED: covered by `test_enrich_recommendation_with_preferred_source()` and `test_enrich_recommendation_with_mixed_sources()`
  - VECTOR_SEARCH: covered by `test_enrich_recommendation_with_vector_search_source()` and `test_enrich_recommendation_with_mixed_sources()`
  - FALLBACK: covered by `test_fallback_node_populates_source_fields()`
- **Steps**:
  1. Run all source type tests together
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py -k "source" -v
  ```
- **Expected Result**: All 6 tests pass and collectively cover all 4 source_type enum values
- [ ] Pass

### UAT-INT-003: Source type tests validate source_id population
- **Test Target**: All 6 source type tests with source_id assertions
- **Description**: Verify that source_id fields are populated correctly and match expected prefixes per source type:
  - SAFE_SET: source_id starts with "safe_"
  - PREFERRED: source_id starts with "preferred_"
  - VECTOR_SEARCH: source_id starts with "vector_"
  - FALLBACK: source_id starts with "fallback_"
- **Steps**:
  1. Examine test assertions in source type tests
  2. Run tests to verify assertions pass
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py -k "source" -v 2>&1 | grep -E "(PASSED|FAILED)"
  ```
- **Expected Result**: All 6 tests pass, indicating source_id assertions were satisfied
- [ ] Pass

---

## Validation: Enum Coverage

### UAT-VAL-001: Verify 4 valid source_type enum values are documented in code
- **Test Target**: `RecommendedExercise` model in `backend/app/kg/generation_graph.py`
- **Description**: Verify that the RecommendedExercise model defines or documents the 4 valid source_type enum values
- **Steps**:
  1. Check that RecommendedExercise has source_type field
  2. Verify enum values are: SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK
- **Command**:
  ```bash
  grep -A 5 "source_type" /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/app/kg/generation_graph.py | head -20
  ```
- **Expected Result**: Output shows source_type field definition with 4 enum values: SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK
- [ ] Pass

### UAT-VAL-002: No exercises missing source_type in response
- **Test Target**: `test_all_exercises_have_source_fields()` regression test
- **Description**: Verify the regression test ensures no exercises slip through without source_type assignment
- **Steps**:
  1. Run the regression test
  2. Verify it passes without assertion errors
- **Command**:
  ```bash
  cd backend && python -m pytest tests/kg/test_generation_graph.py::test_all_exercises_have_source_fields -v
  ```
- **Expected Result**: Test passes; confirms all exercises have source_type in {SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK}
- [ ] Pass

---

## Summary

This UAT verifies that task 084 acceptance criteria are fully satisfied:

1. **All 6 source type test functions exist** — verified by test discovery
2. **All 24 generation_graph tests pass** — full integration test run
3. **Source types cover all 4 enum values** — SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK
4. **source_id population is validated** — all 6 tests assert on source_id prefixes
5. **No regressions** — all 24 tests pass, including 18 existing tests

Each of the 6 source type tests validates:
- source_type is set to the correct enum value
- source_id is populated with correct prefix format
- Exercise provenance is traceable through source_id

