# 095 — Image Upload & Display in Coach Copilot Chat

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [094-workout-exclusion-filter-ui](094-workout-exclusion-filter-ui.md), [098-workout-duration-field](098-workout-duration-field.md)

## Objective

Let a coach attach an image to a Coach Copilot chat message and have that image render inside the conversation bubble and remain visible in the in-session chat history.

## Approach

Add an optional `image` field (data URL string) to `CoachChatMessage` so the user-message object carries the attachment, add an image picker to the composer in `CoachPage.tsx` (wired through `useCoachChat.ts`), and render an `<img>` inside `ChatBubble` whenever a message carries an image. MVP scope is **client-side**: the backend `/coach/chat` endpoint is stateless (it does not store or echo prior turns — see `coach_chat` in `backend/app/routers/coach.py`), so the image lives in the hook's in-memory `messages` state and persists naturally for the session; the backend `CoachChatRequest`/`CoachChatResponse` schemas in `backend/app/schemas/coach.py` get an optional `image` field so the request contract can carry the data URL without breaking validation (no DB persistence, no multimodal LLM call in this task).

## Prerequisites

- [ ] Confirm current chat symbols are unchanged: `CoachChatMessage` (`frontend/src/types/index.ts` ~L148), `ChatBubbleProps`/`ChatBubble` (`frontend/src/components/ChatBubble.tsx`), `useCoachChat` (`frontend/src/hooks/useCoachChat.ts`), `CoachPage` composer (`frontend/src/pages/CoachPage.tsx`), and `CoachChatRequest`/`CoachChatResponse` (`backend/app/schemas/coach.py`).
- [ ] Apply the Workout Wiz ember/brand design system to all new UI: reuse existing CSS tokens (`var(--space-*)`, `var(--card)`, `var(--border)`, `var(--muted-foreground)`) and brand button classes (`ww-btn`, `ww-btn--ghost`, `ww-btn--sm`) already used by the composer — no hardcoded colors or spacing.

---

## Steps

### 1. Add image field to chat message + request/response schemas  <!-- agent: general-purpose -->

- [ ] In `frontend/src/types/index.ts`, add an optional `image?: string` (data URL) field to the `CoachChatMessage` interface.
- [ ] In `backend/app/schemas/coach.py`, add an optional `image: str | None = None` field to `CoachChatRequest` so the request contract accepts a data URL (kept for forward-compatibility; not persisted or sent to the LLM in this task).
- [ ] In `backend/app/schemas/coach.py`, add an optional `image: str | None = None` field to `CoachChatResponse` so the contract can echo an image if a later task makes chat stateful (leave unset by `coach_chat` for now).

### 2. Add an image-attach control to the composer  <!-- agent: general-purpose -->

- [ ] In `frontend/src/pages/CoachPage.tsx`, add a hidden `<input type="file" accept="image/*">` plus a brand-styled trigger button (`ww-btn ww-btn--ghost ww-btn--sm`) in the composer input row, read the selected file as a data URL (`FileReader.readAsDataURL`), hold it in a `pendingImage` state, and show a small removable thumbnail preview above/beside the textarea using brand tokens.
- [ ] In `frontend/src/pages/CoachPage.tsx`, update `handleSend` to pass the pending image to the send call and clear `pendingImage` after sending; allow sending an image even when the text draft is empty (adjust the Send-button `disabled` guard accordingly).
- [ ] In `frontend/src/hooks/useCoachChat.ts`, update `sendMessage` to accept an optional `image` argument, attach it to the constructed user `CoachChatMessage`, include it in the POST body to `/api/coach/chat`, and keep the existing optimistic-add / error-rollback behavior intact.

### 3. Render images in chat bubbles (including history)  <!-- agent: general-purpose -->

- [ ] In `frontend/src/components/ChatBubble.tsx`, add an optional `image?: string` prop to `ChatBubbleProps` and render an `<img>` (constrained max-width/height, rounded corners via brand tokens, with `alt` text) inside `ww-chat__bubble` when `image` is present, alongside the existing text content.
- [ ] In `frontend/src/pages/CoachPage.tsx`, pass `msg.image` into `<ChatBubble>` inside the `messages.map(...)` render so attached images appear for both freshly sent messages and earlier messages in the scrollback history.

### 4. Verification  <!-- agent: general-purpose -->

- [ ] `cd frontend && npm run build` passes with no type errors.
- [ ] Manually attaching an image in the Coach Copilot composer shows a preview, the image renders in its chat bubble after Send, and it stays visible in the conversation history after subsequent messages.

## Acceptance Criteria

- [ ] `CoachChatMessage` carries an optional image data URL, and `CoachChatRequest`/`CoachChatResponse` expose an optional `image` field without breaking existing requests.
- [ ] The composer in `CoachPage.tsx` has a brand-styled image picker with a removable preview, and an image can be sent with or without accompanying text.
- [ ] `ChatBubble` renders an attached image inside the bubble, and images remain visible in the scrollback history for the session.
- [ ] All new UI uses Workout Wiz design tokens/classes (no hardcoded colors or spacing); `npm run build` passes.
