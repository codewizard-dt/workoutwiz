# 097 — Coach Member List & Switcher

> **Depends on**: [099-seed-multi-persona-context](099-seed-multi-persona-context.md)
> **Blocks**: none
> **Parallel-safe with**: [094-workout-exclusion-filter-ui](094-workout-exclusion-filter-ui.md), [098-workout-duration-field](098-workout-duration-field.md)

## Objective

Replace the Coach dashboard's hardcoded single-member view (Jordan Rivera) with a member list / switcher so the coach can select which member's brief and copilot chat to view.

## Approach

Add a `GET /coach/members` endpoint plus an optional `member_id` parameter on `/coach/brief` and `/coach/chat` (driven by a new id-based context lookup in `_fetch_member_context`), then add a brand-styled member selector to `CoachPage.tsx` whose selected member id flows through `useCoachBrief`/`useCoachChat` so switching reloads the brief and resets the chat for that member.

## Prerequisites

- [x] Task 099 (multi-persona context) provides multiple members with rich data to switch between
- [x] Confirm current coach symbols are unchanged: `_fetch_member_context`, `get_coach_brief`, `coach_chat`, `_neo4j_driver` (`backend/app/routers/coach.py`); `CoachBriefResponse`, `CoachChatRequest` (`backend/app/schemas/coach.py`); `useCoachBrief` (`frontend/src/hooks/useCoachBrief.ts`), `useCoachChat` (`frontend/src/hooks/useCoachChat.ts`), `CoachPage` (`frontend/src/pages/CoachPage.tsx`); `CoachBriefResponse`/`CoachChatResponse` (`frontend/src/types/index.ts` ~L135).
- [x] Apply the Workout Wiz ember/brand design system to all new UI: reuse existing CSS tokens (`var(--card)`, `var(--border)`, `var(--space-*)`, `var(--muted-foreground)`, `var(--accent)`) and brand classes (`ww-btn`, `ww-btn--ghost`, `ww-btn--sm`) already used on `CoachPage.tsx` — no hardcoded colors or spacing.

---

## Steps

### 1. Backend member list + `member_id` param  <!-- agent: general-purpose -->

- [x] In `backend/app/schemas/coach.py`, add a `CoachMemberSummary` model (`member_id: str`, `member_name: str`, `tier: str | None`, optional `member_age: int | None`) and a `CoachMembersResponse` (or use `list[CoachMemberSummary]` directly) for the member-list payload.
- [x] In `backend/app/routers/coach.py`, add a `GET /members` endpoint (auth via `current_active_user`) that opens a driver with `_neo4j_driver()`, runs a Cypher query (`MATCH (m:Member) ... RETURN m.id, m.display_name/name, m.tier, m.age`) returning all seeded members as `CoachMemberSummary` items, and closes the driver in a `finally` like the existing handlers.
- [x] In `backend/app/routers/coach.py`, update `_fetch_member_context` to look a member up by id when a `member_id` is provided (add a `member_id: str | None = None` arg and branch the `MATCH (m:Member {id: $member_id})` vs the existing `MATCH (m:Member {email: $email})` lookup) so both brief and chat can target a selected member.
- [x] In `backend/app/routers/coach.py`, add an optional `member_id: str | None = None` query parameter to `get_coach_brief` and pass it into `_fetch_member_context`; when omitted, fall back to the current `user.email` lookup so existing behavior is preserved.
- [x] In `backend/app/routers/coach.py`, add an optional `member_id: str | None = None` field to the chat request handling (via `CoachChatRequest` in `backend/app/schemas/coach.py`) and pass it into `_fetch_member_context` inside `coach_chat`, keeping the email fallback when unset.

### 2. Frontend member selector  <!-- agent: general-purpose -->

- [x] Add a `frontend/src/hooks/useCoachMembers.ts` hook (mirroring `useCoachBrief.ts`: `useQuery`, `apiFetch('/api/coach/members')`, bearer token, `enabled: !!token`) that returns the member list, and export it from `frontend/src/hooks/index.ts`.
- [x] In `frontend/src/hooks/useCoachBrief.ts`, accept a `memberId` argument, include it in the `queryKey` (e.g. `['coach', 'brief', memberId]`) and append it as a `?member_id=` query param on the `/api/coach/brief` request so each member gets its own cached brief.
- [x] In `frontend/src/hooks/useCoachChat.ts`, accept a `memberId` argument, include `member_id` in the POST body to `/api/coach/chat`, and reset chat state (`messages`, `sessionId`) when `memberId` changes so a switch starts a fresh conversation for the newly selected member.
- [x] In `frontend/src/pages/CoachPage.tsx`, add a `selectedMemberId` state, load members via `useCoachMembers`, default the selection to the first member once loaded, render a brand-styled selector (a `<select>` or a row of `ww-btn` chips using design tokens) in the page header, and pass `selectedMemberId` into `useCoachBrief(selectedMemberId)` and `useCoachChat(selectedMemberId)`.
- [x] In `frontend/src/pages/CoachPage.tsx`, replace the hardcoded "Jordan" copy in the chat empty-state and the textarea `placeholder` with the selected member's name from `brief?.member_name` (falling back to a neutral "your member").

### 3. Types  <!-- agent: general-purpose -->

- [x] In `frontend/src/types/index.ts`, add a `CoachMemberSummary` interface (`member_id: string`, `member_name: string`, `tier: string | null`, optional `member_age: number | null`) matching the backend list payload.
- [x] In `frontend/src/types/index.ts`, ensure the chat request type (and any shared coach request shape) carries an optional `member_id?: string`, and thread the `member_id` plumbing through the `useCoachChat`/`useCoachBrief` call sites so the selected id is type-checked end to end.

### 4. Verification  <!-- agent: general-purpose -->

- [x] `cd frontend && npm run build` passes with no type errors. <!-- Completed: 2026-06-08 -->
- [x] Switching members in the selector reloads the brief (member header, goals, adherence, injuries, churn risk) for that member and resets the copilot chat so it is grounded in the newly selected member's context. [DEFERRED-TO-UAT]

## Acceptance Criteria

- [x] `GET /coach/members` returns all seeded members (id, name, tier) and both `/coach/brief` and `/coach/chat` accept an optional `member_id`, falling back to the authenticated user's own member context when it is omitted.
- [x] `_fetch_member_context` resolves a member by id when `member_id` is supplied and by email otherwise.
- [x] `CoachPage.tsx` renders a brand-styled member switcher that drives `useCoachBrief`/`useCoachChat` by the selected member id; no member-specific copy (e.g. "Jordan") remains hardcoded.
- [x] Selecting a different member reloads that member's brief and starts a fresh, correctly-grounded copilot chat. [DEFERRED-TO-UAT]
- [x] All new UI uses Workout Wiz design tokens/classes (no hardcoded colors or spacing); `npm run build` passes.

---
**UAT**: [`.docs/uat/097-coach-member-switcher.uat.md`](../uat/097-coach-member-switcher.uat.md)
