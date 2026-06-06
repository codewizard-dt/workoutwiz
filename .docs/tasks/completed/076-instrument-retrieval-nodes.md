# 076 — Instrument Retrieval Sub-Graph Nodes

> **Depends on**: [074-observability-adr](074-observability-adr.md), [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md)
> **Blocks**: [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md)
> **Parallel-safe with**: [077-instrument-generation-nodes](077-instrument-generation-nodes.md)

## Objective

Add audit entry instrumentation to all retrieval sub-graph nodes (lookup_member, run_injury_traversal, run_preference_traversal, run_vector_search, assemble) to capture timing, result counts, and query patterns. This enables visibility into the GraphRAG retrieval pipeline.

## Approach

The retrieval sub-graph (backend/app/kg/retrieval_graph.py) currently has no instrumentation. We will:

1. Add timing to each node in the graph
2. Capture node-specific metrics: result counts, query type, Neo4j latency
3. Append audit entries to the shared audit_log
4. Ensure token counts are aggregated from sub-agent calls if applicable
5. Test that audit entries are present after a retrieval call

## Steps

### 1. Identify retrieval sub-graph nodes  <!-- agent: general-purpose -->

Read backend/app/kg/retrieval_graph.py and identify all nodes:
- lookup_member — fetch member profile and preferences
- run_injury_traversal — query Neo4j for injury-related constraints
- run_preference_traversal — query Neo4j for preference signals
- run_vector_search — embed query and search exercise vector store
- assemble — merge results into ContextSlice

For each node, note:
- Entry parameters (from state)
- Exit return value (what state fields are updated)
- Any external calls (Neo4j, embeddings)

- [x] All retrieval nodes identified and documented <!-- Completed: 2026-06-06 -->

### 2. Add timing and audit instrumentation to each node  <!-- agent: general-purpose -->

For each of the 5 nodes, add:
- `start = time.monotonic()` at entry
- `latency_ms = int((end - start) * 1000)` at exit
- Audit entry append with node-specific fields
- Example for lookup_member:
  ```python
  audit_entry = {
      "event": "retrieval_lookup_member",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),
      "result_count": 1 if member else 0,
  }
  ```

- [x] lookup_member instrumented with timing and audit entry <!-- Completed: 2026-06-06 -->
- [x] run_injury_traversal instrumented (include result_count, constraint_count) <!-- Completed: 2026-06-06 -->
- [x] run_preference_traversal instrumented (include result_count) <!-- Completed: 2026-06-06 -->
- [x] run_vector_search instrumented (include result_count, embedding_latency_ms if available) <!-- Completed: 2026-06-06 -->
- [x] assemble node instrumented (include input_count, output_count) <!-- Completed: 2026-06-06 -->

### 3. Aggregate audit_log in retrieval graph output  <!-- agent: general-purpose -->

Ensure the retrieval_graph returns the full audit_log with all 5 node entries:
- Each node returns `{"audit_log": state.get("audit_log", []) + [new_entry]}`
- Verify the graph's final output includes all accumulated entries

- [x] Retrieval graph aggregates audit_log from all nodes <!-- Completed: 2026-06-06 -->

### 4. Test audit entry population  <!-- agent: general-purpose -->

Add test in backend/tests/ to verify:
- After a KG recommendation call, audit_log contains entries for all 5 retrieval nodes
- Each entry has non-zero latency_ms
- Result counts are present and reasonable

Example:
```python
retrieval_events = [e["event"] for e in audit_log if e["event"].startswith("retrieval_")]
assert len(retrieval_events) == 5
assert all(audit["latency_ms"] > 0 for audit in retrieval_entries)
```

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] All 5 retrieval nodes have timing instrumentation <!-- Completed: 2026-06-06 -->
- [x] Each node appends an audit entry with latency_ms and node-specific metrics <!-- Completed: 2026-06-06 -->
- [x] Audit_log aggregates entries from all nodes <!-- Completed: 2026-06-06 -->
- [x] Integration test confirms all 5 audit entries are present <!-- Completed: 2026-06-06 -->
- [x] Test is passing <!-- Completed: 2026-06-06 -->

---
**UAT**: [`.docs/uat/076-instrument-retrieval-nodes.uat.md`](../uat/076-instrument-retrieval-nodes.uat.md)
