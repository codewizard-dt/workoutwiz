# UAT: Feedback Submission UI

> **Source task**: [`.docs/tasks/071-feedback-submission-ui.md`](../tasks/071-feedback-submission-ui.md)
> **Generated**: 2026-06-06

---

## Prerequisites

- [ ] Backend server running at `http://localhost:8000`
- [ ] Frontend dev server running at `http://localhost:5173`
- [ ] PostgreSQL running and seeded with exercise data
- [ ] Neo4j running (required for `/kg/feedback` writes)
- [ ] `UAT_AUTH_TOKEN` env var set to a valid JWT for a registered user
- [ ] At least one exercise UUID known (any value from exercises table; placeholder `<exercise-uuid>` used below)
- [ ] Logged-in user's UUID known (placeholder `<member-uuid>` used below; use the `id` field from `GET /users/me`)

---

## API Tests

### UAT-API-001: Submit feedback with rating and text
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /kg/feedback`
- **Description**: Verify a valid feedback submission is persisted and returns `feedback_id` and success message.
- **Steps**:
  1. Substitute a real exercise UUID for `<exercise-uuid>` and a real member UUID for `<member-uuid>`.
  2. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":4,"text":"Great exercise, felt the burn"}' | jq '.'
  ```
- **Expected Result**: `200 OK` with `{"feedback_id": "<non-empty-string>", "message": "Feedback recorded successfully"}`
- [x] Pass <!-- 2026-06-07 -->

### UAT-API-002: Submit feedback with rating only (no text)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /kg/feedback`
- **Description**: Verify `text` is optional — omitting it still succeeds.
- **Steps**:
  1. Run the curl command below as-is (substitute real UUIDs).
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":5}' | jq '.'
  ```
- **Expected Result**: `200 OK` with `{"feedback_id": "<non-empty-string>", "message": "Feedback recorded successfully"}`
- [x] Pass <!-- 2026-06-07 -->

### UAT-API-003: Submit feedback with rating below minimum (validation)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /kg/feedback`
- **Description**: Verify that `rating: 0` is rejected — Pydantic schema enforces `ge=1`.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":0}' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity` with a validation error body indicating `rating` must be `>= 1`.
- [x] Pass <!-- 2026-06-07 -->

### UAT-API-004: Submit feedback with rating above maximum (validation)
- Auth-Required: true
- Auth-Role: user
- **Endpoint**: `POST /kg/feedback`
- **Description**: Verify that `rating: 6` is rejected — Pydantic schema enforces `le=5`.
- **Steps**:
  1. Run the curl command below as-is.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":6}' | jq '.'
  ```
- **Expected Result**: `422 Unprocessable Entity` with a validation error body indicating `rating` must be `<= 5`.
- [x] Pass <!-- 2026-06-07 -->

### UAT-API-005: Submit feedback without authentication
- Auth-Required: false
- **Endpoint**: `POST /kg/feedback`
- **Description**: Verify that the endpoint rejects unauthenticated requests.
- **Steps**:
  1. Run the curl command below without an Authorization header.
- **Command**:
  ```bash
  curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":3}' | jq '.'
  ```
- **Expected Result**: `401 Unauthorized`
- [x] Pass <!-- 2026-06-07 -->

---

## UI Tests

### UAT-UI-001: FeedbackForm renders per exercise after recommendation
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that after a workout recommendation is returned, a `FeedbackForm` appears for each exercise in the list.
- **Steps**:
  1. Log in and navigate to `http://localhost:5173/knowledge-graph`.
  2. In the textarea labelled "What are your goals or constraints today?", type `Upper body strength, 30 minutes`.
  3. Click the "Get Recommendation" button and wait for results to load.
  4. Observe the exercise cards returned in "Recommended Exercises".
  5. Verify that each exercise card contains a section labelled "Rate this exercise" with 5 star buttons and a textarea with placeholder "Optional feedback…".
- **Expected Result**: Every exercise card in the recommendation list has a "Rate this exercise" section with 5 star (★) buttons and an "Optional feedback…" textarea.
- [ ] Pass

### UAT-UI-002: Submit button disabled until star is selected
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify the Submit Feedback button is disabled when no star rating is selected.
- **Steps**:
  1. Log in and navigate to `http://localhost:5173/knowledge-graph`.
  2. Trigger a recommendation (as in UAT-UI-001).
  3. Locate the first `FeedbackForm` in the results — do NOT click any star.
  4. Observe the "Submit Feedback" button.
- **Expected Result**: The "Submit Feedback" button is visually disabled (has `disabled` attribute) when no rating is selected, even if text is entered in the textarea.
- [ ] Pass

### UAT-UI-003: Star rating selection highlights selected star and below
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that clicking star 3 highlights stars 1, 2, and 3 (the selected star and all below it).
- **Steps**:
  1. Log in, navigate to `/knowledge-graph`, and trigger a recommendation.
  2. Locate the first `FeedbackForm`.
  3. Click the star button labelled "Rate 3 out of 5" (third star).
  4. Observe the visual state of all 5 stars.
- **Expected Result**: Stars 1, 2, and 3 appear accented/highlighted (full opacity, `ww-btn--accent` class applied); stars 4 and 5 appear dimmed (40% opacity).
- [ ] Pass

### UAT-UI-004: Successful submission shows "Thank you for your feedback!"
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify that after a successful POST, the form is replaced by a success message.
- **Steps**:
  1. Log in, navigate to `/knowledge-graph`, and trigger a recommendation.
  2. In the first `FeedbackForm`, click any star to select a rating.
  3. Optionally type text in the "Optional feedback…" textarea.
  4. Click "Submit Feedback".
  5. Wait for the request to complete.
- **Expected Result**: The form is replaced by the text "Thank you for your feedback!" (rendered in the success color). The star buttons and textarea are no longer visible.
- [ ] Pass

### UAT-UI-005: Submit button shows "Submitting…" during pending state
- **Page**: `http://localhost:5173/knowledge-graph`
- **Description**: Verify the button label changes while the mutation is in flight.
- **Steps**:
  1. Log in, navigate to `/knowledge-graph`, and trigger a recommendation.
  2. Select a star rating in the first `FeedbackForm`.
  3. Click "Submit Feedback" and immediately observe the button label before the response arrives (use network throttling if needed).
- **Expected Result**: While the POST is pending, the button label reads "Submitting…" and is disabled. After the response, it transitions to the success state.
- [ ] Pass

---

## Edge Case Tests

### UAT-EDGE-001: Feedback form error state when API returns 500
- **Scenario**: Backend returns an HTTP 500 for the feedback POST (e.g., Neo4j unavailable).
- **Steps**:
  1. Stop the Neo4j service (or point the backend at an invalid Neo4j URI).
  2. Log in, navigate to `/knowledge-graph`, trigger a recommendation.
  3. Select a star in the first `FeedbackForm` and click "Submit Feedback".
- **Expected Result**: An inline error message appears below the stars: either the API's error message or "Submission failed. Please try again." The form remains visible (not replaced by the success message). The "Submit Feedback" button is re-enabled after the error.
- [ ] Pass

### UAT-EDGE-002: `useKGFeedback` hook exported from hooks index
- **Scenario**: Ensure the hook is importable from the barrel index.
- **Steps**:
  1. In the project root, run: `grep -r "useKGFeedback" frontend/src/hooks/index.ts`
- **Expected Result**: Output contains `export` and `useKGFeedback`, confirming the hook is re-exported from the hooks index barrel.
- [x] Pass <!-- 2026-06-06 -->

---

## Integration Tests

### UAT-INT-001: Full feedback flow — recommend then rate an exercise
- **Components**: `KnowledgeGraphPage` → `FeedbackForm` → `useKGFeedback` hook → `POST /kg/feedback` → Neo4j
- **Flow**: User gets a workout recommendation, selects a star rating for one exercise, submits feedback, and sees a confirmation.
- **Steps**:
  1. Log in and navigate to `http://localhost:5173/knowledge-graph`.
  2. Enter a query (e.g., "Lower body, 20 minutes") and click "Get Recommendation".
  3. Once exercises appear, locate any exercise card that has a "Rate this exercise" section.
  4. Click the 5-star button ("Rate 5 out of 5").
  5. Type "Excellent recommendation" in the "Optional feedback…" textarea.
  6. Click "Submit Feedback".
  7. After submission, verify the success state in the UI.
  8. Confirm the feedback was written to Neo4j by running:
     ```bash
     curl -sS -X POST 'http://localhost:8000/kg/feedback' -H 'Content-Type: application/json' -H "Authorization: Bearer $UAT_AUTH_TOKEN" -d '{"member_id":"<member-uuid>","exercise_id":"<exercise-uuid>","rating":5,"text":"Excellent recommendation"}' | jq '.feedback_id'
     ```
- **Expected Result**: UI shows "Thank you for your feedback!". The curl command in step 8 returns a non-null `feedback_id` string, confirming the Neo4j write path works end-to-end.
- [ ] Pass
