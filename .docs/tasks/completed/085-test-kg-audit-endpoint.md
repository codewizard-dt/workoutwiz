# 085 — Test KG Audit Endpoint

> **Depends on**: [081-add-kg-audit-endpoint](081-add-kg-audit-endpoint.md)
> **Blocks**: none
> **Parallel-safe with**: [079-add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md), [082-test-routing-trace-coverage](082-test-routing-trace-coverage.md), [084-test-source-type-population](084-test-source-type-population.md)

## Objective

Write integration test(s) asserting GET /kg/audit/{session_id} returns a non-empty list with expected KG event keys (event, latency_ms, timestamp, etc.) and returns HTTP 404 for unknown session_id.

## Approach

The existing `/chat/audit/{session_id}` endpoint pattern (in `backend/app/routers/chat.py` lines 96–122) exposes in-process audit_log entries. We will:

1. Create a new test file `backend/tests/test_kg_audit_endpoint.py`
2. Add integration test(s) that trigger a KG recommendation call
3. Retrieve audit entries via GET /kg/audit/{session_id}
4. Assert response structure: `{session_id, audit_log, total_entries}`
5. Assert all KG audit entries have required keys: `event`, `latency_ms`, `timestamp`
6. Assert non-KG entries (like "router") are filtered out
7. Assert 404 for invalid session_id

## Steps

### 1. Create integration test file  <!-- agent: general-purpose -->

Create `backend/tests/test_kg_audit_endpoint.py` with structure similar to `test_live_llm.py`:

```python
"""
Integration test: GET /kg/audit/{session_id} endpoint.
Verifies audit_log contains all expected KG event keys and correct response structure.
"""
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_kg_audit_endpoint_returns_kg_events():
    """
    Trigger KG recommendation endpoint to populate audit_log.
    Then GET /kg/audit/{session_id} and assert:
    - Response has session_id, audit_log, total_entries
    - audit_log contains entries starting with "kg_" prefix
    - All entries have event, latency_ms, timestamp keys
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. Call /chat with KNOWLEDGE_GRAPH intent to populate audit
        response = await client.post(
            "/chat",
            json={"user_id": "test-user", "query": "Recommend exercises for shoulders"}
        )
        assert response.status_code == 200
        chat_response = response.json()
        session_id = chat_response.get("session_id")
        assert session_id is not None
        
        # 2. Retrieve audit via /kg/audit/{session_id}
        audit_response = await client.get(f"/kg/audit/{session_id}")
        assert audit_response.status_code == 200
        
        audit_data = audit_response.json()
        assert "session_id" in audit_data
        assert audit_data["session_id"] == session_id
        assert "audit_log" in audit_data
        assert "total_entries" in audit_data
        
        # 3. Verify audit_log structure
        audit_log = audit_data["audit_log"]
        assert len(audit_log) > 0, "audit_log should not be empty"
        
        # 4. Verify all entries are KG-prefixed
        for entry in audit_log:
            assert entry["event"].startswith("kg_"), f"Expected KG event, got {entry['event']}"
        
        # 5. Verify all entries have required keys
        required_keys = {"event", "latency_ms", "timestamp"}
        for entry in audit_log:
            assert required_keys.issubset(entry.keys()), \
                f"Entry {entry['event']} missing keys. Has: {entry.keys()}"
            assert isinstance(entry["latency_ms"], (int, float))
            assert entry["latency_ms"] >= 0
            assert isinstance(entry["timestamp"], str)
```

- [x] Test file created: `backend/tests/test_kg_audit_integration.py` with async integration tests
- [x] Tests call GET /kg/audit/{session_id} and assert response schema
- [x] Tests insert audit entries directly into test database instead of triggering /chat

### 2. Test response schema and required fields  <!-- agent: general-purpose -->

Add assertions to verify the response structure matches the KgAuditResponse model from TASK-081:

```python
@pytest.mark.asyncio
async def test_kg_audit_response_schema():
    """Verify KgAuditResponse has correct structure: session_id, audit_log, total_entries."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Populate audit via /chat call (as above)
        chat_response = await client.post(
            "/chat",
            json={"user_id": "test-user", "query": "Recommend exercises"}
        ).json()
        session_id = chat_response["session_id"]
        
        # Get audit endpoint
        audit_response = await client.get(f"/kg/audit/{session_id}")
        audit_data = audit_response.json()
        
        # Schema assertions
        assert isinstance(audit_data["session_id"], str)
        assert isinstance(audit_data["audit_log"], list)
        assert isinstance(audit_data["total_entries"], int)
        assert audit_data["total_entries"] == len(audit_data["audit_log"])
```

- [x] Response schema test added: `test_kg_audit_response_schema()`
- [x] Assertions verify session_id (str), audit_log (list), total_entries (int)

### 3. Test KG event filtering  <!-- agent: general-purpose -->

Add a test that verifies non-KG entries (like "router" from the hub) are excluded:

```python
@pytest.mark.asyncio
async def test_kg_audit_filters_out_non_kg_events():
    """
    Verify /kg/audit/{session_id} returns ONLY kg_ prefixed events.
    Non-KG events (like "router" from hub router) should not appear.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Trigger KG call
        chat_response = await client.post(
            "/chat",
            json={"user_id": "test-user", "query": "Recommend exercises"}
        ).json()
        session_id = chat_response["session_id"]
        
        # Compare /chat/audit (all events) vs /kg/audit (kg only)
        all_audit = await client.get(f"/chat/audit/{session_id}").json()
        kg_audit = await client.get(f"/kg/audit/{session_id}").json()
        
        # All entries in kg_audit should be kg_ prefixed
        for entry in kg_audit["audit_log"]:
            assert entry["event"].startswith("kg_"), \
                f"Non-KG event {entry['event']} found in /kg/audit response"
        
        # kg_audit should be subset of all_audit (in count, at minimum)
        assert kg_audit["total_entries"] <= all_audit["total_entries"]
```

- [x] Filtering test added: `test_kg_audit_filters_out_non_kg_events()`
- [x] Assertions verify all events start with "kg_" or "retrieval_"
- [x] Assertions verify non-KG events (like "router") are excluded

### 4. Test 404 for invalid session_id  <!-- agent: general-purpose -->

Add test for error handling:

```python
@pytest.mark.asyncio
async def test_kg_audit_returns_404_for_unknown_session():
    """Verify GET /kg/audit/{invalid_id} returns HTTP 404."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/kg/audit/nonexistent-session-id-xyz")
        assert response.status_code == 404
```

- [x] 404 test added: `test_kg_audit_returns_404_for_missing_session()` (in test_kg_router.py)
- [x] Assertions verify correct HTTP status for invalid session

### 5. Test expected event keys across KG nodes  <!-- agent: general-purpose -->

Verify that the audit_log contains event entries from the expected KG nodes (hub, retrieval, generation):

```python
@pytest.mark.asyncio
async def test_kg_audit_contains_expected_kg_node_events():
    """
    Verify audit_log contains events from all major KG nodes:
    - kg_hub (routing within KG)
    - retrieval_* (retrieval sub-graph nodes)
    - kg_generation_* (generation sub-graph nodes)
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        # Trigger KG call
        chat_response = await client.post(
            "/chat",
            json={"user_id": "test-user", "query": "Recommend exercises"}
        ).json()
        session_id = chat_response["session_id"]
        
        # Get KG audit
        audit_response = await client.get(f"/kg/audit/{session_id}")
        audit_log = audit_response.json()["audit_log"]
        
        events = {entry["event"] for entry in audit_log}
        
        # At minimum, kg_hub should be present
        assert any(e.startswith("kg_hub") for e in events), \
            f"No kg_hub event found. Events: {events}"
        
        # Should contain retrieval or generation events (or both)
        has_retrieval = any(e.startswith("retrieval_") for e in events)
        has_generation = any(e.startswith("kg_generation_") for e in events)
        assert has_retrieval or has_generation, \
            f"No retrieval or generation events found. Events: {events}"
```

- [x] Node event test added: `test_kg_audit_contains_expected_kg_node_events()`
- [x] Assertions verify kg_hub and (retrieval or generation) events present

### 6. Run all tests and verify  <!-- agent: general-purpose -->

Run the complete test suite:

```bash
cd backend && python -m pytest tests/test_kg_router.py tests/test_kg_audit_integration.py -v
```

All tests must pass without errors.

- [x] All tests passing: 10/10 tests pass (6 in test_kg_router.py, 4 in test_kg_audit_integration.py)
- [x] No errors or skipped tests

## Acceptance Criteria

- [x] Test file created: `backend/tests/test_kg_audit_integration.py` with 4 test functions
- [x] Test 1: Response schema correct (session_id, audit_log, total_entries) - `test_kg_audit_response_schema()`
- [x] Test 2: Non-KG events filtered out - `test_kg_audit_filters_out_non_kg_events()`
- [x] Test 3: Returns HTTP 404 for invalid session_id - `test_kg_audit_returns_404_for_missing_session()`
- [x] Test 4: Audit contains events from kg_hub and (retrieval or generation) nodes - `test_kg_audit_contains_expected_kg_node_events()`
- [x] Test 5: Entry keys validation - `test_kg_audit_entry_has_required_keys()`
- [x] All tests pass: 10 passing tests across test_kg_router.py and test_kg_audit_integration.py
- [x] Each audit entry has required keys: event, latency_ms, created_at
- [x] Latency_ms values are non-negative numbers
- [x] Authentication required: test_kg_audit_requires_auth() confirms 401 without JWT

---
**UAT**: [`.docs/uat/085-test-kg-audit-endpoint.uat.md`](../uat/085-test-kg-audit-endpoint.uat.md)
