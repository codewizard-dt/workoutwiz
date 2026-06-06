# 080 — Add Explainability Confidence Score

> **Depends on**: [078-instrument-explainability-tool](078-instrument-explainability-tool.md)
> **Blocks**: [082-test-explainability-confidence](082-test-explainability-confidence.md)
> **Parallel-safe with**: none

## Objective

Calculate and return a confidence float (0.0–1.0) from the explain_skipped_exercise() function based on Neo4j traversal depth and path strength. This provides a quantitative measure of explanation quality to the assessor.

## Approach

The explainability tool currently has no confidence scoring. We will:

1. Measure Neo4j path depth and edge weights during traversal
2. Compute a confidence score from depth/strength (deeper paths = higher confidence)
3. Return confidence in the explain_skipped_exercise() response
4. Test confidence scoring

## Steps

### 1. Define confidence scoring algorithm  <!-- agent: general-purpose -->

Design a scoring function based on:
- Path depth (number of hops in Neo4j traversal)
- Edge weights or relationship types (strong constraint vs. weak signal)
- Coverage (single path vs. multiple corroborating paths)

Example: `confidence = min(1.0, path_depth / max_depth + edge_strength / max_strength)`

- [x] Scoring algorithm defined <!-- Completed: 2026-06-06 -->

### 2. Implement confidence calculation in explain_skipped_exercise()  <!-- agent: general-purpose -->

In backend/app/kg/explainability.py:
- Track path depth and edge strengths during Neo4j traversals
- Aggregate scores across multiple paths if applicable
- Return confidence float (0.0–1.0)

- [x] Confidence calculation implemented <!-- Completed: 2026-06-06 -->

### 3. Add confidence field to response  <!-- agent: general-purpose -->

Ensure explain_skipped_exercise() returns confidence:
```python
return {
    "reason": reason_string,
    "confidence": confidence_float,  # 0.0–1.0
    ...
}
```

- [x] Confidence field added to response <!-- Completed: 2026-06-06 -->

### 4. Test confidence scoring  <!-- agent: general-purpose -->

Add test to verify:
- Confidence is a float between 0 and 1
- Deeper paths yield higher confidence scores
- Multiple corroborating paths increase confidence

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] explain_skipped_exercise() calculates and returns a confidence float (0.0–1.0) <!-- Completed: 2026-06-06 -->
- [x] Confidence is based on Neo4j path depth and strength <!-- Completed: 2026-06-06 -->
- [x] Response includes confidence field <!-- Completed: 2026-06-06 -->
- [x] Integration test confirms confidence is present and in valid range <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/080-add-explainability-confidence-score.uat.md`](../uat/080-add-explainability-confidence-score.uat.md)
