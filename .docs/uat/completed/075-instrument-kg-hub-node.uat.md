# UAT: Instrument KG Hub Node Routing Trace

> **Source task**: [`.docs/tasks/075-instrument-kg-hub-node.md`](../tasks/075-instrument-kg-hub-node.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server is NOT required for unit-level tests (UAT-UNIT-001 through UAT-UNIT-003 use `pytest` directly)
- [ ] Backend server running at `http://localhost:8000` for API tests (UAT-API-001, UAT-API-002)
- [ ] Python virtual environment activated (`cd backend && source .venv/bin/activate` or equivalent)
- [ ] For API tests: `$UAT_AUTH_TOKEN` must be set — obtain by running:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"uat-075@example.com","password":"UatPass123!"}' && curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -d 'username=uat-075@example.com&password=UatPass123!'
  ```
  Then export: `export UAT_AUTH_TOKEN=<access_token from login response>`

---

## Unit Tests (pytest — no server required)

### UAT-UNIT-001: `test_kg_hub_node_audit_entry` passes
- **Description**: Verify the existing unit test for `_knowledge_graph_node` audit instrumentation passes, confirming the `kg_hub` entry is appended with all required fields.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_agents_hub.py::test_kg_hub_node_audit_entry -v
  ```
- **Expected Result**: Test passes (`PASSED tests/test_agents_hub.py::test_kg_hub_node_audit_entry`). No assertion errors.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: Audit entry contains all required fields
- **Description**: Verify `_knowledge_graph_node` appends an audit entry with `event="kg_hub"`, `intent="KNOWLEDGE_GRAPH"`, non-negative `latency_ms`, `user_id`, numeric `tokens_in`/`tokens_out`, and `provider="neo4j"`.
- **Steps**:
  1. Run the full hub test suite to confirm all hub tests pass, including the audit entry assertions
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_agents_hub.py -v
  ```
- **Expected Result**: All tests in `test_agents_hub.py` pass. Specifically `test_kg_hub_node_audit_entry` asserts:
  - `kg_entry["event"] == "kg_hub"`
  - `kg_entry["intent"] == "KNOWLEDGE_GRAPH"`
  - `kg_entry["latency_ms"] >= 0`
  - `kg_entry["user_id"] == "user-123"`
  - `kg_entry["tokens_in"] == 5`
  - `kg_entry["tokens_out"] == 3`
  - `kg_entry["provider"] == "neo4j"`
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: `audit_log` is correctly returned from the KG node
- **Description**: Verify that the returned state dict from `_knowledge_graph_node` includes the full `audit_log` (prior entries plus the new `kg_hub` entry), not just the new entry alone.
- **Steps**:
  1. Run the pytest command below — the test pre-seeds the state with a `router` entry and checks the new `kg_hub` entry appears alongside it
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_agents_hub.py::test_kg_hub_node_audit_entry -v -s
  ```
- **Expected Result**: Test passes. The `result["audit_log"]` contains at least 2 entries: the pre-existing `router` entry from the seed state and the new `kg_hub` entry appended by the node.
- [x] Pass <!-- 2026-06-06 -->

---

## API Tests

### UAT-API-001: Chat endpoint returns `kg_hub` audit entry for KG-intent messages

Auth-Required: true
Auth-Role: user

- **Endpoint**: `POST /chat/`
- **Description**: Send a message that triggers KNOWLEDGE_GRAPH routing via the hub and verify the response's `audit_log` contains a `kg_hub` entry with required fields (`event`, `intent`, `latency_ms`, `provider`).
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below — the message is designed to trigger KNOWLEDGE_GRAPH intent routing
  3. Inspect the `audit_log` array in the response for a `kg_hub` entry
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"recommend me a knowledge graph workout based on my history"}' | jq '[.audit_log[] | select(.event == "kg_hub")]'
  ```
- **Expected Result**: Response is `200 OK`. The `jq` output is a non-empty array containing at least one object with:
  - `"event": "kg_hub"`
  - `"intent": "KNOWLEDGE_GRAPH"`
  - `"latency_ms"` present and a non-negative integer
  - `"provider": "neo4j"`
  - `"user_id"` present (string, the authenticated user's ID)

  > **Note**: This test requires Neo4j to be running and accessible. If Neo4j is unavailable, the `_knowledge_graph_node` exception path runs and still appends the `kg_hub` entry with `latency_ms >= 0` and `tokens_in/tokens_out == 0`. The audit entry must be present in either case.
- [FAIL: auto-judge: /chat/ endpoint returned HTTP 500 — server implementation may require restart after code changes] <!-- 2026-06-06 -->

### UAT-API-002: Audit log audit entry includes `latency_ms > 0` for successful KG call

Auth-Required: true
Auth-Role: user

- **Endpoint**: `POST /chat/`
- **Description**: For a successful KG invocation, verify `latency_ms` in the `kg_hub` entry is strictly greater than 0, confirming timing instrumentation fired correctly.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set and a valid session from UAT-API-001 exists
  2. Run the curl command below using the `session_id` returned from UAT-API-001 (substitute `<session-id-from-UAT-API-001>`)
  3. Inspect `latency_ms` on the `kg_hub` entry
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"suggest a knowledge graph workout","session_id":"<session-id-from-UAT-API-001>"}' | jq '.audit_log[] | select(.event == "kg_hub") | .latency_ms'
  ```
- **Expected Result**: `200 OK`. The `jq` output is an integer greater than `0`, confirming the timing instrumentation captured real elapsed time.
- [FAIL: auto-judge: /chat/ endpoint prerequisite failed (depends on UAT-API-001)] <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: KG hub audit entry is present even when Neo4j is unavailable
- **Scenario**: `_knowledge_graph_node` raises an exception (e.g. Neo4j not reachable); the `except` block still computes `latency_ms` and appends the `kg_hub` entry.
- **Steps**:
  1. Run the unit test suite — `test_kg_hub_node_audit_entry` exercises the success path. For the error path, run the command below against the full hub test file which includes exception coverage.
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_agents_hub.py -v -k "kg"
  ```
- **Expected Result**: All KG-related hub tests pass. The instrumentation code structure guarantees `latency_ms = int((time.monotonic() - t0) * 1000)` runs in the `except` block (line 154 of `backend/app/agents/hub.py`), so the `kg_hub` entry is always appended.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: `tokens_in` and `tokens_out` default to `0` when not provided by generation graph
- **Scenario**: If the generation graph result does not include `tokens_in`/`tokens_out` keys, the hub node defaults both to `0` (via `.get("tokens_in", 0)`).
- **Steps**:
  1. The unit test in `test_kg_hub_node_audit_entry` explicitly sets `tokens_in=5, tokens_out=3` in the mock result. Verify the test assertion correctly reflects these values (not the defaults).
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_agents_hub.py::test_kg_hub_node_audit_entry -v -s 2>&1 | grep -E "PASSED|FAILED|tokens"
  ```
- **Expected Result**: Test passes, confirming `tokens_in` and `tokens_out` are extracted from the generation result when present. The code on line 151-152 of hub.py handles the `.get(..., 0)` default correctly.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Full audit log chain: `router` entry followed by `kg_hub` entry

Auth-Required: true
Auth-Role: user

- **Components**: Hub router node → `_knowledge_graph_node` → `audit_log` in `ChatResponse`
- **Flow**: A single `/chat/` call with KNOWLEDGE_GRAPH intent produces an `audit_log` containing two entries in order: first a `router` entry (from `_router_node`) and then a `kg_hub` entry (from `_knowledge_graph_node`).
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Run the curl command below
  3. Verify both entries are present and in the correct order
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/chat/' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"message":"build me a knowledge graph based workout recommendation"}' | jq '[.audit_log[] | {event: .event, intent: .intent, latency_ms: .latency_ms}]'
  ```
- **Expected Result**: `200 OK`. The `jq` output is an array where:
  - First entry has `"event": "router"` (no `intent` field, but has `route` and `confidence` fields)
  - Last entry has `"event": "kg_hub"` with `"intent": "KNOWLEDGE_GRAPH"` and a non-negative `"latency_ms"`
  - Order is preserved: router entry precedes kg_hub entry in the array
- [FAIL: auto-judge: /chat/ endpoint prerequisite failed — server implementation requires restart] <!-- 2026-06-06 -->
