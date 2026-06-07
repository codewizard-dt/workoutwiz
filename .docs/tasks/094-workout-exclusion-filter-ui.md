# 094 — Interactive Exercise-Exclusion & Equipment-Filter Controls (New Workout)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [095-coach-chat-image-support](095-coach-chat-image-support.md), [096-coach-message-charts](096-coach-message-charts.md), [097-coach-member-switcher](097-coach-member-switcher.md)

## Objective

Give the New Workout page explicit UI controls — an exclude-exercises multi-select and an available-equipment filter — whose selections are injected into the generation request so a coach can constrain the draft (no deadlifts, dumbbells-only, etc.) without typing free-text, satisfying the `candidate-assessment-main` "interactive adjustment driven by the graph" requirement.

## Approach

Add a compact constraints panel to `frontend/src/pages/WorkoutNewPage.tsx` (or a small new `frontend/src/components/` component) holding two controls: an "Exclude exercises" multi-select (chip toggles backed by `useExercises()` data, tracked by exercise name + id) and an "Available equipment" filter (chip toggles over the distinct `equipment_required` values). On Send / quick-chip, the active selections are formatted into a short natural-language constraint preamble and prepended to the message string passed to `useChat().sendMessage(...)`, since `/api/chat/` accepts only a free-text `message` — keeping this change frontend-only while the generator graph honours the constraint via the existing prompt path. State lives in local `useState` (no new global store).

## Prerequisites

- [ ] Read `frontend/src/pages/WorkoutNewPage.tsx` — note it already pulls `exercises` from `useExercises()`, drives chat via `useChat()` (`sendMessage`, `chatLoading`), and renders the `WORKOUT_CHIPS` quick-action buttons (lines ~10-15) and the composer textarea + Send button; the existing `handleSend()` calls `void sendMessage(inputText.trim())` and quick chips call `void sendMessage(text)`.
- [ ] Read `frontend/src/hooks/useChat.ts` — confirm `sendMessage(text: string)` is the single entry point and the POST body is `{ message: trimmed, session_id: sessionId }` (no structured constraints field exists today), so constraints must be embedded into the `text` argument.
- [ ] Read `frontend/src/types/index.ts` `Exercise` interface — fields available for the controls are `id`, `name`, `equipment_required: string[]`, `muscle_groups`, `priority_tier`.
- [ ] Read the brand design reference at `frontend/design-system/` (the design-system readme/tokens) — chips and panels MUST reuse existing brand classes (`ww-card`, `ww-btn`, `ww-btn--outline`, `ww-btn--sm`) and CSS tokens (`var(--space-*)`, `var(--text-*)`, `var(--border)`); do not introduce hardcoded colors/spacing. The `workout-wiz-brand-design` skill auto-triggers when this route file is edited — follow its guidance.

---

## Steps

### 1. Build the constraints controls (multi-select + equipment filter)  <!-- agent: general-purpose -->

- [ ] In `frontend/src/pages/WorkoutNewPage.tsx` (or a new `frontend/src/components/WorkoutConstraints.tsx` that the page imports and re-exports via `frontend/src/components/index.ts`), add a constraints panel rendered above or within the Coach chat card's composer area.
- [ ] Add local state in `WorkoutNewPage`: `const [excludedIds, setExcludedIds] = useState<string[]>([])` and `const [allowedEquipment, setAllowedEquipment] = useState<string[]>([])` (empty = no equipment restriction).
- [ ] Render an "Exclude exercises" control as a toggle-chip list derived from `exercises` (use the same chip styling as the existing `WORKOUT_CHIPS` buttons: `ww-btn ww-btn--outline ww-btn--sm`, with an active/selected visual state when an id is in `excludedIds`). Clicking a chip toggles its `id` in `excludedIds`. For 50 exercises, keep it scrollable/wrappable; you may show a searchable/condensed list — match brand tokens, no raw `<select multiple>` styling.
- [ ] Render an "Available equipment" control as toggle chips over the distinct equipment values computed from the exercise data (e.g. `Array.from(new Set(exercises?.flatMap(e => e.equipment_required) ?? [])).sort()`); clicking toggles the value in `allowedEquipment`. Provide a clear/reset affordance for each control.

### 2. Thread constraints into the generation request  <!-- agent: general-purpose -->

- [ ] Add a helper in `WorkoutNewPage.tsx` (e.g. `buildConstraintPreamble(): string`) that turns the active selections into a concise instruction string, e.g. `Exclude these exercises: <names>. Only use equipment: <equipment list>.` — resolve excluded ids to `name` via the `exercises` array, and omit a clause entirely when its selection is empty (no preamble when both are empty).
- [ ] Update the message-dispatch paths so the preamble is prepended to the user text before it reaches `sendMessage`: wrap both `handleSend()` and the `WORKOUT_CHIPS` chip `onClick` (and the textarea Enter handler `handleKeyDown` path) to send `[preamble, userText].filter(Boolean).join(' ')` instead of the bare text. The visible user bubble may show just the typed text; the constraint preamble only needs to reach the backend prompt — keep the implementation simple (do not add a new request field to `useChat`/`/api/chat/`).
- [ ] Ensure constraints persist across multiple sends in the session and are not auto-cleared on Send; clearing the draft via the existing Clear button should also reset `excludedIds` and `allowedEquipment`.

### 3. Types  <!-- agent: general-purpose -->

- [ ] Update `frontend/src/types/index.ts` only if a shared type is needed (e.g. a small `WorkoutGenerationConstraints` interface for the new component's props); otherwise no type change is required since `Exercise` already exposes `id`, `name`, and `equipment_required`. Do NOT add fields to the `/api/chat/` request shape.

### 4. Verification  <!-- agent: general-purpose -->

- [ ] `cd frontend && npm run build` passes (tsc + Vite) with no type errors.
- [ ] Manually (or via the existing UI) confirm: selecting exercises to exclude and generating produces a draft that does NOT contain the excluded exercises; selecting "dumbbell"-only equipment yields a draft whose exercises use only the allowed equipment; clearing the draft also clears both controls.

## Acceptance Criteria

- [ ] The New Workout page exposes non-chat UI controls to (a) exclude one or more specific exercises and (b) restrict generation to selected available equipment, before/while generating.
- [ ] Active selections are injected into the generation request (as a constraint preamble on the `sendMessage` text) so excluded exercises do not appear in the generated draft and only allowed equipment is used.
- [ ] Controls use the Workout Wiz brand design system (existing `ww-*` classes and CSS tokens), with no hardcoded colors/spacing; the implementer follows the `workout-wiz-brand-design` guidance.
- [ ] Selections persist across multiple generations in a session and are reset when the draft is cleared; empty selections add no preamble and leave existing behavior unchanged.
- [ ] `cd frontend && npm run build` passes with no TypeScript errors.
