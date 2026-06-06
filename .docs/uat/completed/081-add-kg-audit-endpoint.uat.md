# UAT: Add GET /kg/audit/{session_id} Endpoint

> **Source task**: [`.docs/tasks/081-add-kg-audit-endpoint.md`](../tasks/081-add-kg-audit-endpoint.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] `backend/` Python environment installed (`pip install -e ".[dev]"` from `backend/`)
- [ ] Working directory for test commands is `backend/`
- [ ] PostgreSQL available (tests use test database)
- [ ] No live Neo4j or OpenAI connection required — all external calls are mocked

---

## Integration Tests (pytest)

The /kg/audit/{session_id} endpoint retrieves knowledge graph-specific audit log entries from PostgreSQL and filters out non-KG entries.

### UAT-INT-001: GET /kg/audit/{session_id} returns 200 with valid session containing KG entries

- **Test**: `tests/test_kg_router.py::test_kg_audit_returns_kg_entries_only`
- **Description**: Insert audit entries for a session (mix of KG and non-KG), then call GET /kg/audit/{session_id}. Verify the response includes only entries with event starting with "kg_" or "retrieval_", excludes non-KG entries, and response has correct structure.
- **Steps**:
  1. Run the command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_returns_kg_entries_only -v
  ```
- **Expected Result**: Test passes (`PASSED`). Response status is 200. `response.session_id == session_id`. `response.audit_log` contains only KG entries (event starts with "kg_" or "retrieval_"). Non-KG entries (e.g., event="router", "chat_*") are excluded. `response.total_entries` equals the count of KG entries.
- [ ] Pass

### UAT-INT-002: GET /kg/audit/{session_id} returns correct response schema with all fields

- **Test**: `tests/test_kg_router.py::test_kg_audit_response_has_correct_schema`
- **Description**: Call GET /kg/audit/{session_id} with a valid session. Verify the response matches KgAuditResponse schema: has `session_id` (str), `audit_log` (list of dicts), `total_entries` (int). Each audit entry should include event, session_id, created_at, and optional fields like latency_ms, tokens_in, tokens_out, node_name, source_type, source_id.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_response_has_correct_schema -v
  ```
- **Expected Result**: Test passes (`PASSED`). Response JSON deserializes to KgAuditResponse. Has keys: `session_id`, `audit_log`, `total_entries`. Each entry in `audit_log` is a dict with `event` and `created_at`. `total_entries` is an int.
- [ ] Pass

### UAT-INT-003: GET /kg/audit/{session_id} returns 404 for nonexistent session

- **Test**: `tests/test_kg_router.py::test_kg_audit_returns_404_for_missing_session`
- **Description**: Call GET /kg/audit/{session_id} with a session_id that has no entries in the audit_log table. Verify the response is 404 with detail message indicating session not found.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_returns_404_for_missing_session -v
  ```
- **Expected Result**: Test passes (`PASSED`). Response status is 404. `response.json()["detail"]` contains "not found" (case-insensitive).
- [x] Pass

### UAT-INT-004: GET /kg/audit/{session_id} requires JWT authentication (401 without auth)

- **Test**: `tests/test_kg_router.py::test_kg_audit_requires_auth`
- **Description**: Call GET /kg/audit/{session_id} without a valid JWT (by clearing the auth override). Verify the response is 401 Unauthorized.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_requires_auth -v
  ```
- **Expected Result**: Test passes (`PASSED`). Response status is 401. Auth is enforced.
- [x] Pass

### UAT-INT-005: Filters correctly: includes "kg_" and "retrieval_" events, excludes all others

- **Test**: `tests/test_kg_router.py::test_kg_audit_filters_kg_and_retrieval_only`
- **Description**: Insert a session with mixed event types: "kg_recommend", "kg_explainability", "retrieval_lookup_member", "router_select_tool", "chat_message", "workout_log_entry". Call GET /kg/audit/{session_id}. Verify only the KG and retrieval events are returned.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_filters_kg_and_retrieval_only -v
  ```
- **Expected Result**: Test passes (`PASSED`). Returned entries have events: "kg_recommend", "kg_explainability", "retrieval_lookup_member". Entries with events "router_select_tool", "chat_message", "workout_log_entry" are NOT in the response.
- [ ] Pass

### UAT-INT-006: Audit entries include optional fields when present (latency_ms, tokens_in, tokens_out, node_name, source_type, source_id)

- **Test**: `tests/test_kg_router.py::test_kg_audit_includes_optional_fields`
- **Description**: Insert a KG audit entry with all optional fields populated: latency_ms, tokens_in, tokens_out, node_name, source_type, source_id, extra JSON. Call GET /kg/audit/{session_id}. Verify the response entry includes all these fields.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_includes_optional_fields -v
  ```
- **Expected Result**: Test passes (`PASSED`). Returned entry contains: event, session_id, created_at, latency_ms, tokens_in, tokens_out, node_name, source_type, source_id. Extra fields from the `extra` JSON column are merged into the response dict.
- [ ] Pass

### UAT-INT-007: Entries are ordered by created_at (oldest first)

- **Test**: `tests/test_kg_router.py::test_kg_audit_orders_by_created_at`
- **Description**: Insert multiple KG entries with different timestamps. Call GET /kg/audit/{session_id}. Verify entries in response are ordered chronologically (oldest first).
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_orders_by_created_at -v
  ```
- **Expected Result**: Test passes (`PASSED`). Entries in `audit_log` are sorted by `created_at` timestamp in ascending order.
- [ ] Pass

### UAT-INT-008: total_entries field equals the count of returned audit_log entries

- **Test**: `tests/test_kg_router.py::test_kg_audit_total_entries_matches_count`
- **Description**: Call GET /kg/audit/{session_id} with a session containing a known number of KG entries. Verify `response.total_entries == len(response.audit_log)`.
- **Steps**:
  1. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_total_entries_matches_count -v
  ```
- **Expected Result**: Test passes (`PASSED`). `total_entries` field equals the length of the `audit_log` list.
- [ ] Pass

---

## Full Test Suite

### UAT-SUITE-001: All KG router tests pass without regression

- **Test file**: `tests/test_kg_router.py`
- **Description**: Run the entire KG router test file to confirm no existing tests regressed after the audit endpoint was added.
- **Steps**:
  1. Run the command below from the `backend/` directory
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py -v
  ```
- **Expected Result**: All tests in the file pass (`PASSED`). No failures or errors. This includes all existing tests (kg_recommend, kg_explain, kg_feedback) plus new /kg/audit tests.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Session with only non-KG entries returns 404

- **Description**: Insert audit entries for a session that only contain non-KG events (e.g., "chat_message", "router_select_tool"). Call GET /kg/audit/{session_id}. Should return 404 since no KG entries exist, even though the session exists.
- **Steps**:
  1. This is verified by the filtering logic — if kg_entries list is empty after filtering, endpoint should return 404
  2. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_returns_404_when_no_kg_entries -v
  ```
- **Expected Result**: Test passes (`PASSED`). Response status is 404 with detail message indicating session not found (or no KG entries).
- [ ] Pass

### UAT-EDGE-002: Empty audit_log for non-existent session still respects auth

- **Description**: Call GET /kg/audit/{session_id} without auth. Should return 401 before attempting to query the database. Call with invalid auth. Should also return 401.
- **Steps**:
  1. Covered by existing `test_kg_audit_requires_auth` test
  2. Run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_audit_requires_auth -v
  ```
- **Expected Result**: Test passes (`PASSED`). Auth check happens before database query. 401 returned for missing/invalid auth.
- [x] Pass

---

## Manual Verification

### Manual-001: Endpoint is registered and accessible

- **Description**: Start the backend server and verify the endpoint exists in the OpenAPI docs and is callable.
- **Steps**:
  1. Start the backend server: `cd backend && uvicorn app.main:app --reload`
  2. Navigate to http://localhost:8000/docs
  3. Look for GET /kg/audit/{session_id} endpoint under the /kg section
  4. Try to call the endpoint with a valid JWT and session_id (will return 404 if no entries, which is expected)
- **Expected Result**: Endpoint appears in OpenAPI docs. Has correct path, method (GET), and response schema. Can be called when authenticated.
- [ ] Pass

### Manual-002: Response JSON matches OpenAPI schema

- **Description**: Call the endpoint and inspect the response JSON structure.
- **Steps**:
  1. With server running, use curl or Postman to call: `GET http://localhost:8000/kg/audit/{valid-session-id}` with Authorization header
  2. Verify response has `session_id`, `audit_log`, `total_entries`
  3. Verify each entry in `audit_log` is a dict with `event` and `created_at` at minimum
- **Expected Result**: Response JSON has the correct structure. Can be used by frontend clients.
- [ ] Pass
