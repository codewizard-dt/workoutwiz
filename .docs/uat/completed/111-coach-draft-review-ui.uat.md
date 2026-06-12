# UAT: Coach Draft Review UI (PendingDraftsPanel + HITL Gate)

> **Source task**: [`.docs/tasks/111-coach-draft-review-ui.md`](../tasks/111-coach-draft-review-ui.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Backend server running at `http://localhost:8000` (or the full dev stack at `http://localhost:3000`)
- [ ] `$UAT_AUTH_TOKEN` environment variable set — obtain with:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -d 'username=alex@example.com&password=password123' | jq -r .access_token)
  ```
- [ ] Database migrations have run and the `coach_draft` table exists
- [ ] Frontend dev stack reachable at `http://localhost:3000/coach` (for UI tests)

---

## API Tests

### UAT-API-001: Create coach draft — happy path
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `POST /coach/draft`
- **Description**: Verify that a new coach draft can be created with `status: "draft"`. This creates the data that subsequent tests depend on.
- **Steps**:
  1. Set `$UAT_AUTH_TOKEN` per Prerequisites
  2. Run the curl command below as-is
  3. Copy the returned `id` field for use in UAT-API-002 through UAT-API-009
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-jordan-001","member_name":"Jordan Rivera","content_type":"nudge","body":"Hey Jordan, noticed your adherence dipped this week — just checking in. Your Coach","grounded_on":["low adherence"]}' | jq '.'
  ```
- **Expected Result**: `201 Created` with a JSON body matching:
  ```json
  {
    "id": "<uuid>",
    "member_id": "m-jordan-001",
    "member_name": "Jordan Rivera",
    "content_type": "nudge",
    "body": "Hey Jordan, noticed your adherence dipped this week — just checking in. Your Coach",
    "grounded_on": ["low adherence"],
    "status": "draft",
    "created_by": "alex@example.com",
    "approved_by": null,
    "approved_at": null,
    "sent_at": null,
    "created_at": "<iso-timestamp>"
  }
  ```
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-002: List all drafts — returns the created draft
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/draft`
- **Description**: Verify that `GET /coach/draft` returns all drafts including the one created in UAT-API-001.
- **Steps**:
  1. Run the curl command below as-is (data from UAT-API-001 must exist)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '. | length, .[0].status'
  ```
- **Expected Result**: `200 OK` with a JSON array. The array length is at least `1`, and the first element's `status` is `"draft"`. Each item has all `CoachDraftSchema` fields (`id`, `member_id`, `member_name`, `content_type`, `body`, `grounded_on`, `status`, `created_by`, `approved_by`, `approved_at`, `sent_at`, `created_at`).
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-003: List drafts filtered by status
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `GET /coach/draft?status=draft`
- **Description**: Verify that the `?status=` query parameter filters results. The draft from UAT-API-001 should appear; no `approved` or `sent` items should appear.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/draft?status=draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | .status] | unique'
  ```
- **Expected Result**: `200 OK` with a JSON array where every item's `status` equals `"draft"`. The jq projection returns `["draft"]`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-004: Approve a draft — happy path
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify `action: "approve"` transitions status from `draft` → `approved` and sets `approved_by` and `approved_at`.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the `id` from UAT-API-001
  2. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq '{status, approved_by, approved_at}'
  ```
- **Expected Result**: `200 OK` with `{"status": "approved", "approved_by": "alex@example.com", "approved_at": "<iso-timestamp>"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-005: Edit an approved draft — resets to draft
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify `action: "edit"` on an `approved` draft resets `status` back to `draft`, clears `approved_by` and `approved_at`, and updates the body.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the same id used in UAT-API-004 (which is now `approved`)
  2. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"edit","body":"Hey Jordan, just a quick check-in this week. Your Coach"}' | jq '{status, body, approved_by, approved_at}'
  ```
- **Expected Result**: `200 OK` with `{"status": "draft", "body": "Hey Jordan, just a quick check-in this week. Your Coach", "approved_by": null, "approved_at": null}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-006: Send blocked on draft status — HTTP 409
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that `action: "send"` is rejected with HTTP 409 when the draft's `status` is `draft` (not yet approved). The HITL gate must hold.
- **Steps**:
  1. The draft from UAT-API-001 is now back in `draft` status after UAT-API-005
  2. Substitute `<id-from-UAT-API-001>` and run the curl command below
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"send"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `409 Conflict` with `{"detail": "Draft must be approved before it can be sent"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-007: Re-approve then send — full lifecycle
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that after re-approval (following an edit that reset status), the `send` action succeeds and sets `status: "sent"` with a `sent_at` timestamp.
- **Steps**:
  1. First re-approve (the draft is currently `draft` after UAT-API-005):
     ```bash
     curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq .status
     ```
  2. Then send (substitute id and run):
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"send"}' | jq '{status, sent_at}'
  ```
- **Expected Result**: `200 OK` with `{"status": "sent", "sent_at": "<iso-timestamp>"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-008: Approve a sent draft — HTTP 409
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that `action: "approve"` on a `sent` draft is rejected with HTTP 409. The draft from UAT-API-007 is now `sent`.
- **Steps**:
  1. The draft is now `sent` after UAT-API-007
  2. Substitute id and run:
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `409 Conflict` with `{"detail": "Cannot approve a sent draft"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-009: Edit a sent draft — HTTP 409
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that `action: "edit"` on a `sent` draft is rejected with HTTP 409.
- **Steps**:
  1. The draft is still `sent` after UAT-API-007
  2. Substitute id and run:
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<id-from-UAT-API-001>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"edit","body":"New text"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `409 Conflict` with `{"detail": "Cannot edit a sent draft"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-010: Edit without body field — HTTP 422
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that `action: "edit"` without a `body` field returns HTTP 422.
- **Steps**:
  1. Create a fresh draft first (to get a non-sent id):
     ```bash
     NEW_DRAFT_ID=$(curl -sS -X POST 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-test","member_name":"Test Member","content_type":"nudge","body":"Test body","grounded_on":[]}' | jq -r .id)
     ```
  2. Substitute `<new-draft-id>` with the value of `$NEW_DRAFT_ID` and run:
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<new-draft-id>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"edit"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `422 Unprocessable Entity` with `{"detail": "body is required for edit action"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-011: PATCH non-existent draft ID — HTTP 404
- **Auth-Required**: true
- **Auth-Role**: user
- **Endpoint**: `PATCH /coach/draft/{id}`
- **Description**: Verify that a PATCH to a non-existent draft UUID returns HTTP 404.
- **Steps**:
  1. Run the curl command below as-is (uses a valid UUID format that does not exist in the DB)
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/00000000-0000-0000-0000-000000000000' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `404 Not Found` with `{"detail": "Draft not found"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-012: Auth gate — unauthenticated requests return 401
- **Auth-Required**: false
- **Auth-Role**: guest
- **Endpoint**: `GET /coach/draft`
- **Description**: Verify that all coach draft endpoints reject unauthenticated requests with HTTP 401.
- **Steps**:
  1. Run the curl command below (no Authorization header)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/draft' | jq '{detail}'
  ```
- **Expected Result**: HTTP `401 Unauthorized`. Response body contains a `detail` field indicating authentication is required.
- [x] Pass <!-- 2026-06-11 -->

---

## UI Tests

### UAT-UI-001: Panel absent when no pending drafts exist for member
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that `PendingDraftsPanel` renders nothing when there are no `draft` or `approved` items for the selected member. The "Pending Drafts" heading must not appear.
- **Steps**:
  1. Log in as `alex@example.com` / `password123`
  2. Navigate to `http://localhost:3000/coach`
  3. Select a member that has no pending drafts (or clear all drafts for the selected member by sending them via API)
  4. Inspect the page — scroll below the Action Items card
- **Expected Result**: No element with the text "Pending Drafts" appears on the page. The area below Action Items shows the message-pattern / 4-week comparison section without a drafts panel.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-002: Panel renders when pending drafts exist
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that `PendingDraftsPanel` renders the "Pending Drafts" header and draft cards when `draft` or `approved` items exist for the selected member.
- **Steps**:
  1. Create a draft via API for a member that is visible in the member selector:
     ```bash
     curl -sS -X POST 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-jordan-001","member_name":"Jordan Rivera","content_type":"nudge","body":"Test nudge for UI test","grounded_on":["low adherence"]}'
     ```
  2. Navigate to `http://localhost:3000/coach`
  3. Select "Jordan Rivera" in the member switcher
  4. Scroll below the Action Items card
- **Expected Result**: A "Pending Drafts" panel appears below the Action Items card. At least one draft card is visible, showing a status badge (e.g. "draft · nudge"), a textarea pre-filled with the draft body, and a disabled "Send" button.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-003: Draft card shows status badge, content type, and grounded-on tags
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that each draft card in `PendingDraftsPanel` displays the `status · content_type` badge and grounded-on fact chips.
- **Steps**:
  1. A `draft` status nudge with `grounded_on: ["low adherence"]` must exist (created in UAT-UI-002)
  2. On the CoachPage with Jordan Rivera selected, scroll to the Pending Drafts panel
  3. Inspect the first draft card
- **Expected Result**:
  - A status badge in the format `draft · nudge` is visible at the top-left of the card (uppercase)
  - A pill/chip with the text `low adherence` is visible below the textarea
  - A timestamp (locale time string) is visible at the top-right of the card
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-004: Send button is disabled when draft status is "draft"
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that the "Send" button is disabled (not clickable) while the draft's `status` is `draft`. This is the HITL gate.
- **Steps**:
  1. A `draft` status nudge must exist in the panel (from UAT-UI-002)
  2. Scroll to the Pending Drafts panel on CoachPage
  3. Locate the "Send" button for the draft
  4. Attempt to click or inspect it
- **Expected Result**: The "Send" button is disabled (HTML `disabled` attribute present or button unclickable). Its `title` attribute reads `Draft must be approved before sending`. The "Approve" button is visible and enabled.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-005: Approve button transitions draft to approved and enables Send
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that clicking "Approve" calls `PATCH /coach/draft/{id}` with `action: "approve"`, the UI updates to show `approved · nudge` in the badge, and the "Send" button becomes enabled.
- **Steps**:
  1. A `draft` status nudge must be visible in the panel
  2. Click the "Approve" button on that draft card
  3. Wait for the UI to update (the hook invalidates the `['coach', 'drafts']` query and re-fetches)
- **Expected Result**:
  - The status badge updates to `APPROVED · NUDGE` (uppercase, green color)
  - The "Approve" button disappears (it only shows when `status === 'draft' && !isEdited`)
  - The "Send" button is now enabled (no `disabled` attribute)
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-006: Editing body shows "Save Edit" button and disables Send
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that modifying the textarea body makes the "Save Edit" button appear and disables the "Send" button (even on an approved draft).
- **Steps**:
  1. An `approved` draft must be visible in the panel (after UAT-UI-005)
  2. Click inside the textarea of that draft and type additional text (e.g. append " (edited)")
- **Expected Result**:
  - A "Save Edit" button appears in the action area alongside the "Send" button
  - The "Send" button becomes disabled (because `isEdited` is true even though status is `approved`)
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-007: Save Edit resets draft status to "draft" and requires re-approval
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify that clicking "Save Edit" calls `PATCH /coach/draft/{id}` with `action: "edit"` and the new body, and the backend resets status to `draft`. The UI must reflect this.
- **Steps**:
  1. The textarea must have been edited (from UAT-UI-006 — "Save Edit" button is visible)
  2. Click "Save Edit"
  3. Wait for the UI to re-fetch
- **Expected Result**:
  - The "Save Edit" button disappears
  - The status badge reverts to `DRAFT · NUDGE`
  - The "Approve" button reappears
  - The "Send" button is disabled again
  - The textarea shows the newly saved body text
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-UI-008: Send succeeds after re-approval — draft leaves panel
- **Page**: `http://localhost:3000/coach`
- **Description**: Verify the full HITL lifecycle: re-approve the edited draft, then send it. After sending, the draft should disappear from the Pending Drafts panel (because `useCoachDrafts` filters out `sent` items).
- **Steps**:
  1. The draft must be in `draft` status after UAT-UI-007
  2. Click "Approve"
  3. Wait for UI to update (status badge turns green / "APPROVED")
  4. Click "Send"
  5. Wait for UI to update
- **Expected Result**:
  - After "Send", the draft card disappears from the Pending Drafts panel (it is now `sent`, which is filtered out by `useCoachDrafts`)
  - If no other pending drafts exist, the entire "Pending Drafts" panel disappears from the page
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: Unknown PATCH action returns 422
- **Scenario**: A PATCH request with an unrecognized `action` value should return HTTP 422 with an error message identifying the unknown action.
- **Steps**:
  1. Create a fresh draft (or reuse an existing non-sent draft id)
  2. Substitute `<draft-id>` and run:
  ```bash
  curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft-id>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"reject"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP `422 Unprocessable Entity` with `{"detail": "Unknown action: reject"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-002: Draft with empty grounded_on list — no chips rendered
- **Scenario**: A draft created with `grounded_on: []` should show no fact chips in the UI.
- **Steps**:
  1. Create a draft with no grounded-on facts:
     ```bash
     curl -sS -X POST 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-jordan-001","member_name":"Jordan Rivera","content_type":"nudge","body":"Short nudge.","grounded_on":[]}'
     ```
  2. Navigate to CoachPage with Jordan Rivera selected
  3. Locate the new draft card in the Pending Drafts panel
- **Expected Result**: No fact chips / pills are rendered below the textarea in that draft card. The textarea and action buttons are still present.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

### UAT-EDGE-003: `useCoachDrafts` filters out `sent` drafts at the UI layer
- **Scenario**: The `useCoachDrafts` hook filters the API response to exclude items with `status === "sent"`. A sent draft must not appear in the panel even if `GET /coach/draft` returns it.
- **Steps**:
  1. Ensure at least one draft has been sent (via any prior UAT step)
  2. Call `GET /coach/draft` — verify `sent` items are returned by the API:
     ```bash
     curl -sS -X GET 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.status == "sent")] | length'
     ```
  3. Navigate to `http://localhost:3000/coach` and inspect the Pending Drafts panel
- **Expected Result**:
  - Step 2 returns a number ≥ 1 (sent drafts exist in the API)
  - Step 3: No sent draft cards appear in the Pending Drafts panel. Only `draft` or `approved` items appear.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

## Integration Tests

### UAT-INT-001: Full HITL lifecycle — nudge → create draft → approve → send
- **Components**: `POST /coach/nudge` → `GET /coach/draft` → `PATCH /coach/draft/{id}` (approve) → `PATCH /coach/draft/{id}` (send)
- **Flow**: Simulate the intended HITL workflow: the nudge endpoint creates a draft, the coach reviews it via the list endpoint, approves it, and sends it.
- **Steps**:
  1. Generate a nudge (creates a draft as a side effect):
     ```bash
     curl -sS -X POST 'http://localhost:8000/coach/nudge' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-jordan-001","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"m-jordan-001","member_name":"Jordan Rivera","reason":"missed 3 workouts","context":{"note":"Usually very consistent; unusual pattern"}}}' | jq '{draft_message, draft_id}'
     ```
     Note the returned `draft_id`.
  2. Fetch the draft to confirm it exists with `status: "draft"`:
     ```bash
     curl -sS -X GET 'http://localhost:8000/coach/draft?status=draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.id == "<draft_id-from-step-1>")] | .[0].status'
     ```
  3. Approve the draft (substitute `<draft_id-from-step-1>`):
     ```bash
     curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft_id-from-step-1>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq .status
     ```
  4. Send the approved draft:
     ```bash
     curl -sS -X PATCH 'http://localhost:8000/coach/draft/<draft_id-from-step-1>' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"action":"send"}' | jq '{status, sent_at}'
     ```
- **Expected Result**:
  - Step 1: Returns `{"draft_message": "<LLM text>", "draft_id": "<uuid>"}` — the `draft_id` is not null
  - Step 2: Returns `"draft"` — the draft is in the list
  - Step 3: Returns `"approved"`
  - Step 4: Returns `{"status": "sent", "sent_at": "<iso-timestamp>"}` — full lifecycle complete
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-INT-002: UI polling — new draft appears without page reload
- **Components**: `useCoachDrafts` 10-second poll → `PendingDraftsPanel` re-render
- **Flow**: A draft created via the API appears in the Pending Drafts panel within ~10 seconds without a manual page reload.
- **Steps**:
  1. Navigate to `http://localhost:3000/coach` with Jordan Rivera selected
  2. Observe the current state of the Pending Drafts panel (note how many cards are visible, or that the panel is absent)
  3. In a separate terminal, create a new draft via API:
     ```bash
     curl -sS -X POST 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"member_id":"m-jordan-001","member_name":"Jordan Rivera","content_type":"nudge","body":"Polling test nudge message","grounded_on":["poll-test"]}'
     ```
  4. Return to the browser. Wait up to 15 seconds without refreshing the page.
- **Expected Result**: Within ~15 seconds the new draft card (with body "Polling test nudge message") appears in the Pending Drafts panel, demonstrating the 10-second polling interval is working.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->
