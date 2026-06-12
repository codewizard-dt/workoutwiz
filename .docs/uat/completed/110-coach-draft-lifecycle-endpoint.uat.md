# UAT: Coach Draft Lifecycle Endpoint

> **Source task**: [`.docs/tasks/110-coach-draft-lifecycle-endpoint.md`](../tasks/110-coach-draft-lifecycle-endpoint.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Dev stack running: `make dev` (serves at `http://localhost:3000`)
- [ ] Database migrations applied (coach_drafts table exists)
- [ ] Auth token obtained and exported: `export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:3000/api/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=alex@example.com&password=password123' | jq -r .access_token)`
- [ ] `jq` installed on the host

---

## API Tests

### UAT-API-001: Create a coach draft (POST /coach/draft)
- **Endpoint**: `POST /api/coach/draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify a new draft can be created and returns HTTP 201 with `status: "draft"`. This creates the record that all subsequent PATCH/GET tests depend on — save the returned `id`.
- **Steps**:
  1. Run the curl command below as-is.
  2. Note the `id` field from the response — substitute it for `<id-from-UAT-API-001>` in later tests.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:3000/api/coach/draft' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"m1","member_name":"Jordan Rivera","content_type":"nudge","body":"Hey Jordan, noticed you missed a session this week.","grounded_on":["low adherence"]}' | jq '.'
  ```
- **Expected Result**: HTTP 201 with a JSON object containing:
  - `"id"`: a UUID string
  - `"member_id"`: `"m1"`
  - `"member_name"`: `"Jordan Rivera"`
  - `"content_type"`: `"nudge"`
  - `"body"`: `"Hey Jordan, noticed you missed a session this week."`
  - `"grounded_on"`: `["low adherence"]`
  - `"status"`: `"draft"`
  - `"created_by"`: `"alex@example.com"`
  - `"approved_by"`: `null`
  - `"approved_at"`: `null`
  - `"sent_at"`: `null`
  - `"created_at"`: an ISO datetime string
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-002: Create a recommendation draft (POST /coach/draft, content_type=recommendation)
- **Endpoint**: `POST /api/coach/draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify `content_type: "recommendation"` is accepted as a valid content type.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:3000/api/coach/draft' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"m2","member_name":"Alex Chen","content_type":"recommendation","body":"Consider adding a rest day on Thursday.","grounded_on":[]}' | jq '{id,content_type,status}'
  ```
- **Expected Result**: HTTP 201 with `"content_type": "recommendation"` and `"status": "draft"`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-003: List all drafts (GET /coach/draft)
- **Endpoint**: `GET /api/coach/draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the list endpoint returns an array including the draft created in UAT-API-001. Data from UAT-API-001 and UAT-API-002 must exist.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq 'length, .[0].status'
  ```
- **Expected Result**: HTTP 200 with a JSON array of at least 2 items. The first item in the array is the most recently created draft (ordered by `created_at DESC`). Each element has the `CoachDraftSchema` shape (`id`, `member_id`, `member_name`, `content_type`, `body`, `grounded_on`, `status`, `created_by`, `approved_by`, `approved_at`, `sent_at`, `created_at`).
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-004: Filter drafts by status=draft (GET /coach/draft?status=draft)
- **Endpoint**: `GET /api/coach/draft?status=draft`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the optional `?status` query parameter correctly filters results to only `"draft"` records.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[].status] | unique'
  ```
- **Expected Result**: HTTP 200 with a JSON array where every element has `"status": "draft"`. The jq expression returns `["draft"]` (only one distinct status value).
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-005: Approve a draft (PATCH /coach/draft/{id}, action=approve)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the `approve` action transitions status from `"draft"` to `"approved"` and populates `approved_by` and `approved_at`.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID saved in UAT-API-001.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}' | jq '{status,approved_by,approved_at}'
  ```
- **Expected Result**: HTTP 200 with:
  - `"status"`: `"approved"`
  - `"approved_by"`: `"alex@example.com"`
  - `"approved_at"`: a non-null ISO datetime string
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-006: Edit an approved draft resets status to draft (PATCH, action=edit after approve)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that editing an already-approved draft resets `status` back to `"draft"` and clears `approved_by`/`approved_at`, enforcing re-approval before sending. Depends on UAT-API-005 having approved the draft first.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID from UAT-API-001.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"edit","body":"Hey Jordan, great work this week. Keep it up!"}' | jq '{status,body,approved_by,approved_at}'
  ```
- **Expected Result**: HTTP 200 with:
  - `"status"`: `"draft"` (reset from `"approved"`)
  - `"body"`: `"Hey Jordan, great work this week. Keep it up!"`
  - `"approved_by"`: `null` (cleared)
  - `"approved_at"`: `null` (cleared)
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-007: Send blocked when status is draft (PATCH, action=send on unapproved draft)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that attempting to send a draft that is in `"draft"` status (not `"approved"`) returns HTTP 409 with the correct error detail. At this point the draft was reset to `"draft"` by UAT-API-006.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID from UAT-API-001.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 409 with `{"detail": "Draft must be approved before it can be sent"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-008: Re-approve then send the draft (full happy path completion)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the complete `draft → approved → sent` lifecycle. First re-approve the draft (reset to `"draft"` in UAT-API-006), then send it. Two sequential PATCH calls.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID from UAT-API-001.
  2. Run Step A (approve).
  3. Run Step B (send).
- **Command (Step A — approve again)**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}' | jq '{status}'
  ```
- **Expected (Step A)**: HTTP 200 with `{"status": "approved"}`.
- **Command (Step B — send)**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}' | jq '{status,sent_at}'
  ```
- **Expected (Step B)**: HTTP 200 with:
  - `"status"`: `"sent"`
  - `"sent_at"`: a non-null ISO datetime string
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-009: Filter drafts by status=sent (GET /coach/draft?status=sent)
- **Endpoint**: `GET /api/coach/draft?status=sent`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the `?status=sent` filter returns only drafts that have been sent. The draft from UAT-API-001/008 should appear here.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=sent' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[].status] | unique'
  ```
- **Expected Result**: HTTP 200 with a JSON array where every element has `"status": "sent"`. The jq expression returns `["sent"]`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-010: Approve a sent draft is blocked (PATCH, approve on sent draft)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that attempting to approve a draft that is already in `"sent"` status returns HTTP 409. Depends on the draft being in `"sent"` status after UAT-API-008.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID from UAT-API-001.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 409 with `{"detail": "Cannot approve a sent draft"}`.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-API-011: Edit a sent draft is blocked (PATCH, edit on sent draft)
- **Endpoint**: `PATCH /api/coach/draft/<id-from-UAT-API-001>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that attempting to edit a draft in `"sent"` status returns HTTP 409. Depends on UAT-API-008.
- **Steps**:
  1. Substitute `<id-from-UAT-API-001>` with the UUID from UAT-API-001.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-001>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"edit","body":"Trying to override sent draft"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 409 with `{"detail": "Cannot edit a sent draft"}`.
- [x] Pass <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: PATCH non-existent draft returns 404
- **Scenario**: Requesting a PATCH on a UUID that does not exist in the database.
- **Steps**:
  1. Run the curl command below as-is (the UUID is a well-formed but non-existent ID).
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/00000000-0000-0000-0000-000000000000' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 404 with `{"detail": "Draft not found"}`.
- **Auth-Required**: true
- **Auth-Role**: user
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-002: Edit action requires body field (422 when body is missing)
- **Scenario**: Calling PATCH with `action: "edit"` but omitting the `body` field.
- **Steps**:
  1. Create a fresh draft first (or use UAT-API-002's id, which is still in `"draft"` status).
  2. Run the curl command below, substituting `<id-from-UAT-API-002>` with the id from UAT-API-002.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-002>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"edit"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 422 with `{"detail": "body is required for edit action"}`.
- **Auth-Required**: true
- **Auth-Role**: user
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-003: Unknown action returns 422
- **Scenario**: Calling PATCH with an action value that is not one of "approve", "edit", or "send".
- **Steps**:
  1. Substitute `<id-from-UAT-API-002>` with the id from UAT-API-002.
  2. Run the curl command.
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<id-from-UAT-API-002>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"delete"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 422 with `{"detail": "Unknown action: delete"}`.
- **Auth-Required**: true
- **Auth-Role**: user
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-004: POST /coach/draft without auth returns 401
- **Scenario**: Unauthenticated request to a protected endpoint.
- **Steps**:
  1. Run the curl command below as-is (no Authorization header).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:3000/api/coach/draft' -H 'Content-Type: application/json' -d '{"member_id":"m1","member_name":"Jordan Rivera","content_type":"nudge","body":"test"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 401.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-005: GET /coach/draft without auth returns 401
- **Scenario**: Unauthenticated request to the list endpoint.
- **Steps**:
  1. Run the curl command below as-is (no Authorization header).
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft' | jq '{detail}'
  ```
- **Expected Result**: HTTP 401.
- [x] Pass <!-- 2026-06-11 -->

---

### UAT-EDGE-006: PATCH /coach/draft/{id} without auth returns 401
- **Scenario**: Unauthenticated request to the PATCH endpoint.
- **Steps**:
  1. Run the curl command below as-is (no Authorization header).
- **Command**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/00000000-0000-0000-0000-000000000000' -H 'Content-Type: application/json' -d '{"action":"approve"}' | jq '{detail}'
  ```
- **Expected Result**: HTTP 401.
- [x] Pass <!-- 2026-06-11 -->

---

## Integration Tests

### UAT-INT-001: POST /coach/nudge persists a CoachDraft and returns draft_id
- **Components**: `POST /coach/nudge` → CoachDraft DB row → `NudgeResponse.draft_id`
- **Flow**: Calling the nudge endpoint creates a draft with `status: "draft"` as a side effect, and the response includes the `draft_id` UUID for the new draft.
- **Steps**:
  1. Call `POST /api/coach/nudge` with a valid action item.
  2. Verify the response contains a non-null `draft_id`.
  3. Use the returned `draft_id` to call `GET /api/coach/draft` (filtered by `status=draft`) and confirm the new draft appears.
- **Command (Step 1 — call nudge)**:
  ```bash
  curl -sS -X POST 'http://localhost:3000/api/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"m1","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"m1","member_name":"Jordan Rivera","reason":"low adherence this week","context":{"adherence_pct":40,"week_of":"2026-06-01"}}}' | jq '{draft_message,draft_id}'
  ```
- **Expected (Step 1)**: HTTP 200 with:
  - `"draft_message"`: a non-empty string (LLM-generated nudge text)
  - `"draft_id"`: a non-null UUID string
- [x] Pass <!-- 2026-06-11 -->
- **Command (Step 2 — verify draft exists)**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.member_id == "m1")] | length'
  ```
- **Expected (Step 2)**: HTTP 200 with a count of at least 1 (the nudge-persisted draft for member `m1` is in the list).
- **Auth-Required**: true
- **Auth-Role**: user
- [x] Pass (Step 2 — verify draft persisted) <!-- 2026-06-11 -->

---

### UAT-INT-002: Complete lifecycle — draft created via POST, progressed through approve and send, visible via GET filters
- **Components**: `POST /coach/draft` → `PATCH approve` → `PATCH send` → `GET ?status=sent`
- **Flow**: Full end-to-end verification of the state machine in a single coherent sequence.
- **Steps**:
  1. Create a new draft (Step A).
  2. Confirm it appears in `GET ?status=draft` (Step B).
  3. Approve it (Step C).
  4. Confirm it no longer appears in `GET ?status=draft` and does appear in `GET ?status=approved` (Step D).
  5. Send it (Step E).
  6. Confirm it appears in `GET ?status=sent` (Step F).
- **Command (Step A — create)**:
  ```bash
  curl -sS -X POST 'http://localhost:3000/api/coach/draft' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"m3","member_name":"Sam Lee","content_type":"recommendation","body":"Add a deload week this cycle.","grounded_on":["high training load"]}' | jq '.id'
  ```
- **Expected (Step A)**: HTTP 201, prints the new draft's UUID. Save as `<int2-draft-id>`.
- **Command (Step B — verify status=draft)**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.member_id == "m3")] | length'
  ```
- **Expected (Step B)**: At least 1 result (the new draft is in the draft list).
- **Command (Step C — approve)**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<int2-draft-id>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"approve"}' | jq '{status}'
  ```
- **Expected (Step C)**: HTTP 200 with `{"status": "approved"}`.
- **Command (Step D — verify filtered by approved)**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=approved' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.member_id == "m3")] | length'
  ```
- **Expected (Step D)**: At least 1 result (now visible in approved filter, not in draft filter).
- **Command (Step E — send)**:
  ```bash
  curl -sS -X PATCH 'http://localhost:3000/api/coach/draft/<int2-draft-id>' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"action":"send"}' | jq '{status,sent_at}'
  ```
- **Expected (Step E)**: HTTP 200 with `{"status": "sent", "sent_at": "<non-null iso>"}`.
- **Command (Step F — verify in sent filter)**:
  ```bash
  curl -sS -X GET 'http://localhost:3000/api/coach/draft?status=sent' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.member_id == "m3")] | length'
  ```
- **Expected (Step F)**: At least 1 result (the draft is now in the sent list).
- **Auth-Required**: true
- **Auth-Role**: user
- [x] Pass <!-- 2026-06-11 -->
