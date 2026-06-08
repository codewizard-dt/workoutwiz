# UAT: Interactive Exercise-Exclusion & Equipment-Filter Controls (New Workout)

> **Source task**: [`.docs/tasks/094-workout-exclusion-filter-ui.md`](../tasks/094-workout-exclusion-filter-ui.md)
> **Generated**: 2026-06-08

---

## Prerequisites

- [ ] Frontend dev server running (`cd frontend && npm run dev` or `make dev-frontend`)
- [ ] Backend server running (exercises endpoint must respond)
- [ ] Navigate to `http://localhost:5173` and sign in so the New Workout page is accessible
- [ ] Open `http://localhost:5173/workouts/new` — confirm the page loads with the "Coach" chat panel visible

---

## UI Tests

### UAT-UI-001: Constraints panel renders with "Exclude exercises" section
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify the constraints panel is present and the "Exclude exercises" label and exercise chip list are rendered above the composer.
- **Steps**:
  1. Navigate to `/workouts/new`
  2. Wait for the exercise chips to load (they are fetched from the backend)
  3. Locate the section labelled **"Exclude exercises"** above the quick-action chips area
  4. Confirm a scrollable list of chip-style buttons is visible, each labelled with an exercise name (e.g. "Barbell Back Squat", "Deadlift", "Push-Up", etc.)
- **Expected Result**: The "Exclude exercises" label is present. At least one exercise name chip (styled `ww-btn ww-btn--outline ww-btn--sm`) is visible. No raw `<select multiple>` element is used.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-002: Constraints panel renders with "Available equipment" section
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify the "Available equipment" control renders distinct equipment chips derived from exercise data.
- **Steps**:
  1. Navigate to `/workouts/new`
  2. Wait for exercises to load
  3. Locate the section labelled **"Available equipment (all)"** (the `(all)` suffix appears when no equipment is selected)
  4. Confirm chip buttons appear for distinct equipment values (e.g. "barbell", "dumbbell", "bodyweight", etc.)
- **Expected Result**: The label "Available equipment (all)" is present. At least two distinct equipment chips are visible. No raw `<select>` element is used.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-003: Clicking an exercise chip marks it as excluded (visual active state)
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that clicking an exercise chip toggles its excluded/active state visually (strikethrough text, red border/color, `ww-btn--active` class).
- **Steps**:
  1. Navigate to `/workouts/new`
  2. Wait for exercise chips to load
  3. Click one exercise chip (e.g. "Push-Up")
  4. Observe the chip's visual state after the click
- **Expected Result**: The clicked chip gains a line-through text decoration and red-tinted border/color (reflecting the `borderColor: var(--destructive)` and `textDecoration: 'line-through'` styles). The chip has the class `ww-btn--active` added.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-004: Clicking an excluded exercise chip again deselects it
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify the excluded exercise chip is a toggle — a second click removes it from the exclusion list.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click "Push-Up" chip once (it becomes excluded/active)
  3. Click "Push-Up" chip again
  4. Observe the chip's visual state after the second click
- **Expected Result**: The chip returns to its default, non-excluded appearance (no strikethrough, no red styling, opacity back to 0.7, `ww-btn--active` class removed).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-005: "Clear (N)" button appears when exercises are excluded and resets the list
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that a "Clear (N)" button appears in the "Exclude exercises" section header when one or more exercises are selected, and clicking it clears all exclusions.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click two or three exercise chips to exclude them (e.g. "Push-Up", "Deadlift")
  3. Observe the "Exclude exercises" section header — confirm a button labelled "Clear (2)" (or matching count) appears
  4. Click the "Clear (2)" button
  5. Observe the chips after clearing
- **Expected Result**: After step 3 a "Clear (N)" button appears (N = number of excluded exercises). After step 4 all chips return to their default non-excluded visual state and the "Clear" button disappears.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-006: Clicking an equipment chip marks it as selected (active state)
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify clicking an equipment chip highlights it as selected (primary background color, `ww-btn--active` class).
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click one equipment chip (e.g. "dumbbell")
  3. Observe the chip after the click
- **Expected Result**: The chip gains a primary-coloured background and foreground (reflecting `background: var(--primary)`, `color: var(--primary-foreground)`) and acquires the class `ww-btn--active`. The section label changes from "(all)" to "(1 selected)".
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-007: Equipment "Clear" button appears when equipment is selected and resets selection
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify the "Clear" button in the "Available equipment" section header appears when at least one equipment chip is active, and resets to "all" on click.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click "dumbbell" and "barbell" equipment chips
  3. Confirm label reads "Available equipment (2 selected)" and a "Clear" button appears
  4. Click the "Clear" button
- **Expected Result**: After step 4, all equipment chips return to default (no primary highlight, no `ww-btn--active`). The label returns to "Available equipment (all)". The "Clear" button disappears.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-008: Constraint preamble is prepended when Send is clicked
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that when exercises are excluded and/or equipment is restricted, the constraint preamble is included in the request sent to the backend (verifiable by observing the user bubble text or backend behaviour).
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click "Push-Up" in "Exclude exercises"
  3. Click "dumbbell" in "Available equipment"
  4. Type "30 minute upper body session" in the textarea
  5. Click **Send**
  6. Observe the user message bubble that appears in the chat stream
- **Expected Result**: The user bubble content contains the constraint preamble prepended to the typed text, producing a message that starts with "Exclude these exercises: Push-Up. Only use equipment: dumbbell." followed by " 30 minute upper body session". The coach's response should reflect the constraints (no push-ups, dumbbell exercises only).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-009: WORKOUT_CHIPS quick-action chips also prepend the constraint preamble
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that clicking a quick-action chip (e.g. "Upper body") while constraints are active sends the preamble + chip text to the backend.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Exclude one exercise (e.g. "Deadlift") by clicking its chip
  3. Click the quick-action chip **"Upper body"**
  4. Observe the user bubble that appears in the chat stream
- **Expected Result**: The user bubble content is "Exclude these exercises: Deadlift. Upper body" (preamble + chip text). The coach response should not include the excluded exercise.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-010: Constraints persist across multiple sends without being cleared
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that the active constraint selections remain active after sending a message (they do not reset on Send).
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click "Barbell Back Squat" in "Exclude exercises" and "barbell" in "Available equipment"
  3. Type "Push day" and click **Send**; wait for the coach's reply
  4. After the reply arrives, check the constraint chips — they should still be active
  5. Type "Make it harder" and click **Send** again
  6. Observe the second user bubble
- **Expected Result**: After step 3 the exclusion chip for "Barbell Back Squat" still shows its active/strikethrough style, and "barbell" equipment chip still shows its primary highlight. The second user bubble (step 6) also contains the constraint preamble, confirming constraints persist for the entire session.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-011: Clear draft button resets both constraint controls
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify the "Clear" button in the sequence panel (which clears the draft + messages) also resets `excludedIds` and `allowedEquipment` to empty.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Exclude one exercise and select one equipment chip
  3. Send any message (e.g. "Upper body") and click "✓ Use This Workout" on the generated draft so the sequence panel has data and the "Clear" button is visible
  4. Click the **Clear** button in the sequence panel footer
- **Expected Result**: After clicking Clear: (a) the draft sequence panel shows "Nothing yet — ask the coach to build a session.", (b) all exercise chips in "Exclude exercises" return to their default non-excluded appearance, (c) all equipment chips return to their default (no primary highlight), (d) the "Exclude exercises" section has no "Clear (N)" button, (e) the equipment label reads "(all)".
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-UI-012: Empty constraints add no preamble — existing behavior unchanged
- **Page**: `http://localhost:5173/workouts/new`
- **Description**: Verify that when no exercises are excluded and no equipment is restricted, sending a message does NOT prepend any constraint text — the message is passed through as-is.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Confirm no exercise chips are in their active/excluded state and no equipment chips are highlighted
  3. Type "Full body strength" and click **Send**
  4. Observe the user bubble that appears
- **Expected Result**: The user bubble contains exactly "Full body strength" with no preamble (no "Exclude these exercises:" or "Only use equipment:" prefix).
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Edge Case Tests

### UAT-EDGE-001: Equipment label shows correct count when multiple items are selected
- **Page**: `http://localhost:5173/workouts/new`
- **Scenario**: Label correctly reflects the selected count for 1, 2, and 3 equipment chips selected.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for equipment chips to load
  2. Click one equipment chip → confirm label reads "Available equipment (1 selected)"
  3. Click a second equipment chip → confirm label reads "Available equipment (2 selected)"
  4. Click a third equipment chip → confirm label reads "Available equipment (3 selected)"
- **Expected Result**: Label suffix updates accurately to `(N selected)` as each chip is toggled.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-EDGE-002: Exercise chips are scrollable when more than fit in the container
- **Page**: `http://localhost:5173/workouts/new`
- **Scenario**: The "Exclude exercises" chip list has a fixed max-height (80px) and should be scrollable for the full 50-exercise dataset.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for all exercise chips to load
  2. Hover over the chip list in the "Exclude exercises" section
  3. Scroll down within that container
- **Expected Result**: The chip list is scrollable (overflow-y: auto / scroll); exercises beyond the initial visible row are accessible by scrolling. The rest of the page does not scroll when the pointer is inside the chip list and all chips are within the contained scroll area.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

### UAT-EDGE-003: Preamble contains only exercise name (not id) for excluded exercises
- **Page**: `http://localhost:5173/workouts/new`
- **Scenario**: The `buildConstraintPreamble` function resolves exercise IDs to names. Verify the sent message uses human-readable names, not UUID strings.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. Click any exercise chip (e.g. "Deadlift")
  3. Type "test" and click **Send**
  4. Observe the user bubble in the chat stream
- **Expected Result**: The user bubble reads "Exclude these exercises: Deadlift. test" — the exercise name "Deadlift" appears, not a UUID.
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->

---

## Integration Tests

### UAT-INT-001: Full constraint-driven generation flow (exclude + equipment + send)
- **Page**: `http://localhost:5173/workouts/new`
- **Components**: `WorkoutNewPage` → `dispatchMessage` → `useChat.sendMessage` → `POST /api/chat/` → generation agent → workout draft response
- **Flow**: User sets constraints, sends a generation request, and verifies the resulting draft respects the constraints.
- **Steps**:
  1. Navigate to `/workouts/new`, wait for exercises to load
  2. In "Exclude exercises", click the chip for **"Barbell Back Squat"** and **"Deadlift"**
  3. In "Available equipment", click **"dumbbell"** only
  4. Type "30 minute lower body workout" in the textarea and click **Send**
  5. Wait for the assistant reply (the coach's response)
  6. If a "✓ Use This Workout" button appears, click it to load the draft into the sequence panel
  7. Inspect the sequence panel — review the exercise names listed in the draft
- **Expected Result**: 
  - The user bubble message starts with "Exclude these exercises: Barbell Back Squat, Deadlift. Only use equipment: dumbbell."
  - The generated draft (if produced) does NOT include "Barbell Back Squat" or "Deadlift"
  - The generated draft (if produced) only uses exercises that require dumbbell equipment
- [FAIL: auto-judge: UI test requires human verification — use /uat-walk] <!-- 2026-06-08 -->
