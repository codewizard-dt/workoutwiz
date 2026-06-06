# 075 — Instrument KG Hub Node Routing Trace

> **Depends on**: [074-observability-adr](074-observability-adr.md)
> **Blocks**: [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md), [078-instrument-explainability-tool](078-instrument-explainability-tool.md), [079-add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md)
> **Parallel-safe with**: none

## Objective

Add audit entry instrumentation to the knowledge graph hub node that captures the KG invocation intent, confidence, and end-to-end latency. This mirrors the existing hub router pattern (backend/app/agents/hub.py lines 44–78) and establishes the observability baseline for the KG layer.

## Approach

The KG hub node (in backend/app/kg/hub.py or within the hub router) currently has no instrumentation. We will:

1. Identify the KG hub node entry point (likely where KNOWLEDGE_GRAPH intent is routed)
2. Add timing instrumentation using `time.monotonic()` 
3. Capture KG-specific fields: intent (KNOWLEDGE_GRAPH), member_id, context_size
4. Extract token counts from the retrieval sub-graph output
5. Append audit entry to the shared `audit_log` in AgentState
6. Add a test to verify audit entry structure after a KG recommendation call

## Steps

### 1. Locate and understand the KG hub node  <!-- agent: general-purpose -->

Read the KG hub invocation point in the codebase:
- Search for where KNOWLEDGE_GRAPH intent routes to the KG layer in `backend/app/agents/hub.py`
- Identify the KG graph invocation (likely `kg_graph.invoke()` or similar)
- Note the current state passing and return value handling

- [x] KG hub invocation point located and documented <!-- Completed: 2026-06-06 -->

### 2. Add timing instrumentation  <!-- agent: general-purpose -->

Wrap the KG graph invocation with timing logic:
- Import `time.monotonic()` at the top of the file
- Capture `start = time.monotonic()` before the invocation
- Capture `end = time.monotonic()` after the invocation
- Calculate `latency_ms = int((end - start) * 1000)`

- [x] Timing instrumentation added around KG invocation <!-- Completed: 2026-06-06 -->

### 3. Create audit entry for KG hub node  <!-- agent: general-purpose -->

After the KG invocation completes, append an audit entry to `state["audit_log"]`:
- Event name: `"kg_hub"`
- Fields: `event`, `model`, `provider`, `latency_ms`, `user_id`, `intent` (always "KNOWLEDGE_GRAPH"), `confidence` (optional, from KG logic if available)
- Token counts: extract from KG result if available (retrieval sub-graph should return token metadata), otherwise 0
- Example structure:
  ```python
  audit_entry = {
      "event": "kg_hub",
      "model": "n/a",  # KG layer may not have a direct LLM; retrieval sub-agents do
      "provider": "neo4j",  # or mixed if retrieval sub-graphs have LLM
      "intent": "KNOWLEDGE_GRAPH",
      "latency_ms": latency_ms,
      "user_id": state.get("user_id"),
      "tokens_in": kg_result.get("tokens_in", 0),
      "tokens_out": kg_result.get("tokens_out", 0),
  }
  ```

- [x] Audit entry structure defined and appended to audit_log <!-- Completed: 2026-06-06 -->

### 4. Return updated audit_log in state  <!-- agent: general-purpose -->

Ensure the updated `audit_log` is returned as part of the node's state return:
- Return: `{"audit_log": state.get("audit_log", []) + [audit_entry]}`
- This follows the pattern from the hub router node

- [x] Updated audit_log returned in node output <!-- Completed: 2026-06-06 -->

### 5. Test audit entry population  <!-- agent: general-purpose -->

Add or update an integration test in `backend/tests/` (likely in a KG test file or the existing live test suite) to verify:
- After a KG recommendation call via `/chat` with a KNOWLEDGE_GRAPH intent
- The response's `audit_log` contains an entry with `event: "kg_hub"`
- The entry has non-zero `latency_ms`
- Optional fields are present (user_id, intent)

Example test assertion:
```python
assert any(e["event"] == "kg_hub" for e in response["audit_log"])
assert response["audit_log"][-2]["latency_ms"] > 0  # KG hub entry is near the end
```

- [x] Test written and passing <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] KG hub node in backend code has timing instrumentation
- [x] Audit entry with event="kg_hub" is appended to audit_log
- [x] Entry includes latency_ms, user_id, intent, and token counts (if available)
- [x] Updated audit_log is returned from the KG hub node
- [x] Integration test confirms audit entry population after a KG call
- [x] Test is passing and committed

---
**UAT**: [`.docs/uat/075-instrument-kg-hub-node.uat.md`](../uat/075-instrument-kg-hub-node.uat.md)
