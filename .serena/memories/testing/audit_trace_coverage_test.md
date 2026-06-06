# Audit Trace Coverage Test (Task 082)

## Test Location
- **File**: `backend/tests/test_agents_hub.py`
- **Function**: `test_audit_trace_coverage()` (lines 138-353)
- **Decorator**: `@pytest.mark.asyncio` (async test)

## What It Tests
Integration test verifying the audit_log contains a complete trace of all KG nodes:
1. **Router node** (1 entry) - initial routing decision
2. **KG hub node** (1 entry) - knowledge graph pipeline orchestration
3. **Retrieval nodes** (5 entries):
   - `retrieval_lookup_member` - member record lookup
   - `retrieval_injury_traversal` - injury history traversal
   - `retrieval_preference_traversal` - exercise preference traversal
   - `retrieval_vector_search` - semantic similarity search
   - `retrieval_assemble` - context assembly
4. **Generation nodes** (3 entries):
   - `kg_generation_llm` - LLM-based recommendation generation (has token counts)
   - `kg_generation_safety_gate` - safety filtering
   - `kg_generation_fallback` - fallback handler

**Minimum total**: 10 audit entries (1 router + 1 kg_hub + 5 retrieval + 3 generation)

## Key Assertions
1. **Router entry**: exactly 1, latency_ms > 0, route == "KNOWLEDGE_GRAPH", has tokens_in/out
2. **KG hub entry**: >= 1, latency_ms > 0, provider == "neo4j"
3. **Retrieval nodes**: all 5 event names must be in audit_log (uses set subtraction for detection)
4. **Generation nodes**: all 3 event names must be in audit_log (uses set subtraction for detection)
5. **All latencies**: >= 0 (non-negative; allows 0 for fallback)
6. **LLM nodes** (router, kg_generation_llm): must have tokens_in >= 0 and tokens_out >= 0
7. **Total count**: len(audit_log) >= 10

## Mock Structure
- **mock_rec**: Recommendation object with 1 exercise (ex-1, Squat)
- **mock_context**: Dict with safe_exercises, contraindicated_ids, preferred/performed exercises, vector_docs
- **retrieval_audit_log**: List of 5 dicts representing retrieval node events (latencies: 45, 120, 85, 200, 60 ms)
- **generation_audit_log**: List of 3 dicts (llm: 450ms + tokens, safety_gate: 25ms, fallback: 0ms)
- **mock_retrieval_graph.ainvoke()**: Returns {context, audit_log} with 50ms sleep
- **mock_generation_graph.ainvoke()**: Returns {recommendation, audit_log} with 50ms sleep

## Patching
```python
with patch("app.agents.hub.neo4j") as mock_neo4j, \
     patch("app.agents.hub.build_retrieval_graph", return_value=mock_retrieval_graph), \
     patch("app.agents.hub.build_generation_graph", return_value=mock_gen_graph):
    result = await _knowledge_graph_node(state)
```

## Test Execution
```bash
cd backend && python -m pytest tests/test_agents_hub.py::test_audit_trace_coverage -v
```
Expected: PASSED, ~1-2s runtime

## UAT Coverage
Task 082 has comprehensive UAT at `.docs/uat/082-test-routing-trace-coverage.uat.md` with 50+ test cases covering:
- Function existence & structure
- Individual assertion validation
- Mock data validation
- State & graph mocking
- Integration & behavioral flows
- Error scenarios & boundary conditions
- Pytest integration
- Documentation & clarity
