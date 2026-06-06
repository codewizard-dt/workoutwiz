# UAT: KG Chat/Dashboard — Knowledge Graph Frontend Page

> **Source task**: [`.docs/tasks/completed/070-kg-chat-dashboard.md`](../tasks/completed/070-kg-chat-dashboard.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend running on `http://localhost:8000` (`uvicorn app.main:app --reload` from `backend/`)
- [ ] Frontend dev server running on `http://localhost:5173` (`npm run dev` from `frontend/`)
- [ ] Neo4j running and reachable (via Docker Compose or local instance)
- [ ] At least one registered user exists; `$UAT_AUTH_TOKEN` env var set to a valid JWT Bearer token for that user
- [ ] `$UAT_MEMBER_ID` env var set to the UUID of the authenticated user (obtain from `GET /auth/me`)

To obtain token and member ID:
```bash
curl -sS -X POST 'http://localhost:8000/auth/jwt/login' -H 'Content-Type: application/x-www-form-urlencoded' -d 'username=test@example.com&password=testpassword'
# Set UAT_AUTH_TOKEN to the access_token value from the response
curl -sS 'http://localhost:8000/auth/me' -H "Authorization: Bearer $UAT_AUTH_TOKEN"
# Set UAT_MEMBER_ID to the id value from the response
```

---

## API Tests

### UAT-API-001: POST /kg/recommend — happy path returns recommendation
- **Endpoint**: `POST /kg/recommend`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify the endpoint accepts a valid member_id and query, and returns a structured recommendation with exercises, overall_reasoning, and fallback_used flag.
- **Steps**:
  1. Run the curl command below as-is (substituting `$UAT_AUTH_TOKEN` and `$UAT_MEMBER_ID`)
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"member_id\": \"$UAT_MEMBER_ID\", \"query\": \"upper body strength workout, 45 minutes\"}" | jq '{member_id, fallback_used, exercise_count: (.exercises | length), first_exercise: .exercises[0]}'
  ```
- **Expected Result**: `200 OK` with JSON body containing `member_id` (string), `exercises` (non-empty array), `overall_reasoning` (non-empty string), `skipped_exercise_ids` (array), and `fallback_used` (boolean). Each exercise object has `exercise_id`, `name`, `sets` (int), and `reasoning` (string); optionally `reps`, `duration_seconds`, `weight_kg`.
- [FAIL: auto-judge: prerequisite not satisfied — backend not running on localhost:8000] <!-- 2026-06-06 -->

### UAT-API-002: POST /kg/recommend — 401 without auth token
- **Endpoint**: `POST /kg/recommend`
- **Auth-Required**: false
- **Description**: Verify the endpoint rejects unauthenticated requests with 401.
- **Steps**:
  1. Run the curl command below — no Authorization header
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -d '{"member_id": "00000000-0000-0000-0000-000000000000", "query": "test"}'
  ```
- **Expected Result**: `401 Unauthorized` response.
- [FAIL: auto-judge: prerequisite not satisfied — backend not running on localhost:8000] <!-- 2026-06-06 -->

### UAT-API-003: POST /kg/recommend — missing required fields returns 422
- **Endpoint**: `POST /kg/recommend`
- **Auth-Required**: true
- **Auth-Role**: user
- **Description**: Verify that omitting required `query` field returns a validation error.
- **Steps**:
  1. Run the curl command below
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/recommend' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d "{\"member_id\": \"$UAT_MEMBER_ID\"}"
  ```
- **Expected Result**: `422 Unprocessable Entity` with a body describing the missing `query` field.
- [FAIL: auto-judge: prerequisite not satisfied — backend not running on localhost:8000] <!-- 2026-06-06 -->

---

## UI Tests

### UAT-UI-001: /knowledge-graph route renders the page
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify the `/knowledge-graph` route is registered and renders `KnowledgeGraphPage` when authenticated.
- **Steps**:
  1. Open a browser and navigate to `http://localhost:5173` — log in if redirected to the login page
  2. Navigate to `http://localhost:5173/knowledge-graph`
  3. Observe the page header
- **Expected Result**: Page loads without error. Heading "AI Coach" is visible. Subtext "Get a personalized workout recommendation powered by your training history and the knowledge graph." is visible.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-002: Nav link "AI Coach" is present and navigates to /knowledge-graph
- **Page**: Any authenticated page (e.g., `http://localhost:5173/workouts`)
- **Description**: Verify the "AI Coach" nav link appears in the AppShell navigation and routes to `/knowledge-graph`.
- **Steps**:
  1. Navigate to any authenticated page (e.g., `/workouts`)
  2. Locate the navigation bar/sidebar
  3. Click the "AI Coach" link
- **Expected Result**: Navigation link labeled "AI Coach" is visible in the nav. Clicking it navigates to `http://localhost:5173/knowledge-graph`.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-003: Query form is present with correct elements
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify the form has a textarea input and a submit button with the correct labels.
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Inspect the form area
- **Expected Result**: Label "What are your goals or constraints today?" is visible. A multi-line textarea is present. A button labeled "Get Recommendation" is visible and initially enabled.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-004: Submit button is disabled when textarea is empty
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify the submit button is disabled when the query textarea is blank.
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Ensure the textarea is empty (clear it if needed)
  3. Observe the "Get Recommendation" button state
- **Expected Result**: The "Get Recommendation" button is disabled (cannot be clicked).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-005: Loading state renders skeleton cards while request is in flight
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that while the recommendation request is pending, loading skeleton placeholders are shown.
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Type a query in the textarea (e.g., "upper body strength")
  3. Click "Get Recommendation" and immediately observe the UI before the response arrives (throttle network in DevTools if needed to extend loading time)
- **Expected Result**: Button text changes to "Generating…" and button becomes disabled. Three skeleton placeholder cards appear below the form while the request is in flight.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-006: Error state displays error banner on API failure
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that when the API returns an error, an error banner is shown.
- **Steps**:
  1. Stop the backend server (or use DevTools to block the `/api/kg/recommend` request)
  2. Navigate to `http://localhost:5173/knowledge-graph`
  3. Enter a query and click "Get Recommendation"
  4. Observe the UI after the request fails
- **Expected Result**: An error banner appears containing "Error:" followed by a failure message. No skeleton cards remain. The form is still available to re-submit.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-007: Successful response renders exercise cards with name, sets/reps, and reasoning
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that a successful recommendation response renders one card per exercise showing exercise name, sets × reps or duration, and reasoning text.
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Enter a query (e.g., "upper body strength workout, 45 minutes") and click "Get Recommendation"
  3. Wait for the response to load
  4. Observe the rendered exercise cards
- **Expected Result**: A list of exercise cards appears. Each card shows the exercise name (bold), a badge with sets × reps (e.g., "3 × 10 reps") or duration (e.g., "3 × 30s"), and reasoning text below the name. A heading "Recommended Exercises (N)" is shown above the cards.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

### UAT-UI-008: Fallback notice appears when fallback_used is true
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that when the backend returns `fallback_used: true`, the fallback notice "Limited options due to injury constraints." is displayed.
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Submit a query for a member profile that has many injury constraints (use a member_id for a synthetic member with known injuries, or mock the response in DevTools Network tab to include `"fallback_used": true`)
  3. Observe the results area
- **Expected Result**: A notice reading "Limited options due to injury constraints." appears above the exercise cards when `fallback_used` is `true` in the response.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-06 -->

---

## Edge Case Tests

### UAT-EDGE-001: Unauthenticated user is redirected away from /knowledge-graph
- **Scenario**: A logged-out user navigates directly to `/knowledge-graph`
- **Steps**:
  1. Clear all session cookies/tokens (log out or open a private window)
  2. Navigate directly to `http://localhost:5173/knowledge-graph`
- **Expected Result**: User is redirected to the login page (`/login`) and does not see the KnowledgeGraphPage content.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

### UAT-EDGE-002: Empty recommendation list shows empty state message
- **Scenario**: API returns `exercises: []` (no recommendations)
- **Steps**:
  1. Navigate to `http://localhost:5173/knowledge-graph`
  2. Intercept the `/api/kg/recommend` response via DevTools and replace the body with `{"member_id":"<uuid>","exercises":[],"overall_reasoning":"","skipped_exercise_ids":[],"fallback_used":false}`
  3. Submit any query and observe the results
- **Expected Result**: The message "No recommendations found. Try a different query." appears and no exercise cards are rendered.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Full end-to-end flow — query to displayed recommendation
- **Components**: Frontend form → `useKGRecommend` hook → Axios POST `/api/kg/recommend` → Vite proxy → FastAPI `/kg/recommend` → retrieval graph → generation graph → KGRecommendResponse → exercise cards rendered
- **Flow**: Authenticated user enters a query, submits the form, receives and views a personalized recommendation.
- **Steps**:
  1. Ensure backend (port 8000) and frontend (port 5173) are both running with Neo4j reachable
  2. Log into the app at `http://localhost:5173`
  3. Click the "AI Coach" nav link
  4. Type "I want a lower body workout, no knee pain" in the textarea
  5. Click "Get Recommendation"
  6. Observe the loading skeletons appear
  7. Wait for the response (may take 5–15 seconds due to LLM generation)
  8. Observe the exercise cards
- **Expected Result**: Loading skeletons appear immediately after submit. Within ~15 seconds, exercise cards appear showing at least one recommended exercise with name, sets/reps or duration, and reasoning text. No error banner appears.
- [FAIL: auto-judge: manual test requires human verification] <!-- 2026-06-06 -->

---

## Notes

- UAT-UI-008 (fallback notice) may be difficult to trigger without a synthetic member with many injury constraints. Use DevTools network interception to mock `"fallback_used": true` in the response if no such member exists in the test environment.
- UAT-UI-006 (error state) is easiest to test by blocking the network request in DevTools or stopping the backend server temporarily.
