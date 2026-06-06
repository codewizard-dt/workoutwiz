# 078 — Instrument Explainability Tool

> **Depends on**: [074-observability-adr](074-observability-adr.md)
> **Blocks**: [080-add-explainability-confidence-score](080-add-explainability-confidence-score.md)
> **Parallel-safe with**: [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md)

## Objective

Add audit entry instrumentation to the explain_skipped_exercise() function in backend/app/kg/explainability.py to capture Neo4j query latency, traversal depth, path strength, and result counts. This provides visibility into why exercises were not recommended.

## Approach

The explainability tool (backend/app/kg/explainability.py) currently has no instrumentation. We will:

1. Wrap Neo4j queries in the explain_skipped_exercise() function with timing
2. Capture query metrics: latency, result count, path depth
3. Append audit entry to audit_log
4. Test that audit entries are present when explainability is queried

## Steps

### 1. Locate explainability tool and understand structure  <!-- agent: general-purpose -->

Read backend/app/kg/explainability.py:
- Understand explain_skipped_exercise() parameters and return value
- Identify all Neo4j queries (likely via traversal.py)
- Note any LLM calls if present

- [x] Explainability function located and documented <!-- Completed: 2026-06-06 -->

### 2. Add timing to Neo4j queries  <!-- agent: general-purpose -->

Wrap all Neo4j traversals in explain_skipped_exercise() with timing:
- `start = time.monotonic()` before query
- `latency_ms = int((end - start) * 1000)` after query
- Capture result count from query response

- [x] Neo4j query timing added <!-- Completed: 2026-06-06 -->

### 3. Create audit entry for explainability tool  <!-- agent: general-purpose -->

After queries complete, append an audit entry:
- Event name: `"kg_explainability"`
- Fields:
  ```python
  audit_entry = {
      "event": "kg_explainability",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),  # or extract from context
      "query_count": number_of_queries,
      "result_count": total_results,
      "path_depth": max_traversal_depth,
      "reason_type": reason_category,  # e.g. "contraindication", "preference", "previous"
  }
  ```

- [x] Audit entry appended <!-- Completed: 2026-06-06 -->

### 4. Return audit_log in explainability response  <!-- agent: general-purpose -->

Ensure the audit entry is included in the response or passed back to the calling context:
- If explain_skipped_exercise() is called from within a graph node, append to that node's audit_log
- If called from an endpoint, ensure the endpoint includes audit_entry in its response

- [x] Audit entry integrated into response flow <!-- Completed: 2026-06-06 -->

### 5. Test audit entry population  <!-- agent: general-purpose -->

Add test to verify:
- After calling explain_skipped_exercise(), audit_log contains an entry with event="kg_explainability"
- Entry has non-zero latency_ms and result_count
- query_count is >= 1

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] explainability tool wraps Neo4j queries with timing instrumentation <!-- Completed: 2026-06-06 -->
- [x] Audit entry includes latency_ms, query_count, result_count, path_depth, reason_type <!-- Completed: 2026-06-06 -->
- [x] Entry is appended to audit_log and returned <!-- Completed: 2026-06-06 -->
- [x] Integration test confirms audit entry after explain_skipped_exercise() call <!-- Completed: 2026-06-06 -->
- [x] Test is passing <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/completed/078-instrument-explainability-tool.uat.md`](../uat/completed/078-instrument-explainability-tool.uat.md)
