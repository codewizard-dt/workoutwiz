# 079 — Add source_id/source_type to RecommendedExercise

> **Depends on**: [074-observability-adr](074-observability-adr.md), [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md), [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md)
> **Blocks**: [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md)
> **Parallel-safe with**: none

## Objective

Extend the RecommendedExercise Pydantic model to include source provenance fields (source_type and source_id) that track where each exercise recommendation originated (safe set, preferred, vector search, or fallback). This enables the assessor to understand the recommendation rationale.

## Approach

The RecommendedExercise model (backend/app/kg/generation_graph.py line 29) currently has no source provenance. We will:

1. Add two new fields to the model: source_type and source_id
2. Populate these fields during recommendation assembly in the generation sub-graph
3. Ensure they are returned in the KG recommendation response
4. Test that all exercises in a recommendation have source fields populated

## Steps

### 1. Extend RecommendedExercise model  <!-- agent: general-purpose -->

Update backend/app/kg/generation_graph.py (line 29) to add fields:
```python
class RecommendedExercise(BaseModel):
    exercise_id: str
    exercise_name: str
    # ... existing fields ...
    source_type: Literal["SAFE_SET" | "PREFERRED" | "VECTOR_SEARCH" | "FALLBACK"]
    source_id: str | None = None  # optional: query ID, context ID, or fallback set ID
```

Document each field in docstring.

- [ ] RecommendedExercise model extended with source_type and source_id

### 2. Identify recommendation assembly points  <!-- agent: general-purpose -->

Locate where RecommendedExercise objects are created in the generation sub-graph:
- In the safety_gate node (exercises filtered from ContextSlice)
- In the generation node (exercises from LLM output)
- In the fallback_handler (fallback exercises)

For each point, determine the source:
- SAFE_SET: exercises that passed safety_gate
- PREFERRED: exercises from preference traversal in retrieval context
- VECTOR_SEARCH: exercises from vector_search in retrieval context
- FALLBACK: exercises from fallback_handler

- [ ] Recommendation assembly points identified

### 3. Populate source_type during recommendation assembly  <!-- agent: general-purpose -->

Update each assembly point to set source_type:
- In safety_gate: exercises passing filter are SAFE_SET (mark origin)
- In generation: LLM-picked exercises inherit source from context (PREFERRED or VECTOR_SEARCH based on context provenance)
- In fallback: exercises are FALLBACK

Example:
```python
recommended = RecommendedExercise(
    exercise_id=exercise["id"],
    exercise_name=exercise["name"],
    # ... other fields ...
    source_type="PREFERRED",
    source_id=f"context_{context_id}",
)
```

- [ ] source_type populated at all assembly points
- [ ] source_id populated where applicable (context ID, fallback set ID, etc.)

### 4. Update response serialization  <!-- agent: general-purpose -->

Ensure RecommendedExercise fields are returned in the API response:
- Verify FastAPI schema exports source_type and source_id
- Test that POST /kg/recommendation response includes these fields in each exercise object

- [ ] API response includes source fields

### 5. Test source field population  <!-- agent: general-purpose -->

Add test to verify:
- After a KG recommendation call, all exercises in the response have source_type set
- source_type is one of the 4 valid enum values
- source_id is populated for exercises with available context

Example:
```python
for exercise in recommendation.exercises:
    assert hasattr(exercise, "source_type")
    assert exercise.source_type in ["SAFE_SET", "PREFERRED", "VECTOR_SEARCH", "FALLBACK"]
```

- [ ] Test written and passing

## Acceptance Criteria

- [ ] RecommendedExercise model has source_type (enum) and source_id (optional str) fields
- [ ] All assembly points populate source_type correctly
- [ ] API response includes source fields for every exercise
- [ ] Integration test confirms source_type is set and valid
- [ ] Test is passing
