# 081 — Add GET /kg/audit/{session_id} Endpoint

> **Depends on**: [074-observability-adr](074-observability-adr.md), [075-instrument-kg-hub-node](075-instrument-kg-hub-node.md), [076-instrument-retrieval-nodes](076-instrument-retrieval-nodes.md), [077-instrument-generation-nodes](077-instrument-generation-nodes.md), [079-add-source-fields-to-recommended-exercise](079-add-source-fields-to-recommended-exercise.md)
> **Blocks**: none
> **Parallel-safe with**: none

## Objective

Create a new REST endpoint GET /kg/audit/{session_id} that exposes knowledge graph-specific audit log entries separate from the existing /chat/audit endpoint. This allows the assessor to inspect the full KG layer instrumentation (hub, retrieval, generation, explainability nodes).

## Approach

The existing pattern is /chat/audit/{session_id} in backend/app/routers/chat.py (lines 96–122). We will:

1. Create a new router (kg.py) or extend an existing KG router
2. Add the /kg/audit/{session_id} endpoint
3. Filter audit_log to only KG layer entries (event starts with "kg_")
4. Return response with session_id, audit_log, total_entries
5. Test the endpoint

## Steps

### 1. Create or identify KG router  <!-- agent: general-purpose -->

Check if backend/app/routers/kg.py exists:
- If not, create it with standard FastAPI router pattern
- If yes, add the new endpoint to it

- [ ] KG router file identified or created

### 2. Implement GET /kg/audit/{session_id} endpoint  <!-- agent: general-purpose -->

Add endpoint:
```python
@router.get("/kg/audit/{session_id}", response_model=KgAuditResponse)
async def get_kg_audit(session_id: str, request: Request):
    # Retrieve session state (from store or memory)
    # Filter audit_log for KG entries (event like "kg_*")
    # Return KgAuditResponse
    pass
```

Response model:
```python
class KgAuditResponse(BaseModel):
    session_id: str
    audit_log: list[dict[str, Any]]  # KG layer entries only
    total_entries: int
```

- [ ] Endpoint implemented

### 3. Add session state persistence  <!-- agent: general-purpose -->

Ensure the endpoint can retrieve session state:
- Session state should be stored (in-memory cache, database, or Redis)
- Endpoint retrieves audit_log by session_id
- Return 404 if session not found

- [ ] Session state retrieval implemented

### 4. Register router in main.py  <!-- agent: general-purpose -->

In backend/app/main.py:
- Import the KG router
- Register with `app.include_router(router, prefix="/kg")`
- Ensure it's accessible at /kg/audit/{session_id}

- [ ] Router registered in main.py

### 5. Test the endpoint  <!-- agent: general-purpose -->

Add integration test:
- Call KG recommendation endpoint to generate audit_log entries
- GET /kg/audit/{session_id}
- Assert response includes all KG-specific audit entries (event startswith "kg_")
- Assert non-KG entries (like "router") are filtered out
- Assert 404 for invalid session_id

- [ ] Test written and passing

## Acceptance Criteria

- [ ] GET /kg/audit/{session_id} endpoint exists in KG router
- [ ] Returns KgAuditResponse with session_id, audit_log (KG entries only), total_entries
- [ ] Filters out non-KG entries (chat router entries not included)
- [ ] Returns 404 for invalid session_id
- [ ] Requires JWT authentication (same as /chat/audit)
- [ ] Integration test confirms endpoint behavior
