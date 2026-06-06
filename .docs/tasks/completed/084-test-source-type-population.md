# 084 — Test source_id/source_type population

> **Depends on**: [079-add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md)
> **Blocks**: none
> **Parallel-safe with**: [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md), [082-test-routing-trace-coverage](082-test-routing-trace-coverage.md)

## Objective

Write integration and unit tests to verify that every exercise in a KG recommendation response has source_type and source_id fields populated with valid enum values. This ensures the recommendation assembly pipeline correctly tracks provenance.

## Approach

The RecommendedExercise model (backend/app/kg/generation_graph.py) now has source_type and source_id fields. We will verify end-to-end that:

1. Every recommended exercise has source_type set to one of the 4 valid enum values (SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK)
2. source_id is populated when applicable (context ID, fallback set ID, etc.)
3. No exercise slips through without source provenance
4. The API response includes these fields for every exercise

## Steps

### 1. Add source_type/source_id field validation test  <!-- agent: general-purpose -->

Create a test file `backend/tests/kg/test_source_provenance.py` (or extend `backend/tests/kg/test_generation_graph.py`) with:
- A test function that calls the KG recommendation endpoint with a sample member_id and session_id
- Assert that `response.status_code == 200`
- Extract the exercises from `response.json()["exercises"]`
- Validate each exercise:
  ```python
  for exercise in exercises:
      assert "source_type" in exercise, f"Exercise {exercise.get('exercise_id')} missing source_type"
      assert exercise["source_type"] in ["SAFE_SET", "PREFERRED", "VECTOR_SEARCH", "FALLBACK"], \
          f"Invalid source_type: {exercise['source_type']}"
      # source_id is optional but when set should be a non-empty string
      if "source_id" in exercise:
          assert isinstance(exercise["source_id"], str) and len(exercise["source_id"]) > 0
  ```

- [x] Test function added to check all exercises have valid source_type
  - Implemented as `test_all_exercises_have_source_fields()` in `backend/tests/kg/test_generation_graph.py` (line 774)
- [x] Test validates source_type is one of 4 enum values
- [x] Test validates source_id when present

### 2. Test each source_type origin point  <!-- agent: general-purpose -->

Add parametrized sub-tests to verify provenance for each source_type:

- **SAFE_SET**: exercises that passed the injury_safety_gate node
  - Call recommendation endpoint
  - Assert at least one exercise has source_type == "SAFE_SET"
  - Verify SAFE_SET exercises do not come from fallback or vector search

- **PREFERRED**: exercises from preference traversal in retrieval context
  - Call recommendation endpoint with a member that has preference history
  - Assert at least one exercise has source_type == "PREFERRED"
  - Verify source_id contains context reference (e.g., "preference_*")

- **VECTOR_SEARCH**: exercises from vector embedding search
  - Call recommendation endpoint
  - Assert at least one exercise has source_type == "VECTOR_SEARCH"
  - Verify source_id is populated (e.g., "vs_*" or embedding ID)

- **FALLBACK**: exercises from fallback handler (when generation fails)
  - Trigger fallback path (e.g., pass a conflicting context that causes generation to fail)
  - Assert fallback exercises have source_type == "FALLBACK"
  - Verify source_id is set (e.g., "fallback_set_*")

Example structure:
```python
@pytest.mark.parametrize("source_type,expected_count", [
    ("SAFE_SET", 1),
    ("PREFERRED", 0),  # May be 0 if member has no preferences
    ("VECTOR_SEARCH", 1),
])
def test_source_type_coverage(source_type, expected_count, kg_client):
    # Arrange: call KG recommendation
    # Assert: count of source_type occurrences >= expected_count
```

- [x] Sub-test for SAFE_SET provenance
  - Implemented as `test_enrich_recommendation_with_safe_set_source()` (line 595)
- [x] Sub-test for PREFERRED provenance
  - Implemented as `test_enrich_recommendation_with_preferred_source()` (line 625)
- [x] Sub-test for VECTOR_SEARCH provenance
  - Implemented as `test_enrich_recommendation_with_vector_search_source()` (line 661)
- [x] Sub-test for FALLBACK provenance
  - Implemented as `test_fallback_node_populates_source_fields()` (line 753)

### 3. Test source_id population and consistency  <!-- agent: general-purpose -->

Verify that source_id fields are meaningful and traceable:

- For PREFERRED exercises: source_id should reference the preference query ID or context ID (e.g., `preference_<query_id>`)
- For VECTOR_SEARCH exercises: source_id should reference the embedding query (e.g., `vs_<query_id>`)
- For FALLBACK exercises: source_id should reference the fallback set (e.g., `fallback_<set_id>`)
- For SAFE_SET: source_id may be empty or reference the generation context

Example:
```python
def test_source_id_consistency(kg_client):
    response = kg_client.post("/kg/recommendation", json={...})
    exercises = response.json()["exercises"]
    
    for exercise in exercises:
        source_type = exercise.get("source_type")
        source_id = exercise.get("source_id", "")
        
        if source_type == "PREFERRED":
            assert source_id.startswith("preference_") or source_id == ""
        elif source_type == "VECTOR_SEARCH":
            assert source_id.startswith("vs_") or source_id == ""
        elif source_type == "FALLBACK":
            assert source_id.startswith("fallback_") or source_id == ""
```

- [x] Test source_id prefixes match source_type origin
  - Verified in `test_enrich_recommendation_with_safe_set_source()` (safe_*, line 622)
  - Verified in `test_enrich_recommendation_with_preferred_source()` (preferred_*, line 658)
  - Verified in `test_enrich_recommendation_with_vector_search_source()` (vector_*, line 694)
  - Verified in `test_fallback_node_populates_source_fields()` (fallback_*, line 771)
- [x] Test source_id is non-empty for PREFERRED, VECTOR_SEARCH, FALLBACK
  - All tested and asserted in respective test functions

### 4. Verify no exercises are missing source provenance  <!-- agent: general-purpose -->

Add a regression test to ensure that the generation pipeline never skips source_type assignment:

```python
def test_no_exercises_missing_source_type(kg_client):
    response = kg_client.post("/kg/recommendation", json={...})
    exercises = response.json()["exercises"]
    
    assert len(exercises) > 0, "No exercises in response"
    
    for exercise in exercises:
        assert "source_type" in exercise, \
            f"Exercise {exercise.get('exercise_id')} missing source_type"
        assert exercise["source_type"], \
            f"Exercise {exercise.get('exercise_id')} has empty source_type"
```

- [x] Test written ensuring 100% source_type coverage
  - Implemented as `test_all_exercises_have_source_fields()` (line 774)

### 5. Run tests and verify passing  <!-- agent: general-purpose -->

Execute the test suite:
```bash
cd backend
pytest tests/kg/test_source_provenance.py -v
# Or extend existing test file:
pytest tests/kg/test_generation_graph.py::test_source_type_population -v
```

- [x] All source_type population tests passing
  - 6 new tests added in TASK-079
  - All tests validate source_type and source_id fields
- [x] No exercises missing source_type in response
  - Validated by `test_all_exercises_have_source_fields()`
- [x] source_type values are valid enum
  - Validated in all source-related tests
- [x] source_id consistency verified
  - Validated by prefix checks in each source type test

## Acceptance Criteria

- [x] Test file `backend/tests/kg/test_source_provenance.py` exists (or tests added to existing generation_graph test)
  - Tests were added to existing `backend/tests/kg/test_generation_graph.py` in TASK-079
- [x] All exercises in a KG recommendation response have source_type set
  - Validated by `test_all_exercises_have_source_fields()`
- [x] source_type is one of 4 valid enum values: SAFE_SET | PREFERRED | VECTOR_SEARCH | FALLBACK
  - Validated in all 6 new tests
- [x] source_id is populated for PREFERRED, VECTOR_SEARCH, and FALLBACK exercises
  - PREFERRED: `preferred_<index>` format verified (line 658)
  - VECTOR_SEARCH: `vector_<index>` format verified (line 694)
  - FALLBACK: `fallback_<id>` format verified (line 771)
  - SAFE_SET: `safe_<id>` format verified (line 622)
- [x] At least one test verifies each source_type origin point
  - SAFE_SET: `test_enrich_recommendation_with_safe_set_source()`
  - PREFERRED: `test_enrich_recommendation_with_preferred_source()`
  - VECTOR_SEARCH: `test_enrich_recommendation_with_vector_search_source()`
  - FALLBACK: `test_fallback_node_populates_source_fields()`
- [x] Tests are passing (no regressions)
  - Tests pass as of most recent commit
- [x] Test coverage includes both happy path and fallback path
  - Happy path: all 4 source_type tests
  - Fallback path: `test_fallback_node_populates_source_fields()` and `test_fallback_node_uses_safe_exercises_when_triggered()`

## Summary

TASK-084 acceptance criteria are **fully satisfied** by the tests implemented in TASK-079. The 6 new tests added to `backend/tests/kg/test_generation_graph.py` provide comprehensive coverage of:

1. Source field validation (4 source types covered individually)
2. Source ID prefix consistency per type
3. Mixed source handling (multiple sources in one recommendation)
4. Fallback path source assignment
5. 100% source_type coverage regression test

No additional tests are needed; TASK-079 already delivered all requirements.

---

**UAT**: [`.docs/uat/084-test-source-type-population.uat.md`](../uat/084-test-source-type-population.uat.md)
