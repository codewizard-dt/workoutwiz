# UAT: KG FastAPI Router — /kg/recommend, /kg/explain, /kg/feedback

> **Source task**: [`.docs/tasks/completed/065-kg-fastapi-router.md`](../tasks/completed/065-kg-fastapi-router.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running on port 8000: `cd backend && uvicorn app.main:app --port 8000`
- [ ] Neo4j running and accessible (bolt://localhost:7687)
- [ ] `UAT_AUTH_TOKEN` env var set — obtain via:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/register' -H 'Content-Type: application/json' -d '{"email":"uat-kg-test@example.com","password":"S3cur3Pass!"}' > /dev/null; curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -d 'username=uat-kg-test@example.com&password=S3cur3Pass!' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  ```
- [ ] A seeded Neo4j graph with at least one Member node (run `python -m app.knowledge_graph.seed` if needed; a non-existent member_id is also valid — endpoints must not 500 on missing members)

---

## API Tests

### UAT-API-001: POST /kg/recommend — happy path returns 200 with response shape
- **Endpoint**: `POST /kg/recommend`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify the recommend endpoint invokes the retrieval+generation pipeline and returns a `KGRecommendResponse` with all required fields.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set (see Prerequisites).
  2. Run the curl command below. Because Neo4j may not have this member, the generation graph may trigger its fallback path — that is acceptable; the response shape must still be correct.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","query":"upper body strength workout"}' | jq '{member_id,overall_reasoning,fallback_used,exercise_count:.exercises|length,skipped_count:.skipped_exercise_ids|length}'
  ```
- **Expected Result**: `200 OK`. JSON object containing keys `member_id`, `exercises` (array), `overall_reasoning` (string), `skipped_exercise_ids` (array), `fallback_used` (boolean). `member_id` equals `"test-member-001"`.
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; server returned HTTP 500 "Couldn't connect to localhost:7687"] <!-- 2026-06-06 -->

### UAT-API-002: POST /kg/recommend — unauthenticated request returns 401
- **Endpoint**: `POST /kg/recommend`
- Auth-Required: false
- **Description**: Verify the endpoint rejects requests without a Bearer token.
- **Steps**:
  1. Run the curl command below (no Authorization header).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -d '{"member_id":"test-member-001","query":"legs"}' | jq '{status_hint:.detail}'
  ```
- **Expected Result**: `401 Unauthorized`. Response body contains `"detail"` field.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-003: POST /kg/recommend — missing required fields returns 422
- **Endpoint**: `POST /kg/recommend`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify Pydantic validation rejects a body missing the required `query` field.
- **Steps**:
  1. Run the curl command below — body omits the `query` field.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001"}' | jq '.detail[0].loc'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Response `detail` array includes a validation error locating `query` as the missing field.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-004: POST /kg/explain — happy path returns explanation string
- **Endpoint**: `POST /kg/explain`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify explain endpoint returns a `KGExplainResponse` with `exercise_id` echoed back and a non-empty `explanation` string.
- **Steps**:
  1. Run the curl command below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","exercise_id":"exercise-abc-123"}' | jq '{exercise_id,explanation}'
  ```
- **Expected Result**: `200 OK`. JSON with `exercise_id` equal to `"exercise-abc-123"` and `explanation` as a non-empty string (e.g. "This exercise was not included due to insufficient context." when no injury data exists).
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; endpoint would return 500] <!-- 2026-06-06 -->

### UAT-API-005: POST /kg/explain — unauthenticated returns 401
- **Endpoint**: `POST /kg/explain`
- Auth-Required: false
- **Description**: Verify the endpoint rejects unauthenticated requests.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -d '{"member_id":"test-member-001","exercise_id":"exercise-abc-123"}' | jq '.detail'
  ```
- **Expected Result**: `401 Unauthorized`.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-006: POST /kg/feedback — happy path returns feedback_id
- **Endpoint**: `POST /kg/feedback`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify feedback endpoint persists to Neo4j and returns a `KGFeedbackResponse` with a UUID `feedback_id` and a `message` string.
- **Steps**:
  1. Run the curl command below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","exercise_id":"exercise-abc-123","rating":4,"text":"Felt great","context_type":"post_workout"}' | jq '{feedback_id,message}'
  ```
- **Expected Result**: `200 OK`. JSON with `feedback_id` as a non-empty UUID string and `message` as a non-empty string (e.g. `"Feedback recorded successfully"`).
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; endpoint would return 500] <!-- 2026-06-06 -->

### UAT-API-007: POST /kg/feedback — rating out of range returns 422
- **Endpoint**: `POST /kg/feedback`
- Auth-Required: true
- Auth-Role: user
- **Description**: Verify Pydantic validation rejects a `rating` outside the 1–5 range (defined in `FeedbackPayload.rating` with `ge=1, le=5`).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","exercise_id":"exercise-abc-123","rating":10}' | jq '.detail[0].loc'
  ```
- **Expected Result**: `422 Unprocessable Entity`. Validation error referencing the `rating` field.
- [x] Pass <!-- 2026-06-06 -->

### UAT-API-008: POST /kg/feedback — unauthenticated returns 401
- **Endpoint**: `POST /kg/feedback`
- Auth-Required: false
- **Description**: Verify the endpoint rejects unauthenticated requests.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -d '{"member_id":"test-member-001","exercise_id":"exercise-abc-123","rating":3}' | jq '.detail'
  ```
- **Expected Result**: `401 Unauthorized`.
- [x] Pass <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: /kg/recommend — member_id defaults to authenticated user id when omitted
- **Scenario**: The `member_id` field in `KGRecommendRequest` is required by the schema — but the router falls back to `str(user.id)` when a value is provided. Verify the response `member_id` echoes back the value sent.
- Auth-Required: true
- Auth-Role: user
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"explicit-member-999","query":"core stability"}' | jq '.member_id'
  ```
- **Expected Result**: `200 OK`. `member_id` in response is `"explicit-member-999"` (the value from the request body, not the auth user's id).
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; endpoint would return 500] <!-- 2026-06-06 -->

### UAT-EDGE-002: /kg/explain — no injury data returns graceful explanation string
- **Scenario**: When Neo4j has no injury-exercise contraindication data for the given member/exercise pair, `explain_skipped_exercise` returns `"This exercise was not included due to insufficient context."` — not a 500.
- Auth-Required: true
- Auth-Role: user
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"nonexistent-member","exercise_id":"nonexistent-exercise"}' | jq '{status_check: (.explanation // "MISSING"), exercise_id}'
  ```
- **Expected Result**: `200 OK`. `explanation` is `"This exercise was not included due to insufficient context."` (the graceful fallback from `explainability.py`).
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; endpoint would return 500] <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Full recommend → explain flow
- **Components**: `POST /kg/recommend` → `POST /kg/explain`
- **Flow**: Call recommend to get a list of exercises (and skipped IDs if any), then call explain for one of the skipped or included exercise IDs.
- Auth-Required: true
- Auth-Role: user
- **Steps**:
  1. Call `POST /kg/recommend` and capture the response.
  2. Note any `exercise_id` from the `exercises` array (or use a known exercise UUID).
  3. Call `POST /kg/explain` for that exercise_id.
- **Command** (step 1 — recommend):
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","query":"lower body"}' | jq '{member_id, exercise_count: (.exercises|length), first_exercise_id: .exercises[0].exercise_id}'
  ```
- **Command** (step 2 — explain using a known exercise id):
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/explain' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"test-member-001","exercise_id":"<exercise_id-from-step-1-or-any-uuid>"}' | jq '{exercise_id, explanation}'
  ```
- **Expected Result**: Both calls return `200 OK`. The explain call returns a non-empty `explanation` string. No 500 errors in either call.
- [FAIL: auto-judge: prerequisite not satisfied — Neo4j not running; integration flow requires live graph] <!-- 2026-06-06 -->
