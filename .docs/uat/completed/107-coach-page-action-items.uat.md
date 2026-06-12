# UAT: Surface Ranked Action Items + Draft Nudges in CoachPage

> **Source task**: [`.docs/tasks/107-coach-page-action-items.md`](../tasks/107-coach-page-action-items.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Docker stack is running (`make up` or equivalent); app available at `http://localhost:3000`
- [ ] Backend API available at `http://localhost:8000`
- [ ] Neo4j seed data is present (Jordan Rivera member exists with churn risk and adherence data)
- [ ] `UAT_AUTH_TOKEN` env var is set to a valid JWT for `alex@example.com` (obtain via `curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -F 'username=alex@example.com' -F 'password=password123' | jq -r '.access_token'`)

---

## API Tests

### UAT-API-001: POST /coach/nudge — happy path with high-churn action item

- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the nudge endpoint accepts a well-formed `NudgeRequest` and returns a non-empty `draft_message`, a `grounded_on` array containing the action item reason, and a `draft_id` (UUID string).
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set in the shell.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"jordan-rivera","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"jordan-rivera","member_name":"Jordan Rivera","reason":"High churn risk: missed 3 consecutive weeks","context":{"churn_level":"high","churn_reasons":["missed 3 consecutive weeks"]}}}' | jq '{draft_message,grounded_on,draft_id}'
  ```
- **Expected Result**: `200 OK` with `{"draft_message": "<non-empty string referencing Jordan Rivera's situation>", "grounded_on": ["High churn risk: missed 3 consecutive weeks"], "draft_id": "<uuid-string or null>"}`. The `draft_message` must be a non-empty string.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-002: POST /coach/nudge — happy path with low-adherence action item

- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the endpoint generates a nudge grounded on an adherence-based action item.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set in the shell.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"jordan-rivera","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"jordan-rivera","member_name":"Jordan Rivera","reason":"Low adherence this week: 40% (week of 2026-06-02)","context":{"week_of":"2026-06-02","adherence_pct":40}}}' | jq '{draft_message,grounded_on}'
  ```
- **Expected Result**: `200 OK` with `draft_message` being a non-empty string and `grounded_on` equal to `["Low adherence this week: 40% (week of 2026-06-02)"]`.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-003: POST /coach/nudge — 401 without auth token

- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: false
- **Description**: Verify that the endpoint returns 401 when no Authorization header is provided.
- **Steps**:
  1. Run the curl command below as-is (no auth header).
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -d '{"member_id":"jordan-rivera","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"jordan-rivera","member_name":"Jordan Rivera","reason":"test","context":{}}}'
  ```
- **Expected Result**: HTTP status `401`.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-004: POST /coach/nudge — 422 with missing required fields

- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that omitting the required `action_item` field returns a 422 validation error.
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set in the shell.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"jordan-rivera","member_name":"Jordan Rivera"}'
  ```
- **Expected Result**: HTTP status `422`.
- [x] Pass <!-- 2026-06-11 -->

---

## UI Tests

### UAT-UI-001: Action Items card renders for a member with action items

- **Page**: `http://localhost:3000/coach`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that the "Action Items" card appears when the selected member has a high churn risk or low/below-target adherence. The card title "Action Items" must be visible.
- **Steps**:
  1. Log in as `alex@example.com` / `password123` and navigate to `http://localhost:3000/coach`.
  2. Wait for the brief to load (member name appears in the left panel).
  3. Observe the main content area between the adherence chart section and the message pattern section.
- **Expected Result**: A card with the heading "ACTION ITEMS" (displayed in uppercase) is visible. At least one action item row appears inside the card, each row showing a priority label (e.g. "HIGH" or "MEDIUM") and a reason string.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

### UAT-UI-002: Each action item row shows priority label, reason text, and "Draft Nudge" button

- **Page**: `http://localhost:3000/coach`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the internal structure of each action item row.
- **Steps**:
  1. Log in and navigate to `http://localhost:3000/coach`.
  2. Wait for the Action Items card to load.
  3. Inspect each row within the card.
- **Expected Result**: Each action item row contains:
  - An uppercase priority label ("HIGH" or "MEDIUM")
  - A reason string (e.g. "High churn risk: …" or "Low adherence this week: …")
  - A button labelled "Draft Nudge"
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

### UAT-UI-003: High-priority items have a visually distinct background tint

- **Page**: `http://localhost:3000/coach`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that rows with `priority === "high"` use a destructive-tinted background, distinct from non-high rows.
- **Steps**:
  1. Log in and navigate to `http://localhost:3000/coach`.
  2. Wait for the Action Items card to load.
  3. If there is a "HIGH" item, inspect its background colour (browser DevTools or visual comparison).
- **Expected Result**: Rows labelled "HIGH" have a reddish/destructive-tinted background (implemented via `color-mix(in srgb, var(--destructive) 8%, var(--card))`). Rows labelled "MEDIUM" use the muted background (`var(--muted)`).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

### UAT-UI-004: Clicking "Draft Nudge" fetches and renders the draft message inline

- **Page**: `http://localhost:3000/coach`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that clicking "Draft Nudge" on an action item calls `POST /api/coach/nudge` and renders the returned `draft_message` inline below the reason text in the same row — without a page reload or navigation.
- **Steps**:
  1. Log in and navigate to `http://localhost:3000/coach`.
  2. Wait for the Action Items card to load with at least one item.
  3. Click the "Draft Nudge" button on the first action item.
  4. Wait up to 15 seconds for the LLM response.
- **Expected Result**: A non-empty text message appears directly beneath the reason text in the same row. The message is rendered in an accent-coloured box (`var(--accent)` background). No page navigation or reload occurs. The "Draft Nudge" button becomes disabled during loading and re-enables after.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

### UAT-UI-005: Action Items card is absent for a member with no flagged items

- **Page**: `http://localhost:3000/coach`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that the card does not render when the selected member has no high churn risk and latest adherence ≥ 70%. This tests the `actionItems.length === 0 → return null` guard.
- **Steps**:
  1. Log in and navigate to `http://localhost:3000/coach`.
  2. In the member switcher, select a member whose churn risk is not "high" AND whose most recent adherence week is ≥ 70% (if such a member exists in the seed data; otherwise note this test as "not applicable — all seed members have action items" and skip).
  3. Wait for the brief to reload.
- **Expected Result**: No card with heading "ACTION ITEMS" is visible in the main content area.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: Multiple "Draft Nudge" clicks on different items produce independent drafts

- **Scenario**: Clicking "Draft Nudge" on two different items should produce two separate inline drafts without overwriting each other.
- **Steps**:
  1. Navigate to `http://localhost:3000/coach` and wait for the Action Items card.
  2. Ensure at least two action items are visible.
  3. Click "Draft Nudge" on the first item. Wait for the draft to appear.
  4. Click "Draft Nudge" on the second item. Wait for the draft to appear.
- **Expected Result**: Both rows independently display their own draft message inline. The draft in the first row is not replaced or cleared when the second row's draft loads.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-11 -->

### UAT-EDGE-002: Action items are sorted high → medium → low

- **Scenario**: If both a high-priority (churn risk) and a medium-priority (50–69% adherence) item exist, high must appear first.
- **Steps**:
  1. Navigate to `http://localhost:3000/coach` for a member with both a high churn risk and a 50–69% adherence week.
  2. Observe the order of rows in the Action Items card.
- **Expected Result**: The row labelled "HIGH" appears above any row labelled "MEDIUM" or "LOW".
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-11 -->

### UAT-EDGE-003: POST /coach/nudge with empty member_name still returns a draft

- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Scenario**: Verify the endpoint handles an empty `member_name` gracefully (no 500 crash; LLM receives the prompt and returns a draft).
- **Steps**:
  1. Ensure `UAT_AUTH_TOKEN` is set.
  2. Run the curl command below.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"unknown-member","member_name":"","action_item":{"priority":"medium","member_id":"unknown-member","member_name":"","reason":"Below-target adherence","context":{"adherence_pct":60}}}' | jq '{draft_message,grounded_on}'
  ```
- **Expected Result**: `200 OK` with a non-empty `draft_message`. The endpoint must not return 500 for an empty name.
- [x] Pass <!-- 2026-06-11 -->

---

## Integration Tests

### UAT-INT-001: Full flow — load brief, compute action items client-side, draft nudge, draft persisted

- **Components**: `CoachPage` → `useCoachBrief` → `useCoachActionItems` → `ActionItemsCard` → `useCoachNudge` → `POST /coach/nudge` → `CoachDraft` DB row
- **Flow**: Load member brief → client computes ranked action items from `adherence_weeks` + `churn_risk` → user clicks "Draft Nudge" → backend LLM call → `draft_message` rendered inline → draft saved to DB (verifiable via `GET /coach/draft`)
- **Steps**:
  1. Log in and navigate to `http://localhost:3000/coach`. Wait for the brief.
  2. Confirm the Action Items card appears with at least one item.
  3. Click "Draft Nudge" on any item. Wait for the inline draft to appear.
  4. Note the text of the inline draft.
  5. Run the verification command below to confirm the draft was persisted to the database.
- **Verification Command**:
  ```bash
  curl -sS 'http://localhost:8000/coach/draft' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.[] | select(.content_type=="nudge")] | first | {id,content_type,status,body}'
  ```
- **Expected Result**:
  - Step 3: The inline draft message is non-empty and appears in an accent box below the action item reason.
  - Step 5: The verification command returns a record with `content_type: "nudge"`, `status: "draft"`, and `body` matching the text displayed inline. The `id` field is a UUID string.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-11 -->
