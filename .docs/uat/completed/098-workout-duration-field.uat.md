# UAT: Session Duration / Time-Window Field (New Workout)

> **Source task**: [`.docs/tasks/098-workout-duration-field.md`](../tasks/098-workout-duration-field.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Frontend dev server running at `http://localhost:5173` (or `npm run dev` in `frontend/`)
- [ ] Backend server running at `http://localhost:8000`
- [ ] Logged-in session — navigate to `/login` and authenticate before running UI tests

---

## UI Tests

### UAT-UI-001: Session length selector is visible on New Workout page
- **Page**: `/workouts/new`
- **Description**: Verify the "Session length" label and four duration chips (15 min, 30 min, 45 min, 60 min) are rendered in the composer area.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Scroll to the composer section at the bottom of the Coach panel (below "Exclude exercises" and "Available equipment")
  3. Observe the row above the quick-action chips
- **Expected Result**: A label reading "Session length" is visible alongside four buttons labelled "15 min", "30 min", "45 min", and "60 min". The "30 min" button has the gradient/active styling (it is the default selection).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-002: Default duration is 30 minutes
- **Page**: `/workouts/new`
- **Description**: Verify the default selected duration is 30 min on page load.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new` (fresh load, no prior state)
  2. Locate the Session length chip row
  3. Inspect which chip has the `ww-btn--gradient` class / active visual styling
- **Expected Result**: The "30 min" chip has active/gradient styling; "15 min", "45 min", and "60 min" chips are in their default outline state.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-003: Clicking a duration chip changes selection
- **Page**: `/workouts/new`
- **Description**: Verify clicking a different chip updates the active selection and removes gradient from the previously active chip.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Confirm "30 min" is the active chip
  3. Click the "45 min" chip
- **Expected Result**: "45 min" now has gradient/active styling. "30 min" reverts to outline styling. All other chips remain in outline state.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-004: Duration is injected into composer send
- **Page**: `/workouts/new`
- **Description**: Verify the selected duration is prepended to the message sent when using the text composer.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Select the "45 min" chip (so duration = 45)
  3. Open browser DevTools → Network tab, filter by `/api/chat/`
  4. Type "Upper body strength" in the textarea
  5. Click "Send"
- **Expected Result**: The POST request body contains `"message": "Time window: 45 minutes. Upper body strength"`. The user-visible textarea is cleared after send; the coach message stream shows the user text (which may include the time window prefix since `useChat` echoes the trimmed text as the user bubble).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-005: Duration is injected via quick-action chips
- **Page**: `/workouts/new`
- **Description**: Verify the selected duration is also prepended when sending via the WORKOUT_CHIPS quick-action buttons.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Select the "15 min" chip in the Session length row
  3. Open browser DevTools → Network tab, filter by `/api/chat/`
  4. Click the "Lower body" quick-action chip
- **Expected Result**: The POST request body contains `"message": "Time window: 15 minutes. Lower body"`. No text appears in the textarea (it is cleared before dispatch).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-006: Cycling through all four duration options
- **Page**: `/workouts/new`
- **Description**: Verify each of the four chips (15, 30, 45, 60 min) can be selected and each becomes the sole active chip.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Click "15 min" — confirm it is active, others are not
  3. Click "60 min" — confirm it is active, others are not
  4. Click "30 min" — confirm it returns to default active state, others are not
- **Expected Result**: At each step, exactly one chip has gradient/active styling corresponding to the clicked duration.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-007: Duration selector uses design-system tokens (no hardcoded colors)
- **Page**: `/workouts/new`
- **Description**: Verify the Session length row uses `ww-btn` classes and CSS token-based styling consistent with the rest of the composer.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Open DevTools → Elements, inspect the "30 min" button
  3. Confirm it has class `ww-btn ww-btn--outline ww-btn--sm ww-btn--gradient` (active) or `ww-btn ww-btn--outline ww-btn--sm` (inactive)
  4. Confirm no `color`, `background`, or `border-color` inline style properties are hardcoded with hex/rgb values
- **Expected Result**: Duration chips use only `ww-btn` CSS classes and `var(--...)` token-based inline styles (e.g. `font-size: var(--text-xs)`, `font-weight: var(--weight-semibold)`). No hardcoded color values appear in the inline style.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: Duration flows through to backend chat request
- **Components**: `WorkoutNewPage` → `dispatchMessage` → `useChat.sendMessage` → `POST /api/chat/`
- **Flow**: Select a non-default duration, type a prompt, send — confirm the backend receives the prefixed message.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Select "60 min" from the Session length chips
  3. Open DevTools → Network tab
  4. Type "Full body HIIT" in the textarea and click "Send"
  5. In the Network tab, open the `/api/chat/` request payload
- **Expected Result**: The request body is `{"message": "Time window: 60 minutes. Full body HIIT", "session_id": "<uuid>"}`. The backend responds and an assistant message appears in the chat stream. No duration field exists at the top level of the JSON body (duration travels inside `message` only).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-INT-002: Duration persists across multiple sends within same session
- **Components**: `WorkoutNewPage` duration state → multiple `dispatchMessage` calls
- **Flow**: Select a duration, send two messages, verify both carry the same duration prefix.
- **Steps**:
  1. Navigate to `http://localhost:5173/workouts/new`
  2. Select "45 min"
  3. Open DevTools → Network tab
  4. Send "Warm up exercises" via the composer
  5. Send "Add a cooldown" via the composer
- **Expected Result**: Both POST requests to `/api/chat/` contain `"message": "Time window: 45 minutes. ..."` with their respective text appended. The selected chip remains "45 min" (state does not reset between sends).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->
