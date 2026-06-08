# 098 — Session Duration / Time-Window Field (New Workout)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [095-coach-chat-image-support](095-coach-chat-image-support.md), [096-coach-message-charts](096-coach-message-charts.md), [097-coach-member-switcher](097-coach-member-switcher.md)

## Objective

Add a structured session-duration / time-window control to the New Workout page so the coach supplies a prompt **and** an explicit time window, instead of having to state the duration as free text in chat.

## Approach

Add a duration selector (e.g. 15 / 30 / 45 / 60 min chips, or a numeric `ww-input` select) to the chat composer in `WorkoutNewPage.tsx`. Since the backend `/api/chat/` `ChatRequest` schema accepts only `message` + `session_id` (no duration field), the chosen duration is **injected into the prompt text** at send time (in `WorkoutNewPage.tsx` before calling `sendMessage`, e.g. prefixing `"Time window: <N> minutes. "`). This keeps the generator unchanged — it already parses duration from the free-text prompt — while giving the coach a deterministic structured input.

## Prerequisites

- [x] Confirmed the chat request shape: `useChat().sendMessage(text)` POSTs `{ message, session_id }` to `/api/chat/`; backend `ChatRequest` (`backend/app/schemas/chat.py`) has no duration field.
- [x] Confirmed both send paths in `WorkoutNewPage.tsx` route through `sendMessage`: the composer `handleSend` and the `WORKOUT_CHIPS` quick-action buttons.
- [x] Reviewed the Workout Wiz ember design system (inline styles with `var(--space-*)` / `var(--text-*)` tokens and `ww-card` / `ww-input` / `ww-btn ww-btn--outline ww-btn--sm` classes) so the new control matches existing composer styling.

---

## Steps

### 1. Duration control  <!-- agent: general-purpose -->

- [x] In `WorkoutNewPage.tsx`, add a `duration` state value (default e.g. `30`) alongside the existing `inputText` state.
- [x] Render a duration selector in the composer (above the textarea / near `WORKOUT_CHIPS`): either toggle chips for 15 / 30 / 45 / 60 min using `ww-btn ww-btn--outline ww-btn--sm` (active state via `ww-btn--gradient`), or a `ww-input` `<select>`; label it clearly (e.g. "Session length").
- [x] Style the control with the ember design tokens (`var(--space-*)`, `var(--text-*)`) consistent with the surrounding composer; do not hardcode colors/spacing.

### 2. Wire into request  <!-- agent: general-purpose -->

- [x] In `WorkoutNewPage.tsx`, thread the selected `duration` into the prompt for **both** send paths (`handleSend` and the `WORKOUT_CHIPS` `onClick`) — e.g. build the outgoing string as `` `Time window: ${duration} minutes. ${text}` `` before calling `void sendMessage(...)`.
- [x] Keep the user-visible composer text unchanged; only the message passed to `sendMessage` carries the injected duration (confirm `useChat`/`useDraftWorkout` need no signature changes — the duration travels inside `message`).

### 3. Verification  <!-- agent: general-purpose -->

- [x] `cd frontend && npm run build` passes; selecting a duration and sending (via composer or a quick-action chip) produces a chat message whose text includes the chosen time window, and the generated workout reflects that duration. <!-- Pre-existing type errors in useDraftWorkout.ts + CoachPage.tsx (unrelated to this task); WorkoutNewPage.tsx changes are type-clean. -->

## Acceptance Criteria

- [x] The New Workout page shows an explicit, structured session-duration / time-window control next to the chat prompt (no longer requiring the user to type the duration as free text).
- [x] The selected duration is included in the message sent to `/api/chat/` for both the composer and the quick-action chips.
- [x] No backend changes are required; the generator receives the duration via the prompt text.
- [x] The control matches the Workout Wiz ember design system (token-based styling, `ww-*` classes); `cd frontend && npm run build` passes.

---
**UAT**: [`.docs/uat/098-workout-duration-field.uat.md`](../uat/098-workout-duration-field.uat.md)
