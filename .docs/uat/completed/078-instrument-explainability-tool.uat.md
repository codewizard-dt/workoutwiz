# UAT: Instrument Explainability Tool

> **Source task**: [`.docs/tasks/078-instrument-explainability-tool.md`](../tasks/078-instrument-explainability-tool.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server is running (`cd backend && uvicorn app.main:app --reload`)
- [ ] Python/pytest environment available in `backend/` (`pip install -e ".[dev]"`)
- [ ] `$UAT_AUTH_TOKEN` env var set (register + login via `/auth/register` and `/auth/jwt/login`) or use the curl commands in UAT-API-001 to obtain one

---

## Unit Tests (pytest)

These tests verify the core instrumentation logic in `backend/app/kg/explainability.py` directly — no live Neo4j connection required (driver is mocked).

### UAT-UNIT-001: Audit entry fields populated on contraindication path

- **Description**: After calling `explain_skipped_exercise()` with a mocked Neo4j driver that returns a contraindicated exercise record, the returned `audit_entry` must contain all required observability fields with correct values.
- **Steps**:
  1. From `backend/`, run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py::test_explain_audit_entry_populated -v
  ```
- **Expected Result**: Test passes (`PASSED`). The test asserts `audit_entry["event"] == "kg_explainability"`, `audit_entry["query_count"] == 1`, `audit_entry["result_count"] == 1`, `audit_entry["path_depth"] == 2`, `audit_entry["reason_type"] == "contraindication"`, `audit_entry["user_id"] == "member-audit"`, `isinstance(audit_entry["latency_ms"], int)`, and `0.0 < audit_entry["confidence"] <= 1.0`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-002: Audit entry populated when no contraindication found

- **Description**: When the mocked driver returns no record (no contraindication path), the audit entry must still be present with `reason_type="unknown"` and `result_count=0`.
- **Steps**:
  1. From `backend/`, run the command below
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py::test_explain_audit_entry_no_contraindication -v
  ```
- **Expected Result**: Test passes (`PASSED`). The test asserts `audit_entry["event"] == "kg_explainability"`, `audit_entry["query_count"] == 1`, `audit_entry["result_count"] == 0`, `audit_entry["reason_type"] == "unknown"`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-003: Timing instrumentation is present (latency_ms is non-negative int)

- **Description**: The function wraps the Neo4j query with `time.monotonic()` — `latency_ms` must be a non-negative integer in the audit entry for both the contraindication and no-record paths.
- **Steps**:
  1. From `backend/`, run both targeted tests
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py -k "audit_entry" -v
  ```
- **Expected Result**: Both `test_explain_audit_entry_populated` and `test_explain_audit_entry_no_contraindication` pass. Each asserts `isinstance(audit_entry["latency_ms"], int)` and `audit_entry["latency_ms"] >= 0`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-UNIT-004: Full explainability test suite passes

- **Description**: All tests in `test_explainability.py` pass, including happy-path explanation text, fallback text, confidence scoring, and audit entry population.
- **Steps**:
  1. From `backend/`, run the full test module
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py -v
  ```
- **Expected Result**: All 10 tests pass with `10 passed` in the summary. No failures or errors.
- [x] Pass <!-- 2026-06-06 -->

---

## API Tests

### UAT-API-001: Obtain auth token (prerequisite for API tests)

- **Description**: Register and log in to obtain a JWT Bearer token for subsequent authenticated API calls.
- **Steps**:
  1. Register a test user (may already exist — 400 on duplicate is fine)
  2. Run the login command below and capture the `access_token` value
  3. Export: `export UAT_AUTH_TOKEN=<access_token from response>`
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=uat-test-078@example.com&password=UATpass123!'
  ```
- **Expected Result**: `200 OK` with `{"access_token": "<jwt>", "token_type": "bearer"}`. Copy the `access_token` value and export as `UAT_AUTH_TOKEN`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: POST /kg/explain — returns explanation, confidence, and exercise_id

Auth-Required: true
Auth-Role: user

- **Endpoint**: `POST /kg/explain`
- **Description**: Verify the endpoint returns a 200 response with `exercise_id`, `explanation` string, and `confidence` float. The audit entry is captured internally (logged at DEBUG level); the response shape is `KGExplainResponse`.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set from UAT-API-001
  2. Run the curl command below as-is (exercise_id and member_id are arbitrary UUIDs — Neo4j will return no contraindication record for them, producing the fallback explanation)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"00000000-0000-0000-0000-000000000001","exercise_id":"00000000-0000-0000-0000-000000000002"}'
  ```
- **Expected Result**: `200 OK` with JSON body containing `{"exercise_id": "00000000-0000-0000-0000-000000000002", "explanation": "<non-empty string>", "confidence": <float between 0.0 and 1.0 inclusive>}`. The `explanation` field will be `"This exercise was not included due to insufficient context."` when no contraindication record exists.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: POST /kg/explain — 401 when no token provided

- **Endpoint**: `POST /kg/explain`
- **Description**: Verify the endpoint rejects unauthenticated requests with 401.
- **Steps**:
  1. Run the curl command below (no Authorization header)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -d '{"member_id":"00000000-0000-0000-0000-000000000001","exercise_id":"00000000-0000-0000-0000-000000000002"}'
  ```
- **Expected Result**: `401 Unauthorized` response.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: explain_skipped_exercise() return tuple includes audit_entry with all required fields

- **Description**: Verify end-to-end that calling `explain_skipped_exercise()` returns the full 3-tuple `(explanation: str, audit_entry: dict, confidence: float)` and that `audit_entry` contains the six required observability fields: `event`, `latency_ms`, `query_count`, `result_count`, `path_depth`, `reason_type`.
- **Steps**:
  1. Run the full KG router unit test suite which exercises the mocked integration
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py tests/kg/test_explainability.py -v
  ```
- **Expected Result**: All tests pass. `test_kg_explain_returns_explanation` verifies the router correctly unpacks the 3-tuple and returns `exercise_id`, `explanation`, and `confidence` in the HTTP response. `test_explain_audit_entry_populated` verifies all six audit fields are present.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: No contraindication path — fallback explanation and zero confidence

- **Description**: When no `(Member)-[:HAS_INJURY]->(Injury)<-[:CONTRAINDICATED_BY]-(Exercise)` path exists in the KG, the function must return a fallback explanation, `reason_type="unknown"`, `result_count=0`, and `confidence=0.0`.
- **Steps**:
  1. Run the targeted test
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py::test_explain_returns_fallback_when_no_contraindication tests/kg/test_explainability.py::test_confidence_is_zero_when_no_path -v
  ```
- **Expected Result**: Both tests pass. `test_explain_returns_fallback_when_no_contraindication` asserts explanation contains `"insufficient context"`. `test_confidence_is_zero_when_no_path` asserts `confidence == 0.0`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-EDGE-002: Multiple injuries — confidence scales with result_count

- **Description**: The confidence score formula is `depth_score + coverage_score` where `depth_score = path_depth / MAX_PATH_DEPTH = 2/4 = 0.5` and `coverage_score = min(result_count, 4) / 4 * 0.5`. With 1 injury this should be 0.625; with multiple injuries it should be higher (saturating at 1.0 for 4+ injuries).
- **Steps**:
  1. Run the confidence scaling tests
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py::test_confidence_in_valid_range_single_injury tests/kg/test_explainability.py::test_confidence_increases_with_more_corroborating_paths -v
  ```
- **Expected Result**: Both tests pass. Single injury: `confidence == 0.625`. Multiple injuries: `confidence_multi > confidence_one`.
- [x] Pass <!-- 2026-06-06 -->
