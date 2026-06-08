# UAT: Coach Member List & Switcher

> **Source task**: [`.docs/tasks/097-coach-member-switcher.md`](../tasks/097-coach-member-switcher.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend server running at `http://localhost:8000`
- [ ] Frontend dev server running at `http://localhost:5173` (or built and served)
- [ ] Neo4j is reachable and the KG seed has been run (`make seed-kg` or equivalent) — at least 5 Member nodes with `display_name`, `tier`, and `age` properties must exist
- [ ] `$UAT_AUTH_TOKEN` is set — obtain with:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=alex@example.com&password=password123' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  ```

---

## API Tests

### UAT-API-001: GET /coach/members returns all seeded members

- **Endpoint**: `GET /coach/members`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies the new members list endpoint returns all seeded Member nodes with required fields.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.'
  ```
- **Expected Result**: `200 OK` with a JSON array of objects. Each object must contain `member_id` (non-empty string), `member_name` (non-empty string), `tier` (string or null), and `member_age` (integer or null). The array must contain **at least 5 entries** (one per seeded persona). Names "Alex Chen", "Jordan Rivera", "Sam Nakamura", "Morgan Lee", and "Casey Williams" must appear in `member_name` fields.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: GET /coach/members requires authentication

- **Endpoint**: `GET /coach/members`
- **Auth-Required**: false
- **Description**: Verifies the endpoint rejects unauthenticated requests.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' 'http://localhost:8000/coach/members'
  ```
- **Expected Result**: HTTP status `401`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: GET /coach/brief with explicit member_id returns that member's data

- **Endpoint**: `GET /coach/brief?member_id=<id>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that passing a `member_id` query param returns the brief for the specified member, not the authenticated user's own profile. Uses the ID of "Alex Chen" from the members list.
- **Steps**:
  1. Fetch the member list and capture Alex Chen's ID:
     ```bash
     ALEX_ID=$(curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq -r '.[] | select(.member_name=="Alex Chen") | .member_id')
     ```
  2. Run the brief request with that ID:
- **Command**:
  ```bash
  curl -sS "http://localhost:8000/coach/brief?member_id=$ALEX_ID" -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{member_id, member_name, tier, member_age}'
  ```
- **Expected Result**: `200 OK`. Response body contains `member_name: "Alex Chen"`. The `member_id` field matches `$ALEX_ID`. `tier` is a non-null string.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-004: GET /coach/brief without member_id falls back to authenticated user's context

- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that omitting `member_id` falls back to the current user's own member record (email-based lookup), preserving the original behavior.
- **Steps**:
  1. Run the curl command below as-is (authenticated as `alex@example.com`)
- **Command**:
  ```bash
  curl -sS 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{member_id, member_name}'
  ```
- **Expected Result**: `200 OK`. Response contains `member_name: "Alex Chen"` (the authenticated user). No `member_id` query param was used.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-005: GET /coach/brief with unknown member_id returns 404

- **Endpoint**: `GET /coach/brief?member_id=<nonexistent>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that requesting a brief for a non-existent member_id returns 404.
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -o /dev/null -w '%{http_code}' 'http://localhost:8000/coach/brief?member_id=00000000-0000-0000-0000-000000000000' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
  ```
- **Expected Result**: HTTP status `404`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-006: GET /coach/brief returns full CoachBriefResponse shape for a specific member

- **Endpoint**: `GET /coach/brief?member_id=<jordan-id>`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies the response shape for Jordan Rivera contains all required fields including goals, injuries, churn_risk, adherence_weeks, equipment, morning_tasks, message_pattern, and weekly_comparison.
- **Steps**:
  1. Fetch Jordan Rivera's member_id:
     ```bash
     JORDAN_ID=$(curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq -r '.[] | select(.member_name=="Jordan Rivera") | .member_id')
     ```
  2. Fetch the brief:
- **Command**:
  ```bash
  curl -sS "http://localhost:8000/coach/brief?member_id=$JORDAN_ID" -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq 'keys'
  ```
- **Expected Result**: `200 OK`. The JSON keys include: `member_id`, `member_name`, `member_age`, `tier`, `goals`, `injuries`, `morning_tasks`, `churn_risk`, `adherence_weeks`, `equipment`, `message_pattern`, `weekly_comparison`. `member_name` is `"Jordan Rivera"`. `injuries` is a non-empty array (Jordan has a shoulder injury and a resolved back strain in the seed data).
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-007: POST /coach/chat with member_id routes to that member's context

- **Endpoint**: `POST /coach/chat`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that sending `member_id` in the chat request body grounds the reply in the specified member's context, not the authenticated user's.
- **Steps**:
  1. Fetch Jordan Rivera's member_id:
     ```bash
     JORDAN_ID=$(curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq -r '.[] | select(.member_name=="Jordan Rivera") | .member_id')
     ```
  2. Send a chat message asking about injuries:
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d "{\"message\":\"What injuries does this member have?\",\"member_id\":\"$JORDAN_ID\"}" | jq '{reply,grounded_facts,session_id}'
  ```
- **Expected Result**: `200 OK`. Response contains `reply` (non-empty string), `grounded_facts` (array), and `session_id` (non-empty string). The `reply` references Jordan Rivera's injury (shoulder or right shoulder) — not Alex Chen's knee injury. `grounded_facts` contains at least one element related to adherence, churn risk, goals, or active injury.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-008: POST /coach/chat without member_id falls back to authenticated user's context

- **Endpoint**: `POST /coach/chat`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that omitting `member_id` in the chat body uses the authenticated user's own member context.
- **Steps**:
  1. Run the curl command below as-is (authenticated as `alex@example.com`)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/chat' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -H 'Content-Type: application/json' -d '{"message":"What is the members name and main injury?"}' | jq '{reply,grounded_facts}'
  ```
- **Expected Result**: `200 OK`. The `reply` references Alex Chen (the authenticated user) and/or their knee injury — not Jordan Rivera. `grounded_facts` is an array (may be empty if no adherence data for this user).
- [x] Pass <!-- 2026-06-08 -->

---

## UI Tests

### UAT-UI-001: Member switcher renders on Coach View page

- **Page**: `/coach` (Coach View)
- **Description**: Verifies the member selector is rendered in the Coach View page header area after members load.
- **Steps**:
  1. Log in to the application as any seeded user (e.g., `alex@example.com` / `password123`)
  2. Navigate to the Coach View page (sidebar nav item)
  3. Wait for the page to fully load
- **Expected Result**: The page header shows a "Member:" label followed by a row of clickable member name buttons (chips). At least 5 member buttons are visible, including buttons labeled "Alex Chen", "Jordan Rivera", "Sam Nakamura", "Morgan Lee", and "Casey Williams". The first member button is in the active/selected state (uses `ww-btn` class without `ww-btn--ghost`, indicating selection) while the rest use `ww-btn--ghost`.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-002: Selecting a different member updates the brief card

- **Page**: `/coach` (Coach View)
- **Description**: Verifies that clicking a different member button in the switcher reloads the member header card to show the newly selected member's data.
- **Steps**:
  1. Load the Coach View page; note which member is shown in the member header card (member name, age, tier)
  2. Click a different member button in the header switcher (e.g., "Jordan Rivera" if Alex is currently selected)
  3. Wait for the brief card to reload
- **Expected Result**: The member header card now shows the newly selected member's name (e.g., "Jordan Rivera"), their age, tier, goals as pill badges, and churn risk badge. The previously selected member's data is no longer displayed. The clicked member button is now in the active/selected state (non-ghost styling) and the previous selection reverts to ghost styling.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-003: Selecting a different member resets the chat to empty state

- **Page**: `/coach` (Coach View)
- **Description**: Verifies that switching members clears the chat conversation and shows the empty-state message grounded in the new member.
- **Steps**:
  1. Load the Coach View; send at least one chat message (e.g., type "Hello" and press Enter)
  2. Confirm the message appears in the chat stream
  3. Click a different member button in the switcher
- **Expected Result**: The chat stream immediately clears — all previous messages disappear. The empty-state placeholder text reappears, referencing the newly selected member's name (e.g., "Ask me anything about Jordan Rivera's progress, or click a quick-prompt above."). No messages from the previous conversation are visible.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-004: Chat textarea placeholder uses selected member's name

- **Page**: `/coach` (Coach View)
- **Description**: Verifies the chat textarea placeholder references the selected member's name dynamically, not a hardcoded "Jordan".
- **Steps**:
  1. Load Coach View; observe the textarea placeholder text
  2. Click a different member button (e.g., "Sam Nakamura")
  3. Observe the textarea placeholder again
- **Expected Result**: After loading, the textarea placeholder contains the member's name (e.g., "Ask about Alex Chen's adherence, sleep, goals…"). After switching to Sam Nakamura, the placeholder updates to "Ask about Sam Nakamura's adherence, sleep, goals…". The word "Jordan" never appears hardcoded unless Jordan Rivera is the selected member.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-005: Empty state text uses selected member's name dynamically

- **Page**: `/coach` (Coach View)
- **Description**: Verifies the chat empty-state message references the currently selected member's name, not a hardcoded name.
- **Steps**:
  1. Load the Coach View — keep the chat empty (do not send any messages)
  2. Observe the empty-state text in the chat area
  3. Click "Morgan Lee" in the member switcher
  4. Observe the empty-state text again
- **Expected Result**: The empty-state text shows the selected member's name (e.g., "Ask me anything about Alex Chen's progress, or click a quick-prompt above."). After switching to Morgan Lee, it updates to "Ask me anything about Morgan Lee's progress, or click a quick-prompt above.". No occurrence of "Jordan" appears unless Jordan Rivera is selected.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: GET /coach/members with valid auth but no Neo4j data returns empty array

- **Scenario**: If no Member nodes exist in the graph, the endpoint returns an empty array rather than an error.
- **Steps**:
  1. This test is **informational** — run only if it is possible to connect to a clean Neo4j instance without seeded members. In a seeded environment, verify the endpoint returns at least 5 members (covered in UAT-API-001).
  2. In a clean environment: `curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '. | length'`
- **Expected Result**: `200 OK` with `[]` (empty array) — no 500 error.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-08 -->

### UAT-EDGE-002: Morgan Lee (member with no injuries) renders brief without injury section

- **Scenario**: A seeded member with zero injuries (`Morgan Lee`) should not cause an error in the brief endpoint or UI.
- **Steps**:
  1. Fetch Morgan Lee's member_id:
     ```bash
     MORGAN_ID=$(curl -sS 'http://localhost:8000/coach/members' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq -r '.[] | select(.member_name=="Morgan Lee") | .member_id')
     ```
  2. Run the brief request:
- **Command**:
  ```bash
  curl -sS "http://localhost:8000/coach/brief?member_id=$MORGAN_ID" -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{member_name, injuries}'
  ```
- **Expected Result**: `200 OK`. `member_name` is `"Morgan Lee"`. `injuries` is an empty array `[]`. No 500 error.
- [x] Pass <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: Full member switch flow — select, load brief, chat, switch, reset

- **Components**: `GET /coach/members` → `GET /coach/brief?member_id=` → `POST /coach/chat` (with `member_id`) → member switch → new brief + empty chat
- **Flow**: The coach loads the page, sees all members, selects Jordan Rivera, views Jordan's brief, sends a chat message, then switches to Alex Chen and confirms the chat resets and the brief now shows Alex's data.
- **Steps**:
  1. Log in to the app (`alex@example.com` / `password123`) and navigate to the Coach View page
  2. Verify the member switcher shows at least 5 members in the page header
  3. Click "Jordan Rivera" in the switcher
  4. Wait for the member header card to show "Jordan Rivera" with her age, tier, goals, and churn risk
  5. Observe that the adherence weeks section shows data (not empty)
  6. Send a chat message: type "What are this member's injuries?" and press Enter
  7. Verify the AI response references Jordan's shoulder injury (not Alex's knee injury)
  8. Click "Alex Chen" in the member switcher
  9. Verify the brief card updates to show "Alex Chen" with his tier and goals
  10. Verify the chat stream is empty (no messages) and the empty-state text references "Alex Chen"
  11. Send a new chat message: "What injuries does this member have?"
  12. Verify the AI response references Alex's knee tendinopathy (not Jordan's shoulder)
- **Expected Result**: All steps pass. Data is correctly scoped to the selected member at each stage. Switching members clears chat history and re-grounds the copilot. No hardcoded "Jordan" text appears when Alex is selected.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-08 -->
