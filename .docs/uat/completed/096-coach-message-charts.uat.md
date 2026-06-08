# UAT: Message-Pattern & 4-Week Comparison Charts (Coach Dashboard)

> **Source task**: [`.docs/tasks/096-coach-message-charts.md`](../tasks/096-coach-message-charts.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Backend server running on `http://localhost:8000`
- [ ] Frontend dev server running on `http://localhost:5173`
- [ ] Neo4j seeded with Jordan Rivera's member context (run `make seed` or equivalent so `ChatMessage`, `AssessmentWorkout`, and `AdherenceWeek` nodes exist)
- [ ] `UAT_AUTH_TOKEN` env var set to a valid JWT for a seeded demo account (Jordan Rivera's email). Obtain via: `curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=<demo-email>&password=<demo-password>' | jq -r '.access_token'`

---

## API Tests

### UAT-API-001: GET /coach/brief returns message_pattern array
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that the brief response now includes the `message_pattern` array with per-week member/coach message counts
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{message_pattern}'
  ```
- **Expected Result**: `200 OK`. The `message_pattern` key is an array. Each element has the shape `{"week_of": "<YYYY-MM-DD>", "member_count": <int>, "coach_count": <int>}`. With the Jordan Rivera seed data (3 member messages + 1 coach message across multiple weeks), the array is non-empty and at least one element has `member_count > 0`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-002: GET /coach/brief returns weekly_comparison array
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that the brief response includes the `weekly_comparison` array with per-week adherence, workout, and message aggregates
- **Steps**:
  1. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '{weekly_comparison}'
  ```
- **Expected Result**: `200 OK`. The `weekly_comparison` key is an array. Each element has the shape `{"week_of": "<YYYY-MM-DD>", "adherence_pct": <int>, "workouts_completed": <int>, "messages_sent": <int>}`. With seeded data, at least one element has `workouts_completed > 0`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-003: message_pattern includes coach-side messages (SENT_COACH_MESSAGE)
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies that the coach-side message (seeded via `SENT_COACH_MESSAGE` relationship) is counted in `message_pattern.coach_count`, not ignored as it was before this task
- **Steps**:
  1. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '[.message_pattern[] | select(.coach_count > 0)]'
  ```
- **Expected Result**: `200 OK`. The filtered array is non-empty — at least one `MessagePatternPoint` has `coach_count >= 1`. The Jordan Rivera seed has one coach message (`"from_": "coach"` with ts `2026-06-03T19:05:00-07:00`), so the week of `2026-06-02` (or equivalent Monday) must have `coach_count: 1`.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-004: weekly_comparison is capped at last 4 weeks
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies the `weekly_comparison` array never exceeds 4 elements regardless of how many weeks of data exist
- **Steps**:
  1. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.weekly_comparison | length'
  ```
- **Expected Result**: `200 OK`. The printed integer is between 1 and 4 (inclusive). It must never exceed 4.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-005: message_pattern is capped at last 8 weeks
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verifies the `message_pattern` array never exceeds 8 elements
- **Steps**:
  1. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.message_pattern | length'
  ```
- **Expected Result**: `200 OK`. The printed integer is between 0 and 8 (inclusive). Must never exceed 8.
- [x] Pass <!-- 2026-06-08 -->

### UAT-API-006: GET /coach/brief without auth returns 401
- **Endpoint**: `GET /coach/brief`
- **Auth-Required**: false
- **Description**: Verifies the endpoint rejects unauthenticated requests — unchanged behavior that still holds after this task
- **Steps**:
  1. Run the curl command below (no auth header)
- **Command**:
  ```bash
  curl -sS -X GET 'http://localhost:8000/coach/brief' | jq '.'
  ```
- **Expected Result**: `401 Unauthorized`. Response body contains an error detail.
- [x] Pass <!-- 2026-06-08 -->

---

## UI Tests

### UAT-UI-001: Coach dashboard shows "Message Pattern" card
- **Page**: `http://localhost:5173/coach`
- **Description**: Verifies the Coach page renders a titled card for "Message Pattern" with the Recharts bar chart visible when message data is present
- **Steps**:
  1. Log in as the demo user (Jordan Rivera account)
  2. Navigate to `http://localhost:5173/coach`
  3. Wait for the brief to load (loading state clears)
  4. Scroll down past the Morning Brief / Adherence row
  5. Observe the "Message Pattern" card
- **Expected Result**: A card with the heading "MESSAGE PATTERN" (uppercase per design token style) is visible. Below the heading, a Recharts bar chart renders with bars in at least one week column. Two legend entries — "Member" and "Coach" — are shown. No JS error in the browser console.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-002: Coach dashboard shows "Last 4 Weeks" comparison card
- **Page**: `http://localhost:5173/coach`
- **Description**: Verifies the Coach page renders a titled "Last 4 Weeks" card with the grouped Recharts comparison chart
- **Steps**:
  1. Log in as the demo user (Jordan Rivera account)
  2. Navigate to `http://localhost:5173/coach`
  3. Wait for the brief to load
  4. Scroll down to the Message Pattern / Last 4 Weeks row
  5. Observe the "Last 4 Weeks" card
- **Expected Result**: A card with the heading "LAST 4 WEEKS" is visible. Below the heading, a grouped Recharts bar chart renders. The legend shows three series: "Adherence %", "Workouts", and "Messages". No JS error in the browser console.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-003: Chart cards use design tokens — no hardcoded hex colors
- **Page**: `http://localhost:5173/coach`
- **Description**: Verifies chart series bars use CSS variable design tokens (`--chart-1`, `--chart-2`, `--chart-3`, `--chart-5`) rather than hardcoded hex values, ensuring correct theming
- **Steps**:
  1. Log in and navigate to `/coach`
  2. Open browser DevTools → Elements
  3. Inspect a bar element inside the "Message Pattern" chart (look for `<rect>` elements inside the SVG)
  4. Check the `fill` attribute value
- **Expected Result**: The `fill` attribute on bar `<rect>` elements reads `var(--chart-1)` and `var(--chart-2)` (CSS variable references), not hardcoded hex strings like `#f97316`. Similarly, the "Last 4 Weeks" bars use `var(--chart-1)`, `var(--chart-3)`, and `var(--chart-5)`.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-004: Three distinct charts are visible on the Coach dashboard
- **Page**: `http://localhost:5173/coach`
- **Description**: Verifies all three charts required by the assessment spec — adherence trend, message pattern, and 4-week comparison — are rendered
- **Steps**:
  1. Log in and navigate to `/coach`
  2. Wait for data to load
  3. Count the distinct chart cards on the page
- **Expected Result**: Three separate chart/data-visualization cards are visible: (1) "ADHERENCE — LAST 4 WEEKS" (existing bar chart), (2) "MESSAGE PATTERN" (new Recharts chart), (3) "LAST 4 WEEKS" comparison (new Recharts chart). All three are visible without horizontal scrolling on a standard desktop viewport.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: MessagePatternChart renders null when data is empty
- **Scenario**: The `message_pattern` array is empty (no messages seeded for the user)
- **Steps**:
  1. Confirm `brief.message_pattern` is `[]` by checking the API: `curl -sS 'http://localhost:8000/coach/brief' -H "Authorization: Bearer $UAT_AUTH_TOKEN" | jq '.message_pattern | length'`
  2. If non-zero, skip this test (Jordan Rivera seed has messages)
  3. If zero (testing with a different account), navigate to `/coach` and observe the "Message Pattern" card area
- **Expected Result**: When `message_pattern` is empty, the chart area either: (a) renders the fallback text "No message history yet." inside the card, or (b) the `MessagePatternChart` component returns `null` and nothing is rendered inside the card body. No chart renders. No JS error thrown.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-08 -->

### UAT-EDGE-002: WeeklyComparisonChart renders null when data is empty
- **Scenario**: The `weekly_comparison` array is empty (no adherence/workout/message data)
- **Steps**:
  1. Confirm `brief.weekly_comparison` is `[]` for a fresh/empty-data user
  2. If testing with Jordan Rivera (has data), skip this test or observe the card still renders gracefully
  3. For an account with no data, navigate to `/coach` and observe the "Last 4 Weeks" card
- **Expected Result**: When `weekly_comparison` is empty, the card body shows the fallback text "Not enough weekly data yet." No chart renders. No JS error thrown.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-08 -->

---

**UAT**: [`.docs/uat/096-coach-message-charts.uat.md`](../uat/096-coach-message-charts.uat.md)
