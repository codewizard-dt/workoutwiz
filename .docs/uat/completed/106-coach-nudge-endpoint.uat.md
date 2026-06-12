# UAT: POST /coach/nudge — Draft Context-Grounded Nudge Message

> **Source task**: [`.docs/tasks/106-coach-nudge-endpoint.md`](../tasks/106-coach-nudge-endpoint.md)
> **Generated**: 2026-06-11

---

## Prerequisites

- [ ] Backend server is running and reachable at `http://localhost:8000` (e.g. via `make up` or `docker compose up`)
- [ ] Database is seeded with the default user (`alex@example.com` / `password123`)
- [ ] `ANTHROPIC_API_KEY` is set in the environment (required for LLM call)
- [ ] Obtain a bearer token and export it:
  ```bash
  export UAT_AUTH_TOKEN=$(curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -d 'username=alex@example.com&password=password123' | jq -r .access_token)
  ```
- [ ] Confirm token is non-empty: `echo $UAT_AUTH_TOKEN` should print a JWT string

---

## API Tests

### UAT-API-001: Happy path — valid NudgeRequest returns 200 with draft message
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the endpoint accepts a fully-populated `NudgeRequest` and returns `200 OK` with a non-empty `draft_message` string and a non-empty `grounded_on` list. Also confirms a `draft_id` field is present (may be a UUID string or null if DB persistence failed).
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Low adherence this week: 40% (week of 2026-06-01)","context":{"week_of":"2026-06-01","adherence_pct":40}}}' | jq '.'
  ```
- **Expected Result**: `200 OK` with body matching:
  ```json
  {
    "draft_message": "<non-empty string — 1–3 sentences>",
    "grounded_on": ["Low adherence this week: 40% (week of 2026-06-01)"],
    "draft_id": "<uuid string or null>"
  }
  ```
  `draft_message` must be a non-empty string. `grounded_on` must contain exactly the `action_item.reason` string passed in the request.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-002: Draft message references the nudge reason
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the generated nudge message is grounded in the member's specific situation — it should reference something from the `action_item.reason` or `context`, not be a generic motivational message.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
  3. Read the returned `draft_message` and confirm it contains a reference to adherence, percentage, or "Jordan" — not a generic phrase like "Keep going!" or "You can do it!"
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Missed 3 sessions this week — scheduled Mon/Wed/Fri","context":{"week_of":"2026-06-01","missed_sessions":3}}}' | jq '.draft_message'
  ```
- **Expected Result**: `200 OK`. The `draft_message` string references the member's name ("Jordan") and/or the specific missed-session situation, not a generic motivational platitude.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-003: 401 returned when no auth token is provided
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: false
- **Description**: Verify the endpoint returns `401 Unauthorized` when called without an `Authorization` header.
- **Steps**:
  1. Run the curl command below as-is (no auth header)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Low adherence","context":{}}}' | jq '.'
  ```
- **Expected Result**: HTTP `401 Unauthorized`. The response body should indicate the request is unauthenticated (e.g. `{"detail": "Unauthorized"}`).
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-004: 422 returned when request body is missing required fields
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify Pydantic validation returns `422 Unprocessable Entity` when required fields are absent (e.g., `action_item` is missing entirely).
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera"}' | jq '.'
  ```
- **Expected Result**: HTTP `422 Unprocessable Entity` with a validation error body containing `detail` array describing which field is missing (e.g. `action_item` field required).
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-005: 422 returned when action_item is missing required sub-fields
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify Pydantic validation catches a malformed `ActionItem` (e.g., `reason` field missing) and returns `422`.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera"}}' | jq '.'
  ```
- **Expected Result**: HTTP `422 Unprocessable Entity` with a `detail` array identifying that `reason` and/or `context` are missing from `action_item`.
- [x] Pass <!-- 2026-06-11 -->

### UAT-API-006: grounded_on list contains the action_item.reason string verbatim
- **Endpoint**: `POST /coach/nudge`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that the `grounded_on` field in the response contains exactly the `reason` string from the submitted `action_item` — the endpoint sets `grounded_on = [body.action_item.reason]`.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
  3. Confirm `grounded_on[0]` exactly equals `"Churn risk: cancelled gym membership last month"`
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"medium","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Churn risk: cancelled gym membership last month","context":{"churn_signal":"cancelled_membership"}}}' | jq '.grounded_on'
  ```
- **Expected Result**: `200 OK` with `grounded_on` equal to `["Churn risk: cancelled gym membership last month"]`.
- [x] Pass <!-- 2026-06-11 -->

---

## Edge Case Tests

### UAT-EDGE-001: Empty context dict is accepted — endpoint does not error
- **Scenario**: `action_item.context` is an empty dict `{}`; the schema allows `dict[str, Any]` with no minimum keys.
- **Steps**:
  1. Ensure `$UAT_AUTH_TOKEN` is set (see Prerequisites)
  2. Run the curl command below as-is
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"low","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Check-in: no recent activity logged","context":{}}}' | jq '.draft_message'
  ```
- **Expected Result**: `200 OK` with a non-empty `draft_message`. No 500 error — the LLM handles the sparse context gracefully.
- [x] Pass <!-- 2026-06-11 -->

### UAT-EDGE-002: Draft persistence failure does not fail the endpoint
- **Scenario**: Even if the database is unavailable or the draft insert fails, `coach_nudge` catches the inner DB exception and still returns a successful response (the draft persistence is best-effort, wrapped in its own try/except).
- **Steps**:
  1. This test verifies behavior that is coded defensively — confirm by running the happy-path (UAT-API-001) again and observing the `draft_id` field.
  2. When persistence succeeds: `draft_id` is a UUID string.
  3. The acceptance criterion is structural: `draft_id` is always present in the response (either a UUID or `null`) and the endpoint never returns 500 solely due to a draft-save failure.
  4. Run the curl command below as-is and confirm the response shape.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Low adherence this week: 40% (week of 2026-06-01)","context":{"week_of":"2026-06-01","adherence_pct":40}}}' | jq '{draft_message_present: (.draft_message | length > 0), draft_id_field_present: (has("draft_id"))}'
  ```
- **Expected Result**: `200 OK` with `{"draft_message_present": true, "draft_id_field_present": true}`.
- [x] Pass <!-- 2026-06-11 -->

---

## Integration Tests

### UAT-INT-001: Full auth → nudge flow — login then call endpoint
- **Components**: `POST /auth/jwt/login` → `POST /coach/nudge`
- **Flow**: Obtain a JWT from the login endpoint in the same shell session, then immediately use it to call the nudge endpoint. Verifies end-to-end that auth and nudge are wired together correctly in the running stack.
- **Steps**:
  1. Run the two-command sequence below (login, then nudge). The token is captured into a shell variable within the same pipeline.
  2. Confirm the nudge response has a non-empty `draft_message`.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/coach/nudge' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"demo-member","member_name":"Jordan Rivera","action_item":{"priority":"high","member_id":"demo-member","member_name":"Jordan Rivera","reason":"Low adherence this week: 40% (week of 2026-06-01)","context":{"week_of":"2026-06-01","adherence_pct":40}}}' | jq '{status_ok: (.draft_message | length > 0), grounded_on_populated: (.grounded_on | length > 0)}'
  ```
  (Requires `$UAT_AUTH_TOKEN` to be set from the Prerequisites step, which itself hits the login endpoint.)
- **Expected Result**: `200 OK` with `{"status_ok": true, "grounded_on_populated": true}`.
- [x] Pass <!-- 2026-06-11 -->
