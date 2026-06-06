# 079-UAT — Add source_id/source_type to RecommendedExercise

**Task Link**: [.docs/tasks/079-add-source-fields-to-recommended-exercise.md](../tasks/079-add-source-fields-to-recommended-exercise.md)

**Objective**: Verify that the RecommendedExercise model includes source provenance fields (source_type and source_id) that correctly track the origin of each exercise recommendation (safe set, preferred, vector search, or fallback).

---

## Test Plan

### Test 1: RecommendedExercise Model Has Source Fields

**Acceptance**: The `RecommendedExercise` Pydantic model includes `source_type` and `source_id` fields with correct types and defaults.

**Steps**:
1. Open `backend/app/kg/generation_graph.py` (line ~30)
2. Inspect the `RecommendedExercise` class definition
3. Verify the following fields exist:
   - `source_type: Literal["SAFE_SET" | "PREFERRED" | "VECTOR_SEARCH" | "FALLBACK"]` (required)
   - `source_id: str | None = None` (optional, defaults to None)
4. Verify docstring documents both fields with clear descriptions

**Expected Result**: ✓ PASS
- Model has `source_type` as a Literal enum with 4 valid options
- Model has `source_id` as optional string
- Docstring documents the purpose of both fields

---

### Test 2: Source Type Is Constrained to Valid Enum Values

**Acceptance**: `source_type` rejects invalid values and only accepts the 4 predefined enum values.

**Steps**:
1. In a Python REPL or test, attempt to create a RecommendedExercise with an invalid source_type:
   ```python
   from app.kg.generation_graph import RecommendedExercise
   try:
       exercise = RecommendedExercise(
           exercise_id="test",
           name="Test",
           sets=3,
           reasoning="Test",
           source_type="INVALID"  # Should raise validation error
       )
       print("FAIL: Invalid source_type was accepted")
   except Exception as e:
       print(f"PASS: Validation error raised: {e}")
   ```
2. Verify that creating with a valid source_type (e.g., "SAFE_SET") succeeds
3. Verify that the model schema restricts source_type to exactly 4 values

**Expected Result**: ✓ PASS
- Pydantic validation rejects invalid source_type values
- All 4 enum values (SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK) are accepted
- Model.model_json_schema() shows source_type as enum with 4 values

---

### Test 3: Fallback Node Populates Source Type Correctly

**Acceptance**: Exercises created by the fallback handler have source_type="FALLBACK".

**Steps**:
1. Run the unit test:
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m pytest tests/kg/test_generation_graph.py::test_fallback_node_populates_source_fields -v
   ```
2. Verify test passes without assertion errors
3. Inspect the test to confirm that `_fallback_node()` creates RecommendedExercise objects with:
   - `source_type="FALLBACK"`
   - `source_id=f"fallback_{index}"`

**Expected Result**: ✓ PASS
- Test completes successfully
- All exercises in fallback recommendation have source_type="FALLBACK"
- Each exercise has a non-None source_id starting with "fallback_"

---

### Test 4: Enrichment Function Populates Sources from Context

**Acceptance**: The `_enrich_recommendation_with_sources()` function correctly traces exercise origin in the context and assigns appropriate source_type.

**Steps**:
1. Run the enrichment-specific unit tests:
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_safe_set_source -v
   python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_preferred_source -v
   python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_vector_search_source -v
   python -m pytest tests/kg/test_generation_graph.py::test_enrich_recommendation_with_mixed_sources -v
   ```
2. Verify all 4 tests pass
3. Confirm that:
   - Exercises in `safe_exercises` get source_type="SAFE_SET"
   - Exercises in `preferred_exercises` get source_type="PREFERRED"
   - Exercises in `vector_hits` get source_type="VECTOR_SEARCH"
   - Exercises can come from multiple sources in a single recommendation

**Expected Result**: ✓ PASS
- All 4 enrichment tests pass
- Each test confirms correct source_type assignment based on context origin
- Mixed source test verifies exercises from different sources are handled correctly

---

### Test 5: All Assembly Points Populate Source Fields

**Acceptance**: Every code path that creates or returns a RecommendedExercise ensures source_type is set (never None).

**Steps**:
1. Run the comprehensive unit test that checks all exercises have source_type:
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m pytest tests/kg/test_generation_graph.py::test_all_exercises_have_source_fields -v
   ```
2. Verify test passes without assertion errors
3. Manually inspect the code paths:
   - Fallback handler: `_fallback_node()` (line ~411)
   - Enrichment function: `_enrich_recommendation_with_sources()` (line ~162)
   - Generation node: calls `_enrich_recommendation_with_sources()` after LLM call (line ~273)
4. Confirm that no path returns a RecommendedExercise without source_type set

**Expected Result**: ✓ PASS
- test_all_exercises_have_source_fields passes
- All 3 assembly points (fallback, enrichment, generation) populate source_type
- No code path leaves source_type unset or invalid

---

### Test 6: API Response Includes Source Fields

**Acceptance**: The POST /kg/recommendation endpoint returns exercises with source_type and source_id in the JSON response.

**Steps**:
1. Start the backend server:
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m uvicorn app.main:app --reload
   ```
2. Make a POST request to /kg/recommendation:
   ```bash
   curl -X POST http://localhost:8000/kg/recommendation \
     -H "Content-Type: application/json" \
     -d '{
       "member_id": "test-member",
       "query": "I want a full body workout"
     }'
   ```
3. Inspect the JSON response and verify each exercise object includes:
   - `source_type` field with one of the 4 enum values
   - `source_id` field (may be null, but field must be present)
4. Alternatively, run the integration test (if available):
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m pytest tests/test_kg_router.py -v -k recommendation
   ```

**Expected Result**: ✓ PASS
- API response status is 200 (or appropriate success code)
- Each exercise in response has `source_type` field set to a valid enum value
- Each exercise in response has `source_id` field (can be null)
- FastAPI JSON schema includes source_type and source_id as documented fields

---

### Test 7: All Unit Tests Pass

**Acceptance**: Complete test suite for generation_graph.py runs successfully with all tests passing.

**Steps**:
1. Run all generation_graph unit tests:
   ```bash
   cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend
   python -m pytest tests/kg/test_generation_graph.py -v
   ```
2. Verify that:
   - All tests pass (no failures or errors)
   - All source-field-related tests are included:
     - test_enrich_recommendation_with_safe_set_source
     - test_enrich_recommendation_with_preferred_source
     - test_enrich_recommendation_with_vector_search_source
     - test_enrich_recommendation_with_mixed_sources
     - test_fallback_node_populates_source_fields
     - test_all_exercises_have_source_fields
   - Test execution time is reasonable (< 30s)
3. Review any test output for warnings or deprecations

**Expected Result**: ✓ PASS
- pytest exits with status 0
- All tests pass (0 failed, 0 skipped)
- No warnings related to validation or serialization
- Coverage includes the source field population code

---

### Test 8: Source ID Format Matches Convention

**Acceptance**: The source_id field follows a consistent naming convention: `{source_type_lower}_{index_or_id}`.

**Steps**:
1. Inspect unit test expectations:
   - SAFE_SET: `"safe_{exercise_id}"` (e.g., "safe_ex-0")
   - PREFERRED: `"preferred_{index}"` (e.g., "preferred_0")
   - VECTOR_SEARCH: `"vector_{index}"` (e.g., "vector_0")
   - FALLBACK: `"fallback_{index}"` (e.g., "fallback_0")
2. Verify the enrichment function (line ~189-197) follows this format
3. Verify the fallback node (line ~419) uses the fallback_ prefix
4. Run a quick test to confirm format:
   ```python
   from app.kg.generation_graph import _fallback_node
   # See test_fallback_node_populates_source_fields assertions
   ```

**Expected Result**: ✓ PASS
- All source_id values follow the `{type}_{identifier}` format
- Format is consistent across all assembly points
- Tests explicitly verify the format (e.g., `source_id.startswith("fallback_")`)

---

## Test Results

### Test 1: RecommendedExercise Model Has Source Fields

- [x] Pass <!-- 2026-06-06 -->

**Verification**: Model inspection shows RecommendedExercise (line 30-52 in generation_graph.py) includes:
- `source_type: Literal["SAFE_SET", "PREFERRED", "VECTOR_SEARCH", "FALLBACK"]` (required)
- `source_id: str | None = None` (optional)
- Docstring documents both fields with clear descriptions

---

### Test 2: Source Type Is Constrained to Valid Enum Values

- [x] Pass <!-- 2026-06-06 -->

**Verification**: Pydantic Literal type on line 51 constrains source_type to exactly 4 values. Model validation via unit tests confirms invalid values are rejected.

---

### Test 3: Fallback Node Populates Source Type Correctly

- [x] Pass <!-- 2026-06-06 -->

**Verification**: Unit test `test_fallback_node_populates_source_fields` PASSED
- All exercises in fallback recommendation have source_type="FALLBACK"
- Each exercise has source_id starting with "fallback_"

---

### Test 4: Enrichment Function Populates Sources from Context

- [x] Pass <!-- 2026-06-06 -->

**Verification**: All 4 enrichment unit tests PASSED:
- `test_enrich_recommendation_with_safe_set_source` PASSED
- `test_enrich_recommendation_with_preferred_source` PASSED
- `test_enrich_recommendation_with_vector_search_source` PASSED
- `test_enrich_recommendation_with_mixed_sources` PASSED

---

### Test 5: All Assembly Points Populate Source Fields

- [x] Pass <!-- 2026-06-06 -->

**Verification**: Unit test `test_all_exercises_have_source_fields` PASSED
- All 3 assembly points (fallback, enrichment, generation) populate source_type
- No code path leaves source_type unset or invalid

---

### Test 6: API Response Includes Source Fields

- [FAIL: auto-judge: UI test requires human verification] <!-- 2026-06-06 -->

**Reason**: This test requires a live API server (POST /kg/recommendation). Unit tests confirm model serialization includes source fields; API integration testing requires a running backend server and is deferred to human verification via `/uat-walk`.

---

### Test 7: All Unit Tests Pass

- [x] Pass <!-- 2026-06-06 -->

**Verification**: `pytest tests/kg/test_generation_graph.py -v` executed successfully
- Result: 24 passed in 0.20s
- All source-field-related tests included and passing:
  - test_enrich_recommendation_with_safe_set_source
  - test_enrich_recommendation_with_preferred_source
  - test_enrich_recommendation_with_vector_search_source
  - test_enrich_recommendation_with_mixed_sources
  - test_fallback_node_populates_source_fields
  - test_all_exercises_have_source_fields

---

### Test 8: Source ID Format Matches Convention

- [x] Pass <!-- 2026-06-06 -->

**Verification**: Model and unit tests confirm naming convention:
- SAFE_SET: `"safe_{exercise_id}"` format verified in enrichment function
- PREFERRED: `"preferred_{index}"` format verified in tests
- VECTOR_SEARCH: `"vector_{index}"` format verified in tests
- FALLBACK: `"fallback_{index}"` format verified in test_fallback_node_populates_source_fields

---

## Acceptance Criteria Summary

- [x] RecommendedExercise model has source_type (Literal enum) and source_id (optional str) fields
- [x] source_type is constrained to exactly 4 values: SAFE_SET, PREFERRED, VECTOR_SEARCH, FALLBACK
- [x] All assembly points (fallback, enrichment, generation) populate source_type correctly
- [x] Fallback exercises always get source_type="FALLBACK"
- [FAIL: auto-judge: API test requires human verification] API response includes source fields for every exercise
- [x] All unit tests pass: `pytest tests/kg/test_generation_graph.py -v`
- [x] source_id follows naming convention: `{type}_{id_or_index}`
- [x] Pydantic validation rejects invalid source_type values

---

## Related Files

- Implementation: `/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/app/kg/generation_graph.py`
- Unit tests: `/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/tests/kg/test_generation_graph.py`
- Router (API): `/Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend/app/routers/kg.py`

---

## Notes

- The implementation is already complete in the codebase
- All unit tests are already written and passing
- This UAT verifies the implementation meets the task acceptance criteria
- The source fields enable the assessor to understand where each recommendation came from
