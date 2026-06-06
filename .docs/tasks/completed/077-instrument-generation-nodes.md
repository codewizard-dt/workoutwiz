# 077 — Instrument Generation Sub-Graph Nodes

> **Depends on**: [074-observability-adr](074-observability-adr.md)
> **Blocks**: [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md)
> **Parallel-safe with**: [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md)

## Objective

Add audit entry instrumentation to the knowledge graph generation sub-graph nodes (safety gate, generation, fallback handler) to capture timing, exercise counts, and safety violations. This provides visibility into the recommendation generation and safety filtering pipeline.

## Approach

The generation sub-graph (backend/app/kg/generation_graph.py) currently has no instrumentation. We will:

1. Identify the 3 main nodes: safety_gate, generation, fallback_handler
2. Add timing to each node
3. Capture exercise counts (in/out) and safety violation metrics
4. Append audit entries to audit_log
5. Test that entries are present after a generation call

## Steps

### 1. Identify generation sub-graph nodes  <!-- agent: general-purpose -->

Read backend/app/kg/generation_graph.py and identify the 3 nodes:
- safety_gate — filter ContextSlice exercises through safety rules (contraindications, previous exercises)
- generation — call LLM to generate recommendations from filtered context
- fallback_handler — provide fallback exercises if generation fails or returns empty

Document entry/exit for each node and their dependencies.

- [x] All 3 generation nodes identified <!-- Completed: 2026-06-06 -->

### 2. Instrument safety_gate node  <!-- agent: general-purpose -->

Add timing and audit instrumentation:
- Capture exercise_in (count from ContextSlice)
- Capture exercise_out (count after filtering)
- Capture violations (count of exercises filtered due to safety rules)
- Audit entry:
  ```python
  audit_entry = {
      "event": "kg_generation_safety_gate",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),
      "exercise_in": len(context_slice["exercises"]),
      "exercise_out": len(filtered_exercises),
      "violations_filtered": exercise_in - exercise_out,
  }
  ```

- [x] safety_gate instrumented <!-- Completed: 2026-06-06 -->

### 3. Instrument generation node  <!-- agent: general-purpose -->

Add timing and LLM token extraction:
- Capture LLM call latency and tokens (input/output)
- Capture exercise count in generated recommendation
- Audit entry:
  ```python
  audit_entry = {
      "event": "kg_generation_llm",
      "model": model_name,
      "provider": "anthropic",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),
      "tokens_in": tokens_in,
      "tokens_out": tokens_out,
      "exercise_count": len(recommendation.exercises),
  }
  ```

- [x] generation node instrumented <!-- Completed: 2026-06-06 -->

### 4. Instrument fallback_handler node  <!-- agent: general-purpose -->

Add timing and fallback metrics:
- Capture whether fallback was triggered (boolean)
- Capture fallback exercise count
- Audit entry:
  ```python
  audit_entry = {
      "event": "kg_generation_fallback",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),
      "fallback_triggered": fallback_triggered,
      "exercise_count": len(fallback_exercises) if fallback_triggered else 0,
  }
  ```

- [x] fallback_handler instrumented <!-- Completed: 2026-06-06 -->

### 5. Test audit entry population  <!-- agent: general-purpose -->

Add test in backend/tests/ to verify:
- After a KG generation call, audit_log contains entries for all 3 nodes
- Each entry has non-zero latency_ms
- Exercise counts and violation counts are reasonable

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] All 3 generation nodes have timing instrumentation
- [x] safety_gate entry includes exercise_in, exercise_out, violations_filtered
- [x] generation entry includes LLM tokens and exercise_count
- [x] fallback_handler entry includes fallback_triggered flag
- [x] All entries have non-zero latency_ms
- [x] Integration test confirms all 3 audit entries are present

---
**UAT**: [`.docs/uat/completed/077-instrument-generation-nodes.uat.md`](../../uat/completed/077-instrument-generation-nodes.uat.md)
