# UAT: HITL Approval Tests

> **Source task**: [`.docs/tasks/112-hitl-approval-tests.md`](../tasks/112-hitl-approval-tests.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Backend server running and accessible (Docker stack via `make up`, or locally at port 8000)
- [ ] Frontend dev server running at `http://localhost:5173` (Playwright uses this base URL per `playwright.config.ts`)
- [ ] PostgreSQL database seeded with default users (`alex@example.com` / `password123`)
- [ ] `backend/.venv` exists with dev dependencies installed (`pip install -e ".[dev]"`)
- [ ] `TEST_DATABASE_URL` set in `.env` for pytest integration tests (uses in-process ASGI + test DB)
- [ ] Playwright browsers installed (`cd frontend && npx playwright install chromium`)

---

## Pytest Integration Tests

### UAT-PYTEST-001: Run `test_draft_cannot_be_sent_without_approval`

- **File**: `backend/tests/test_hitl_approval.py`
- **Description**: Verifies the state machine enforced by `PATCH /coach/draft/{id}`: sending a `draft`-status draft returns HTTP 409; approving returns 200 with `status: approved`; sending after approval returns 200 with `status: sent`.
- **Steps**:
  1. Ensure the backend test DB is reachable (see Prerequisites)
  2. Run the command below from the project root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && .venv/bin/pytest tests/test_hitl_approval.py::test_draft_cannot_be_sent_without_approval -v
  ```
- **Expected Result**: Test passes (`PASSED`). Internally the test asserts:
  - `POST /api/coach/draft` → `201 Created` with `{"id": "<uuid>", ...}`
  - `PATCH /api/coach/draft/<id>` with `{"action": "send"}` (before approval) → `409 Conflict` with detail `"Draft must be approved before it can be sent"`
  - `PATCH /api/coach/draft/<id>` with `{"action": "approve"}` → `200 OK` with `{"status": "approved", ...}`
  - `PATCH /api/coach/draft/<id>` with `{"action": "send"}` (after approval) → `200 OK` with `{"status": "sent", ...}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-PYTEST-002: Run `test_edit_after_approval_resets_to_draft`

- **File**: `backend/tests/test_hitl_approval.py`
- **Description**: Verifies that editing an approved draft resets its status to `draft`, and that attempting to send after an edit (without re-approval) returns HTTP 409 again.
- **Steps**:
  1. Ensure the backend test DB is reachable (see Prerequisites)
  2. Run the command below from the project root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && .venv/bin/pytest tests/test_hitl_approval.py::test_edit_after_approval_resets_to_draft -v
  ```
- **Expected Result**: Test passes (`PASSED`). Internally the test asserts:
  - `POST /api/coach/draft` → `201 Created`
  - `PATCH /api/coach/draft/<id>` with `{"action": "approve"}` → `200 OK`
  - `PATCH /api/coach/draft/<id>` with `{"action": "edit", "body": "Updated message"}` → `200 OK` with `{"status": "draft", ...}` (approval fields cleared)
  - `PATCH /api/coach/draft/<id>` with `{"action": "send"}` → `409 Conflict`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-PYTEST-003: Run full `test_hitl_approval.py` suite

- **File**: `backend/tests/test_hitl_approval.py`
- **Description**: Runs both HITL tests together to confirm they are independent and do not share state.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && .venv/bin/pytest tests/test_hitl_approval.py -v
  ```
- **Expected Result**: Both tests pass with `2 passed` in the summary. No failures or errors.
- [x] Pass <!-- 2026-06-11 -->

---

## API Tests (Manual Verification via curl)

> These tests confirm the `PATCH /coach/draft/{id}` state-machine API directly, using the seeded `alex@example.com` account. Obtain a token first with UAT-API-001 and substitute it as `$UAT_AUTH_TOKEN`.

### UAT-API-001: Obtain auth token

- **Endpoint**: `POST /auth/jwt/login`
- **Description**: Get a Bearer token for the seeded user to use in subsequent tests.
- **Steps**:
  1. Run the command below; copy the `access_token` value and export it: `export UAT_AUTH_TOKEN=<value>`
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=alex@example.com&password=password123'
  ```
- **Expected Result**: `200 OK` with `{"access_token": "<jwt>", "token_type": "bearer"}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-002: Create a coach draft

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /coach/draft`
- **Description**: Create a new draft in `draft` status. Captures the `id` for subsequent tests.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (from UAT-API-001)
  2. Run the command below; copy the returned `id` and note it as `<draft-id-from-UAT-API-002>`
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/draft' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"uat-member-1","member_name":"UAT Member","content_type":"nudge","body":"Hey there, keep it up!","grounded_on":[]}'
  ```
- **Expected Result**: `201 Created` with body:
  ```json
  {
    "id": "<uuid>",
    "member_id": "uat-member-1",
    "member_name": "UAT Member",
    "content_type": "nudge",
    "body": "Hey there, keep it up!",
    "grounded_on": [],
    "status": "draft",
    "created_by": "alex@example.com",
    "approved_by": null,
    "approved_at": null,
    "sent_at": null,
    "created_at": "<iso>"
  }
  ```
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-003: Send without approval returns 409

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verifies the core HITL guard: a draft in `draft` status cannot be sent — HTTP 409 is returned.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set
  2. Replace `<draft-id-from-UAT-API-002>` with the `id` from UAT-API-002
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-from-UAT-API-002>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}'
  ```
- **Expected Result**: `409 Conflict` with `{"detail": "Draft must be approved before it can be sent"}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-004: Approve a draft

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Approving a `draft`-status draft transitions it to `approved`.
- **Steps**:
  1. Replace `<draft-id-from-UAT-API-002>` with the `id` from UAT-API-002
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-from-UAT-API-002>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}'
  ```
- **Expected Result**: `200 OK` with `{"status": "approved", "approved_by": "alex@example.com", "approved_at": "<iso>", ...}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-005: Send an approved draft succeeds

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: After approval, sending the draft transitions it to `sent`.
- **Steps**:
  1. Replace `<draft-id-from-UAT-API-002>` with the `id` from UAT-API-002 (must be in `approved` state after UAT-API-004)
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-from-UAT-API-002>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}'
  ```
- **Expected Result**: `200 OK` with `{"status": "sent", "sent_at": "<iso>", ...}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-006: Edit after approval resets status to draft

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Create a new draft, approve it, then edit it. The edit must reset status to `draft` and clear `approved_by`/`approved_at`.
- **Steps**:
  1. Create a second draft: run the UAT-API-002 command again and note the new `id` as `<draft-id-for-edit-test>`
  2. Approve it: run UAT-API-004 command substituting `<draft-id-for-edit-test>`
  3. Run the command below with `<draft-id-for-edit-test>`
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-for-edit-test>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"edit","body":"Revised message after approval"}'
  ```
- **Expected Result**: `200 OK` with `{"status": "draft", "approved_by": null, "approved_at": null, "body": "Revised message after approval", ...}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-007: Send after edit (without re-approval) returns 409 again

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: After an edit resets status to `draft`, sending must again be blocked with 409.
- **Steps**:
  1. Use `<draft-id-for-edit-test>` from UAT-API-006 (which is back in `draft` status)
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-for-edit-test>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}'
  ```
- **Expected Result**: `409 Conflict` with `{"detail": "Draft must be approved before it can be sent"}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-008: Edit action without body returns 422

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: The `edit` action requires a `body` field; omitting it must return 422.
- **Steps**:
  1. Use any existing draft ID (e.g. `<draft-id-from-UAT-API-002>` which is in `sent` state, or create a new one)
  2. Actually create a fresh draft for this test to avoid 409-on-sent complications: re-run UAT-API-002 and note the `id` as `<draft-id-for-no-body-test>`
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-for-no-body-test>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"edit"}'
  ```
- **Expected Result**: `422 Unprocessable Entity` with `{"detail": "body is required for edit action"}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-009: PATCH with unknown action returns 422

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Passing an unknown `action` value must return 422 with a descriptive error.
- **Steps**:
  1. Use any existing draft ID in non-sent status
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id-for-no-body-test>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"publish"}'
  ```
- **Expected Result**: `422 Unprocessable Entity` with `{"detail": "Unknown action: publish"}`
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-010: PATCH non-existent draft returns 404

- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Patching a draft ID that does not exist must return 404.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/00000000-0000-0000-0000-000000000000' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}'
  ```
- **Expected Result**: `404 Not Found` with `{"detail": "Draft not found"}`
- [x] Pass <!-- 2026-06-11 -->

---

## Playwright E2E Test

### UAT-E2E-001: Run Playwright `coach-hitl-approval.spec.ts`

- **File**: `frontend/e2e/coach-hitl-approval.spec.ts`
- **Description**: End-to-end test exercising the full approve → send flow through the `CoachPage` Pending Drafts panel in a real browser. Verifies: Send button is disabled before approval; Send button is enabled after clicking Approve; clicking Send completes without error.
- **Steps**:
  1. Ensure the full stack is running (`make up` or `make dev`) — Playwright config uses `baseURL: http://localhost:5173` and expects the backend on port 8000
  2. Run the command below from the project root
- **Command**:
  ```bash
  cd frontend && npx playwright test e2e/coach-hitl-approval.spec.ts --reporter=list
  ```
- **Expected Result**: `1 passed` in the summary. The test:
  - Logs in via `/login` page, filling `#email` and `#password`, and lands on `/workouts`
  - Navigates to `/coach`, waits for network idle
  - If a "Draft Nudge" button is visible, clicks it to create a new draft
  - Finds "Pending Drafts" section and asserts the Send button is disabled
  - Clicks Approve; asserts Send button becomes enabled
  - Clicks Send; test completes without assertion errors
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

## No-Regression Check

### UAT-PYTEST-004: Full pytest suite passes without regressions

- **Description**: Confirms that adding `test_hitl_approval.py` does not break any pre-existing tests.
- **Steps**:
  1. Run the command below from the project root
- **Command**:
  ```bash
  set -a && source .env && set +a && cd backend && .venv/bin/pytest -v
  ```
- **Expected Result**: All previously passing tests continue to pass. `test_hitl_approval.py` contributes 2 additional `PASSED` entries. Zero failures.
- [x] Pass <!-- 2026-06-11 -->
