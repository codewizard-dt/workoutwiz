# 082 — Test Routing Trace Coverage

> **Depends on**: [074-observability-adr](074-observability-adr.md), [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md), [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Write integration tests that verify audit_log contains a complete trace of all hub router, KG hub, retrieval sub-graph, and generation sub-graph node entries with non-zero latencies after a KG recommendation call. This confirms end-to-end observability coverage.

## Approach

The existing live test suite (backend/tests/test_live_llm.py) covers happy-path functionality. We will:

1. Add a test specifically for observability coverage
2. Verify that audit_log contains entries from: router (hub), kg_hub, retrieval nodes (5), generation nodes (3)
3. Assert all entries have non-zero latency_ms
4. Assert token counts are present where applicable

## Steps

### 1. Add test_audit_trace_coverage test  <!-- agent: general-purpose -->

Create new test in backend/tests/test_live_llm.py or a new observability test file:
```python
def test_audit_trace_coverage():
    # Send KNOWLEDGE_GRAPH intent to /chat
    response = post_chat(user_id="u1", query="Recommend exercises for my knee")
    
    audit_log = response.get("audit_log", [])
    
    # Assert router entry exists
    router_entries = [e for e in audit_log if e["event"] == "router"]
    assert len(router_entries) == 1
    assert router_entries[0]["latency_ms"] > 0
    
    # Assert kg_hub entry exists
    kg_hub_entries = [e for e in audit_log if e["event"] == "kg_hub"]
    assert len(kg_hub_entries) >= 1
    assert kg_hub_entries[0]["latency_ms"] > 0
    
    # ... similar assertions for retrieval and generation nodes
```

- [ ] test_audit_trace_coverage written

### 2. Verify retrieval node coverage  <!-- agent: general-purpose -->

In the test, assert all 5 retrieval nodes are covered:
```python
retrieval_events = {"retrieval_lookup_member", "retrieval_injury_traversal", 
                   "retrieval_preference_traversal", "retrieval_vector_search", 
                   "retrieval_assemble"}
actual_events = {e["event"] for e in audit_log if e["event"].startswith("retrieval_")}
assert retrieval_events.issubset(actual_events), f"Missing: {retrieval_events - actual_events}"
```

- [ ] Retrieval node coverage assertions added

### 3. Verify generation node coverage  <!-- agent: general-purpose -->

Assert all 3 generation nodes are covered:
```python
generation_events = {"kg_generation_safety_gate", "kg_generation_llm", "kg_generation_fallback"}
actual_events = {e["event"] for e in audit_log if e["event"].startswith("kg_generation_")}
assert generation_events.issubset(actual_events)
```

- [ ] Generation node coverage assertions added

### 4. Verify latency coverage  <!-- agent: general-purpose -->

Assert all entries have non-zero latency:
```python
for entry in audit_log:
    if entry["event"].startswith(("router", "kg_", "retrieval_")):
        assert entry.get("latency_ms", 0) > 0, f"No latency for {entry['event']}"
```

- [ ] Latency assertions added

### 5. Run test and verify  <!-- agent: general-purpose -->

Run the test against the live backend:
```bash
cd backend && pytest tests/test_live_llm.py::test_audit_trace_coverage -v
```

Ensure all assertions pass.

- [ ] Test passing

## Acceptance Criteria

- [ ] Test exists and is named test_audit_trace_coverage
- [ ] Test verifies router, kg_hub, all 5 retrieval, and all 3 generation node entries are present
- [ ] Test asserts all entries have non-zero latency_ms
- [ ] Test asserts token counts are present for LLM nodes
- [ ] Test is passing against live backend

---

**UAT**: [`.docs/uat/082-test-routing-trace-coverage.uat.md`](../uat/082-test-routing-trace-coverage.uat.md)
