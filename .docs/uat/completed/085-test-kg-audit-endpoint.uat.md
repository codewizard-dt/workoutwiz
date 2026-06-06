# UAT: KG Audit Endpoint

> **Source task**: [`.docs/tasks/085-test-kg-audit-endpoint.md`](../tasks/085-test-kg-audit-endpoint.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running at `http://localhost:8000`
- [ ] PostgreSQL test database with `audit_log` table initialized
- [ ] Valid JWT auth token available in `$UAT_AUTH_TOKEN` environment variable
- [ ] Test user created and authenticated

---

## API Tests

### UAT-API-001: Retrieve KG Audit Entries with Valid Session
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the endpoint returns KG-specific audit entries filtered by session_id with correct response structure
- **Steps**:
  1. Use a test session_id that has pre-populated KG audit entries (kg_hub_router, retrieval_vector_search events)
  2. Run the curl command below with a valid JWT token
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-kg-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: `200 OK` with response body containing:
  ```json
  {
    "session_id": "<test-session-id-with-kg-events>",
    "audit_log": [
      {
        "event": "kg_hub_router",
        "latency_ms": 42,
        "created_at": "2025-01-01T12:00:00",
        "session_id": "<test-session-id-with-kg-events>"
      },
      {
        "event": "retrieval_vector_search",
        "latency_ms": 150,
        "created_at": "2025-01-01T12:00:01",
        "session_id": "<test-session-id-with-kg-events>"
      }
    ],
    "total_entries": 2
  }
  ```
  - All response fields present and correctly typed
  - `session_id` matches request parameter
  - `total_entries` matches length of `audit_log` array
  - All events start with "kg_" or "retrieval_"
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: Verify Response Schema Structure
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm response has exactly the required top-level fields with correct types
- **Steps**:
  1. Query an existing session with KG audit entries
  2. Run the curl command and verify response structure
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-kg-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{session_id: .session_id, audit_log_type: (.audit_log | type), total_entries_type: (.total_entries | type), total_entries_value: .total_entries}'
  ```
- **Expected Result**: `200 OK` with JSON object showing:
  - `session_id` is a string
  - `audit_log` is an array
  - `total_entries` is an integer
  - `total_entries` value matches the count of items in the audit_log array
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: Filter Out Non-KG Events
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that endpoint only returns events starting with "kg_" or "retrieval_" and excludes other events like "router" or "chat_*"
- **Steps**:
  1. Use a test session_id that has mixed events: KG events (kg_hub_router, retrieval_search), non-KG events (router, chat_*), and other events
  2. Query the endpoint
  3. Verify response contains only KG events
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-mixed-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.audit_log[].event' | sort
  ```
- **Expected Result**: `200 OK` response where:
  - Only events starting with "kg_" or "retrieval_" appear in the audit_log
  - Non-KG events (router, chat_*, etc.) are filtered out
  - Example: "kg_hub_router", "retrieval_vector_search" present; "router" absent
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: Verify Required Fields in Each Entry
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm each audit entry has required fields: event, latency_ms, and created_at
- **Steps**:
  1. Query a session with KG audit entries
  2. Check that each entry contains the required fields
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-kg-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.audit_log[] | {event, latency_ms, created_at}'
  ```
- **Expected Result**: `200 OK` where each audit entry contains:
  - `event`: string (required)
  - `latency_ms`: number (required, must be non-negative)
  - `created_at`: string in ISO 8601 format (required)
  - Optional fields may be present: model, provider, tokens_in, tokens_out, node_name, source_type, source_id, session_id
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-005: Latency Values Are Non-Negative
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify all latency_ms values in audit entries are non-negative integers or floats
- **Steps**:
  1. Query endpoint for a session with KG events
  2. Check that latency_ms values are numbers >= 0
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-kg-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.audit_log[] | .latency_ms | select(type == "number" and . >= 0)]'
  ```
- **Expected Result**: `200 OK` where:
  - All latency_ms values are numbers (int or float)
  - All latency_ms values are >= 0
  - Length of filtered array matches length of audit_log
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: Entries Ordered by Created_At
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify audit entries are ordered chronologically by created_at timestamp (ascending)
- **Steps**:
  1. Query endpoint for session with multiple KG events spanning different timestamps
  2. Verify entries are in order
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-kg-events>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.audit_log[] | .created_at]'
  ```
- **Expected Result**: `200 OK` with array of created_at timestamps in ascending (chronological) order
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-007: Returns 404 for Unknown Session
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify endpoint returns HTTP 404 when querying a session_id that does not exist
- **Steps**:
  1. Use a session_id that has never been created (e.g., "nonexistent-session-xyz-12345")
  2. Run the curl command
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/nonexistent-session-xyz-12345' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: `404 Not Found` with error response containing:
  - `detail` field with message indicating session not found (e.g., "Session 'nonexistent-session-xyz-12345' not found")
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-008: Returns 401 When Not Authenticated
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: false
- **Description**: Verify endpoint returns HTTP 401 Unauthorized when JWT token is missing or invalid
- **Steps**:
  1. Make request without Authorization header
  2. Verify 401 response
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/any-session-id'
  ```
- **Expected Result**: `401 Unauthorized` with error response indicating authentication required
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-009: Handles Optional Fields Correctly
- **Endpoint**: `GET /kg/audit/{session_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify optional fields (model, provider, tokens_in, tokens_out, node_name, source_type, source_id) are included in response when present in database
- **Steps**:
  1. Use a test session_id with audit entries that have optional fields populated (e.g., model="claude-3-5-sonnet", provider="anthropic", tokens_in=100, tokens_out=50)
  2. Query the endpoint
  3. Verify optional fields appear in the response
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/kg/audit/<test-session-id-with-optional-fields>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.audit_log[0]'
  ```
- **Expected Result**: `200 OK` where entries containing optional fields display them in the response:
  - `model` present if set
  - `provider` present if set
  - `tokens_in` present if set
  - `tokens_out` present if set
  - `node_name` present if set
  - `source_type` present if set
  - `source_id` present if set
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Empty Audit Log for Existing Session
- **Scenario**: A session exists in the database but has no KG audit entries (only non-KG events like "router" or "chat_*")
- **Steps**:
  1. Create or use a session_id with only non-KG events
  2. Query GET /kg/audit/{session_id}
- **Expected Result**: Either:
  - `404 Not Found` if no KG entries exist for the session (per implementation at line 275 of kg.py), OR
  - `200 OK` with `audit_log: []` and `total_entries: 0` if the implementation treats this as a valid response
  - **Verification**: Check actual implementation behavior; current implementation returns 404 when no entries match (line 276)
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Session ID with Special Characters
- **Scenario**: A valid session_id contains hyphens, underscores, or dots (realistic UUID/session format)
- **Steps**:
  1. Use a session_id like "test-session-id-2025-01-06"
  2. Query the endpoint with this session_id
- **Expected Result**: `200 OK` with audit_log for that session, or `404 Not Found` if session does not exist; endpoint handles special characters in path parameter correctly
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-003: Large Audit Log Response
- **Scenario**: A session has many KG audit entries (50+ events)
- **Steps**:
  1. Use a session_id with multiple audit events
  2. Query the endpoint
- **Expected Result**: `200 OK` with:
  - All entries returned (no truncation)
  - `total_entries` matches actual count
  - Response remains valid JSON
  - All entries properly ordered by created_at
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: End-to-End KG Audit Retrieval Workflow
- **Components**: POST /chat (triggers KG), GET /kg/audit/{session_id}
- **Flow**: User triggers a chat request with knowledge graph intent → chat endpoint populates audit_log → user queries /kg/audit to view KG-specific events
- **Steps**:
  1. POST to /chat with query that triggers KNOWLEDGE_GRAPH routing (e.g., "Recommend exercises for shoulders")
  2. Extract session_id from response
  3. GET /kg/audit/{session_id}
  4. Verify response contains kg_* and retrieval_* events
- **Expected Result**: 
  - POST /chat returns 200 with session_id
  - GET /kg/audit/{session_id} returns 200
  - audit_log contains at least one kg_* event and at least one retrieval_* or kg_generation_* event
  - All events ordered chronologically
  - total_entries > 0
- [FAIL: auto-judge: integration test requires /chat endpoint invocation with live KG pipeline — use /uat-walk] <!-- 2026-06-06 -->

### UAT-INT-002: Compare KG Audit vs Full Chat Audit
- **Components**: GET /chat/audit/{session_id} (all events), GET /kg/audit/{session_id} (KG events only)
- **Flow**: Trigger KG call → retrieve full audit → retrieve KG-only audit → verify KG audit is subset
- **Steps**:
  1. Trigger a KG-enabled chat request
  2. Retrieve session_id
  3. GET /chat/audit/{session_id} to get all events
  4. GET /kg/audit/{session_id} to get KG-only events
  5. Compare event counts and prefixes
- **Expected Result**:
  - /chat/audit returns all events (may include "router", "chat_*", "kg_*", "retrieval_*")
  - /kg/audit returns only "kg_*" and "retrieval_*" events
  - total_entries in /kg/audit <= total_entries in /chat/audit
  - All events in /kg/audit have correct prefixes
- [FAIL: auto-judge: integration test requires live /chat endpoint and KG pipeline execution — use /uat-walk] <!-- 2026-06-06 -->

### UAT-INT-003: KG Audit Reflects All Node Types
- **Components**: KG hub router, retrieval sub-graph, generation sub-graph, /kg/audit endpoint
- **Flow**: Trigger full KG recommendation pipeline → audit_log populates with hub, retrieval, and generation events → verify all node types appear
- **Steps**:
  1. POST /kg/recommend with a valid request
  2. Extract session_id from response (if available via indirect means)
  3. Query /kg/audit with the session_id
  4. Verify events from all major KG nodes
- **Expected Result**:
  - audit_log contains at least one event starting with "kg_hub"
  - audit_log contains at least one event starting with "retrieval_"
  - audit_log may contain events starting with "kg_generation_"
  - total_entries >= 2 (minimum: kg_hub + retrieval)
- [FAIL: auto-judge: integration test requires POST /kg/recommend execution — use /uat-walk] <!-- 2026-06-06 -->

---

## Manual Test Cases (Not Automated)

### UAT-MANUAL-001: Performance with Large Session ID
- **Description**: Verify endpoint performs well when querying a session with 100+ audit entries
- **Steps**:
  1. Manually populate a test session with 100 audit entries
  2. Query /kg/audit/{session_id}
  3. Measure response time
- **Expected Result**: Response completes in < 1 second; all entries returned with correct ordering
- [FAIL: auto-judge: manual test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

---
