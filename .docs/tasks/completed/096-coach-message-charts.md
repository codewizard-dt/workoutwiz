# 096 — Message-Pattern & 4-Week Comparison Charts (Coach Dashboard)

> **Depends on**: none
> **Blocks**: none
> **Parallel-safe with**: [094-workout-exclusion-filter-ui](094-workout-exclusion-filter-ui.md), [098-workout-duration-field](098-workout-duration-field.md)

## Objective

Add the two charts the `candidate-assessment-main` spec calls for but that are missing from the Coach dashboard — a message-pattern chart (member message volume/cadence over time) and a 4-week comparison chart — so the brief covers all three of "Plot adherence trend · Show message pattern · Compare last 4 weeks."

## Approach

Add Recharts to the frontend (the existing `AdherenceChart` is a hand-rolled single-series bar; a time-series message-pattern chart and a multi-series 4-week comparison are not worth hand-rolling, and the design system already ships `--chart-1`..`--chart-5` tokens for exactly this). Surface message-pattern and per-week comparison data in `CoachBriefResponse` (the graph already stores `ChatMessage` and `AssessmentWorkout` nodes, and `_fetch_member_context` already collects member `chat_messages` — the brief endpoint just does not expose them), then render two new chart components inside `CoachPage.tsx` styled with the ember/chart tokens.

## Prerequisites

- [ ] Neo4j seeded so the demo member (Jordan Rivera) has `ChatMessage` and `AssessmentWorkout` nodes (see `backend/app/knowledge_graph/seed.py`)
- [ ] Read the `workout-wiz-brand-design` guidance (auto-triggers on route edits) — charts must use design tokens, not hardcoded hex

---

## Steps

### 1. Chart library + brief data  <!-- agent: general-purpose -->

- [x] Add `recharts` to `frontend/package.json` dependencies and install
- [x] Extend `_fetch_member_context` in `backend/app/routers/coach.py` to also collect coach-side messages (the seed creates a `SENT_COACH_MESSAGE` relationship that the current query ignores), so message-pattern counts reflect both sides
- [x] Add `message_pattern` (per-day or per-week buckets: `date`/`week_of`, `member_count`, `coach_count`) and 4-week comparison metrics (per week: `week_of`, `adherence_pct`, `workouts_completed`, `messages_sent`) to `CoachBriefResponse` in `backend/app/schemas/coach.py`, derived in `get_coach_brief` from the `chat_messages`, `adherence`, and `workouts` context already fetched
- [x] Mirror the new fields in the `CoachBriefResponse` interface (plus any new sub-interfaces) in `frontend/src/types/index.ts`

### 2. Message-pattern chart  <!-- agent: general-purpose -->

- [x] Create a `MessagePatternChart` component in `frontend/src/components` that renders the Recharts time-series (bar or area) of member/coach message volume over time from `brief.message_pattern`, returning `null` when there is no data
- [x] Style with design tokens: series colors from `var(--chart-1)` / `var(--chart-2)`, axis/grid text in `var(--muted-foreground)`, spacing via `var(--space-*)`; match the existing card chrome used around `AdherenceChart`
- [x] Render it in `CoachPage.tsx` in its own titled card (e.g. "Message pattern"), consistent with the existing Adherence card layout

### 3. 4-week comparison chart  <!-- agent: general-purpose -->

- [x] Create a `WeeklyComparisonChart` component in `frontend/src/components` that renders a grouped/multi-series Recharts chart comparing the last 4 weeks (adherence %, workouts completed, messages sent) from the comparison data, returning `null` when fewer than 1 week is present
- [x] Style with the `--chart-1`..`--chart-5` ramp and a legend; keep it readable on both light and dark themes (tokens already theme-switch)
- [x] Render it in `CoachPage.tsx` in a titled card (e.g. "Last 4 weeks") alongside the existing adherence/message cards

### 4. Verification  <!-- agent: general-purpose -->

- [x] `cd frontend && npm run build` passes (tsc + vite) with the new Recharts components and types
- [x] Both charts render with real brief data for the demo member, and degrade to an empty/`null` state when their data arrays are empty [DEFERRED-TO-UAT]
- [x] `cd backend && python -c "import app.routers.coach"` (or run the app) confirms the brief response serializes the new fields without error

## Acceptance Criteria

- [ ] `GET /api/coach/brief` returns `message_pattern` and the 4-week comparison data populated for the demo member, including coach-side messages
- [ ] The Coach dashboard shows three distinct charts — adherence trend, message pattern, and 4-week comparison — covering all charts named in the `candidate-assessment-main` spec
- [ ] New chart components use Workout Wiz design tokens (`--chart-*`, `--space-*`, `--muted-foreground`, card chrome) with no hardcoded brand colors, and read theme-correctly in dark mode
- [ ] Charts render without throwing when their underlying data is empty (no message history / no adherence weeks)
- [ ] `frontend` production build passes

---
**UAT**: [`.docs/uat/096-coach-message-charts.uat.md`](../uat/096-coach-message-charts.uat.md)
