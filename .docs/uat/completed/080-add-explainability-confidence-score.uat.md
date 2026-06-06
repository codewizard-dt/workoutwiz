# UAT: Add Explainability Confidence Score

> **Source task**: [`.docs/tasks/080-add-explainability-confidence-score.md`](../tasks/080-add-explainability-confidence-score.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running (`cd backend && uvicorn app.main:app --reload`)
- [ ] A registered user exists; obtain a JWT by POSTing to `POST /auth/jwt/login` with `username=<email>&password=<password>` (form-encoded). Set `UAT_AUTH_TOKEN` in your shell.
- [ ] Neo4j is running and reachable at the configured URI (or mock is in place). The `/kg/explain` endpoint calls it live; for a quick smoke-test, any exercise_id + member_id that yields no contraindication will exercise the zero-confidence path.

---

## API Tests

### UAT-API-001: `/kg/explain` response includes `confidence` field
- **Endpoint**: `POST /kg/explain`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the explain endpoint returns a `confidence` float in its response body (the field must be present and be a number between 0.0 and 1.0 inclusive).
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set in your shell.
  2. Run the curl command below. Use any valid UUID-shaped strings for member_id and exercise_id — if no contraindication path exists in Neo4j, the API should still return `confidence: 0.0`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"member-123","exercise_id":"exercise-abc"}' | jq '{exercise_id, explanation, confidence}'
  ```
- **Expected Result**: `200 OK` with a JSON body containing:
  - `"exercise_id"`: the string `"exercise-abc"`
  - `"explanation"`: a non-empty string
  - `"confidence"`: a number in `[0.0, 1.0]`
  
  Example for no-contraindication path:
  ```json
  {
    "exercise_id": "exercise-abc",
    "explanation": "This exercise was not included due to insufficient context.",
    "confidence": 0.0
  }
  ```
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-002: `/kg/explain` confidence is 0.0 when no contraindication path exists
- **Endpoint**: `POST /kg/explain`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: When the Neo4j query finds no `(Member)-[:HAS_INJURY]->(Injury)<-[:CONTRAINDICATED_BY]-(Exercise)` path, `confidence` must be exactly `0.0`.
- **Steps**:
  1. Use a `member_id` and `exercise_id` combination that has no contraindication recorded in Neo4j (any nonexistent IDs will produce this path).
  2. Run the command below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"no-injury-member","exercise_id":"safe-exercise-999"}' | jq '.confidence'
  ```
- **Expected Result**: Output is `0` (JSON number 0.0). The response body must not omit the field.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: `/kg/explain` confidence is in range (0, 1] when a contraindication is found
- **Endpoint**: `POST /kg/explain`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: When a contraindication path exists (member has an injury that contraindicates the exercise), `confidence` must be a positive float no greater than 1.0.
- **Steps**:
  1. Use a `member_id` that has at least one injury linked to a contraindicated exercise in Neo4j. If none exists in the live database, this test can be validated via the unit test `test_confidence_in_valid_range_single_injury` in `backend/tests/kg/test_explainability.py` (see Integration test UAT-INT-001 below).
  2. Substitute real Neo4j member/exercise IDs below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-id-with-injury>","exercise_id":"<contraindicated-exercise-id>"}' | jq '.confidence'
  ```
- **Expected Result**: A JSON number strictly greater than `0` and less than or equal to `1`. For 1 injury, the algorithm yields `0.625`; for 2 injuries `0.75`; for 3 injuries `0.875`; for 4+ injuries `1.0`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: `/kg/explain` returns 401 when called without a token
- **Endpoint**: `POST /kg/explain`
- **Auth-Required**: false
- **Description**: Verify the endpoint is auth-gated — unauthenticated requests must be rejected.
- **Steps**:
  1. Send the request with no `Authorization` header.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -d '{"member_id":"member-123","exercise_id":"exercise-abc"}' | jq '.'
  ```
- **Expected Result**: HTTP `401 Unauthorized`. Response body shape: `{"detail": "Unauthorized"}` or similar fastapi-users auth error.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Unit test suite confirms confidence scoring logic end-to-end
- **Components**: `explain_skipped_exercise()` in `backend/app/kg/explainability.py`, test suite in `backend/tests/kg/test_explainability.py`
- **Description**: Run the confidence-scoring unit tests directly. These cover: zero confidence for no path, valid-range confidence for a single contraindication, and increasing confidence for multiple corroborating paths.
- **Steps**:
  1. From the `backend/` directory, run pytest targeting the confidence tests.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py::test_confidence_is_zero_when_no_path tests/kg/test_explainability.py::test_confidence_in_valid_range_single_injury tests/kg/test_explainability.py::test_confidence_increases_with_more_corroborating_paths -v 2>&1 | tail -20
  ```
- **Expected Result**: All three tests pass (`PASSED`). No failures or errors.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-002: Router-level test confirms `confidence` is present in HTTP response
- **Components**: `kg_explain` handler in `backend/app/routers/kg.py`, `KGExplainResponse` schema, `explain_skipped_exercise()` function
- **Description**: Run the router-level test that mocks `explain_skipped_exercise` and asserts the HTTP response includes a `confidence` float.
- **Steps**:
  1. From the `backend/` directory, run pytest targeting the router explain test.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/test_kg_router.py::test_kg_explain_returns_explanation -v 2>&1 | tail -10
  ```
- **Expected Result**: Test passes (`PASSED`). The test asserts `"confidence" in data` and `isinstance(data["confidence"], float)`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-INT-003: Full confidence test suite passes (no regressions)
- **Components**: All tests in `backend/tests/kg/test_explainability.py`
- **Description**: Run the entire explainability test module to verify no regressions and all confidence tests pass alongside existing explanation tests.
- **Steps**:
  1. From the `backend/` directory, run the full explainability test module.
- **Command**:
  ```bash
  cd /Users/davidtaylor/Repositories/gauntlet/workout-wiz/backend && python -m pytest tests/kg/test_explainability.py -v 2>&1 | tail -20
  ```
- **Expected Result**: All 10 tests pass. No failures. Final line reads something like `10 passed`.
- [x] Pass <!-- 2026-06-06 -->
