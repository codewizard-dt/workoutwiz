# UAT: Accountability Engine Tests

> **Source task**: [`.docs/tasks/completed/108-accountability-engine-tests.md`](../tasks/completed/108-accountability-engine-tests.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Stack is running (`make up` or `docker compose up`) and serving at `http://localhost:3000`
- [ ] `$UAT_AUTH_TOKEN` is set (obtain via `POST /api/auth/jwt/login` with `alex@example.com` / `password123`)
- [ ] Neo4j KG seeded with Jordan Rivera's member context (confirmed via `GET /api/coach/brief`)
- [ ] `backend/.venv` exists and is activated (`cd backend && source .venv/bin/activate`)
- [ ] `@playwright/test` installed in `frontend/` (`cd frontend && npm install`)
- [ ] Playwright browsers installed (`cd frontend && npx playwright install`)

---

## API Tests

### UAT-API-001: Get coach morning brief for demo member
- **Endpoint**: `GET /api/coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm the demo member (Jordan Rivera) brief loads successfully and contains the expected fields including adherence weeks and churn risk.
- **Steps**:
  1. Send an authenticated GET request to `/api/coach/brief`.
  2. Verify HTTP 200 is returned.
  3. Verify the response body contains `member_id`, `member_name`, `adherence_weeks`, and `churn_risk`.
  4. Verify `churn_risk.level` is one of `"high"`, `"medium"`, `"low"`, or `"unknown"`.
- **Command**:
  ```bash
  curl -sS -H "Authorization: Bearer $UAT_AUTH_TOKEN" http://localhost:3000/api/coach/brief
  ```
- **Expected Result**: HTTP 200; JSON body includes `"member_name": "Jordan Rivera"`, non-empty `adherence_weeks` array, and `churn_risk` object with a `level` field.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-002: Get coach brief with explicit member_id query parameter
- **Endpoint**: `GET /api/coach/brief?member_id={member_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that passing `member_id` explicitly returns the same member's brief as without the parameter.
- **Steps**:
  1. Obtain Jordan Rivera's `member_id` from the response of UAT-API-001.
  2. Send an authenticated GET request to `/api/coach/brief?member_id={member_id}`.
  3. Verify HTTP 200 and matching `member_name`.
- **Command**:
  ```bash
  curl -sS -H "Authorization: Bearer $UAT_AUTH_TOKEN" "http://localhost:3000/api/coach/brief?member_id=JORDAN_MEMBER_ID"
  ```
- **Expected Result**: HTTP 200; `member_name` is `"Jordan Rivera"`; response fields match UAT-API-001 output.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-003: Get coach brief unauthenticated returns 401
- **Endpoint**: `GET /api/coach/brief`
- **Auth-Required**: false
- **Description**: Confirm the brief endpoint rejects unauthenticated requests.
- **Steps**:
  1. Send a GET request with no Authorization header.
  2. Verify HTTP 401 is returned.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" http://localhost:3000/api/coach/brief
  ```
- **Expected Result**: `401`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-004: List coach members
- **Endpoint**: `GET /api/coach/members`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm the members list returns seeded members including Jordan Rivera.
- **Steps**:
  1. Send an authenticated GET request to `/api/coach/members`.
  2. Verify HTTP 200 and a non-empty array is returned.
  3. Verify Jordan Rivera appears in the list.
- **Command**:
  ```bash
  curl -sS -H "Authorization: Bearer $UAT_AUTH_TOKEN" http://localhost:3000/api/coach/members
  ```
- **Expected Result**: HTTP 200; JSON array containing an object with `"member_name": "Jordan Rivera"`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-005: Post nudge for a flagged member
- **Endpoint**: `POST /api/coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that posting a nudge request for a member with a low-adherence action item returns a draft nudge message and a `draft_id`.
- **Steps**:
  1. Send an authenticated POST request with a valid `NudgeRequest` body containing an `ActionItem` with `priority: "high"`.
  2. Verify HTTP 200 is returned.
  3. Verify `draft_message` is a non-empty string.
  4. Verify `draft_id` is present and non-null.
- **Command**:
  ```bash
  curl -sS -X POST http://localhost:3000/api/coach/nudge \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"member_id":"test-member","member_name":"Test Member","action_item":{"priority":"high","member_id":"test-member","member_name":"Test Member","reason":"Low adherence this week: 40% (week of 2026-06-01)","context":{"week_of":"2026-06-01","adherence_pct":40}}}'
  ```
- **Expected Result**: HTTP 200; JSON body contains non-empty `draft_message` string and non-null `draft_id` UUID.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-006: Create a coach draft
- **Endpoint**: `POST /api/coach/draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that a coach draft can be created and returns 201 with the draft's schema including `status: "draft"`.
- **Steps**:
  1. Send an authenticated POST request with a valid `CreateDraftRequest` body.
  2. Verify HTTP 201 and a `CoachDraftSchema` JSON body.
  3. Note the returned `id` for use in subsequent tests.
- **Command**:
  ```bash
  curl -sS -X POST http://localhost:3000/api/coach/draft \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"member_id":"test-member","member_name":"Test Member","content_type":"nudge","body":"Hey, noticed your workouts dropped — how are you feeling?","grounded_on":["Low adherence: 40%"]}'
  ```
- **Expected Result**: HTTP 201; JSON body contains `"status": "draft"`, non-null `id`, `"member_name": "Test Member"`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-007: List coach drafts
- **Endpoint**: `GET /api/coach/draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm the draft list returns at least one draft (created in UAT-API-006).
- **Steps**:
  1. Send an authenticated GET request to `/api/coach/draft`.
  2. Verify HTTP 200 and a non-empty array.
- **Command**:
  ```bash
  curl -sS -H "Authorization: Bearer $UAT_AUTH_TOKEN" http://localhost:3000/api/coach/draft
  ```
- **Expected Result**: HTTP 200; JSON array with at least one draft object containing `"status": "draft"`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-008: List coach drafts filtered by status
- **Endpoint**: `GET /api/coach/draft?status=draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that filtering drafts by `status=draft` returns only draft-status records.
- **Steps**:
  1. Send an authenticated GET request to `/api/coach/draft?status=draft`.
  2. Verify all returned items have `"status": "draft"`.
- **Command**:
  ```bash
  curl -sS -H "Authorization: Bearer $UAT_AUTH_TOKEN" "http://localhost:3000/api/coach/draft?status=draft"
  ```
- **Expected Result**: HTTP 200; every item in the array has `"status": "draft"`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-009: Approve a coach draft
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that approving a draft transitions its status to `"approved"` and records `approved_by` and `approved_at`.
- **Steps**:
  1. Use the `draft_id` returned from UAT-API-006.
  2. Send a PATCH request with `{"action": "approve"}`.
  3. Verify HTTP 200 and `"status": "approved"`.
  4. Verify `approved_by` and `approved_at` are non-null.
- **Command**:
  ```bash
  curl -sS -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"approve"}'
  ```
- **Expected Result**: HTTP 200; `"status": "approved"`, `approved_by` is non-null, `approved_at` is an ISO timestamp.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-010: Edit a draft body and verify status resets to draft
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that editing an approved draft resets its status back to `"draft"` and clears approval metadata.
- **Steps**:
  1. Use the approved draft from UAT-API-009.
  2. Send a PATCH request with `{"action": "edit", "body": "Updated message text."}`.
  3. Verify HTTP 200 and `"status": "draft"`.
  4. Verify `approved_by` and `approved_at` are null.
- **Command**:
  ```bash
  curl -sS -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"edit","body":"Updated message text."}'
  ```
- **Expected Result**: HTTP 200; `"status": "draft"`, `approved_by` is null, `approved_at` is null, `body` contains updated text.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-011: Send a draft requires prior approval (409)
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that attempting to send a draft that is not yet approved returns HTTP 409.
- **Steps**:
  1. Use the draft from UAT-API-010 (status `"draft"`).
  2. Send a PATCH request with `{"action": "send"}`.
  3. Verify HTTP 409 is returned.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"send"}'
  ```
- **Expected Result**: `409`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-012: Approve then send a draft succeeds
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that approving, then sending a draft transitions its status to `"sent"` with a `sent_at` timestamp.
- **Steps**:
  1. Approve the draft from UAT-API-010 first (re-run approve PATCH).
  2. Then send a PATCH with `{"action": "send"}`.
  3. Verify HTTP 200 and `"status": "sent"` and non-null `sent_at`.
- **Command**:
  ```bash
  curl -sS -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"send"}'
  ```
- **Expected Result**: HTTP 200; `"status": "sent"`, `sent_at` is an ISO timestamp.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-013: Approve a sent draft returns 409
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that attempting to approve a draft that has already been sent returns HTTP 409.
- **Steps**:
  1. Use the sent draft from UAT-API-012.
  2. Send a PATCH with `{"action": "approve"}`.
  3. Verify HTTP 409 is returned.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"approve"}'
  ```
- **Expected Result**: `409`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-014: PATCH unknown draft returns 404
- **Endpoint**: `PATCH /api/coach/draft/{draft_id}`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Confirm that patching a non-existent draft UUID returns 404.
- **Steps**:
  1. Send a PATCH with `{"action": "approve"}` to a random UUID that does not exist.
  2. Verify HTTP 404 is returned.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" -X PATCH "http://localhost:3000/api/coach/draft/00000000-0000-0000-0000-000000000000" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"approve"}'
  ```
- **Expected Result**: `404`
- [x] Pass <!-- 2026-06-11 -->

---

## Pytest Tests

### UAT-PYTEST-001: All 5 unit tests in test_accountability.py pass
- **Description**: Confirm all unit tests for `rank_action_items` pass without any DB or network access.
- **Steps**:
  1. Activate the backend venv.
  2. Run the unit test suite.
  3. Verify all 5 tests pass.
- **Command**:
  ```bash
  cd backend && python -m pytest tests/services/test_accountability.py -v
  ```
- **Expected Result**: 5 tests collected; all PASSED; exit code 0. Tests: `test_high_churn_yields_action_item`, `test_low_adherence_yields_high_priority`, `test_medium_adherence_yields_medium_priority`, `test_healthy_member_yields_empty`, `test_high_churn_plus_low_adherence_sorted_high_first`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-PYTEST-002: Integration test test_low_adherence_member_yields_ranked_action_item passes
- **Description**: Confirm the integration test asserting that a member with adherence at 40% yields a high-priority ranked action item passes.
- **Steps**:
  1. Activate the backend venv.
  2. Run the integration test.
  3. Verify the test passes.
- **Command**:
  ```bash
  cd backend && python -m pytest tests/test_accountability_integration.py -v
  ```
- **Expected Result**: 1 test collected; PASSED; exit code 0. The test asserts `len(items) >= 1`, `items[0].priority == "high"`, and `"40" in items[0].reason`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-PYTEST-003: Both test files pass together with no regressions
- **Description**: Confirm running all 6 accountability tests (5 unit + 1 integration) together produces no failures or regressions.
- **Steps**:
  1. Activate the backend venv.
  2. Run both test files together.
  3. Verify all 6 tests pass.
- **Command**:
  ```bash
  cd backend && python -m pytest tests/services/test_accountability.py tests/test_accountability_integration.py -v
  ```
- **Expected Result**: 6 tests collected; all PASSED; exit code 0.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-PYTEST-004: Full backend pytest suite passes without regressions
- **Description**: Confirm no pre-existing tests regress after adding the accountability test files.
- **Steps**:
  1. Activate the backend venv.
  2. Run the full pytest suite (excluding live LLM tests).
  3. Verify no failures.
- **Command**:
  ```bash
  cd backend && python -m pytest --ignore=tests/test_live_llm.py -v
  ```
- **Expected Result**: All tests pass; exit code 0; no previously passing tests now fail.
- [x] Pass <!-- 2026-06-11 -->

---

## E2E Tests (Playwright)

### UAT-E2E-001: Coach page shows Morning Brief for logged-in user
- **Description**: Confirm that navigating to `/coach` after login loads Jordan Rivera's Morning Brief section.
- **Steps**:
  1. Ensure the stack is running at `http://localhost:3000`.
  2. Run the Playwright test.
  3. Verify the test passes (logs in, navigates to `/coach`, asserts "Jordan Rivera" and "Morning Brief" visible).
- **Command**:
  ```bash
  cd frontend && npx playwright test e2e/coach-action-items.spec.ts --reporter=line
  ```
- **Expected Result**: 1 test passed; the page displays "Jordan Rivera" and "Morning Brief" within the timeout.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-E2E-002: Action Items card is visible when demo member has flagged signals
- **Description**: Confirm that if Jordan Rivera's seeded data includes adherence below 50% or high/medium churn risk, the "Action Items" card heading is visible on the `/coach` page.
- **Steps**:
  1. Run the stack with Neo4j KG seeded.
  2. Log in as `alex@example.com`.
  3. Navigate to `http://localhost:3000/coach`.
  4. Wait for "Jordan Rivera" to appear.
  5. Check whether "Action Items" heading is visible.
- **Command**:
  ```bash
  cd frontend && npx playwright test e2e/coach-action-items.spec.ts --headed --reporter=line
  ```
- **Expected Result**: If Jordan Rivera's seeded churn level is non-`"low"` or latest adherence is below 70%, the "Action Items" heading is visible on the page. The test does not fail if no action items exist — it asserts the brief loaded at minimum.
- [x] Pass <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: rank_action_items with empty adherence list returns no adherence item
- **Description**: Confirm that passing an empty `adherence_weeks` list produces no adherence-related action items (only churn-risk items may appear).
- **Steps**:
  1. Run a quick Python snippet against the installed package (no DB needed).
- **Command**:
  ```bash
  cd backend && python -c "
from app.services.accountability import rank_action_items
from app.schemas.coach import AdherenceWeek, ChurnRisk
items = rank_action_items('m1','Alice', [], ChurnRisk(level='low', reasons=[]))
assert items == [], f'Expected empty, got: {items}'
print('PASS: empty adherence + low churn = no action items')
"
  ```
- **Expected Result**: Prints `PASS: empty adherence + low churn = no action items`; exit code 0.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-002: rank_action_items returns items sorted high before medium
- **Description**: Confirm that when both a high-churn and a medium-adherence item are generated, the high-priority item sorts first.
- **Steps**:
  1. Run a quick Python snippet with high churn + medium adherence (60%).
- **Command**:
  ```bash
  cd backend && python -c "
from app.services.accountability import rank_action_items
from app.schemas.coach import AdherenceWeek, ChurnRisk
items = rank_action_items('m1','Alice',[AdherenceWeek(week_of='2026-06-01',pct=60)],ChurnRisk(level='high',reasons=['pattern']))
assert items[0].priority == 'high', f'Expected high first, got: {items[0].priority}'
print('PASS: high churn item sorts before medium adherence item')
"
  ```
- **Expected Result**: Prints `PASS: high churn item sorts before medium adherence item`; exit code 0.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-003: edit action requires body field (422 on missing body)
- **Description**: Confirm that sending an `edit` PATCH action without a `body` field returns HTTP 422.
- **Steps**:
  1. Create a draft (UAT-API-006) and note its `id`.
  2. Send a PATCH with `{"action": "edit"}` and no `body` field.
  3. Verify HTTP 422 is returned.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" -X PATCH "http://localhost:3000/api/coach/draft/DRAFT_ID" \
    -H "Authorization: Bearer $UAT_AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"action":"edit"}'
  ```
- **Expected Result**: `422`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-004: Nudge endpoint rejects unauthenticated request
- **Description**: Confirm POST /coach/nudge returns 401 without a Bearer token.
- **Steps**:
  1. Send a POST to `/api/coach/nudge` with a valid body but no Authorization header.
  2. Verify HTTP 401.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w "%{http_code}" -X POST http://localhost:3000/api/coach/nudge \
    -H "Content-Type: application/json" \
    -d '{"member_id":"m1","member_name":"Alice","action_item":{"priority":"high","member_id":"m1","member_name":"Alice","reason":"test","context":{}}}'
  ```
- **Expected Result**: `401`
- [x] Pass <!-- 2026-06-11 -->
