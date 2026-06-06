# 070 — KG Chat/Dashboard: Knowledge Graph Frontend Page

> **Depends on**: [065-kg-fastapi-router](completed/065-kg-fastapi-router.md)
> **Blocks**: none
> **Parallel-safe with**: [071-feedback-submission-ui](071-feedback-submission-ui.md), [072-docker-compose-verification](072-docker-compose-verification.md), [073-readme-production-eval](073-readme-production-eval.md)

## Objective

Add a `/knowledge-graph` React page to the frontend that lets the user request a personalized workout recommendation from the KG system, and displays the result with exercise details and reasoning.

## Approach

- New page `frontend/src/pages/KnowledgeGraphPage.tsx`
- Route `/knowledge-graph` added to `frontend/src/router.tsx`
- Nav link in the main layout
- Form: `query` textarea + submit button (member_id derived from auth context user.id)
- Calls `POST /kg/recommend` via Axios
- Displays recommendation cards with exercise name, sets/reps, reasoning
- Shows "fallback used" notice if `fallback_used: true`
- Loading and error states handled

**React Query hook** `useKGRecommend` in `frontend/src/hooks/useKGRecommend.ts`:
```typescript
import { useMutation } from '@tanstack/react-query'
import axios from 'axios'

export function useKGRecommend() {
  return useMutation({
    mutationFn: async ({ memberId, query }: { memberId: string; query: string }) => {
      const { data } = await axios.post('/api/kg/recommend', { member_id: memberId, query })
      return data
    }
  })
}
```

## Steps

### 1. Create `frontend/src/hooks/useKGRecommend.ts`  <!-- agent: general-purpose -->

Write using the `Write` tool with the hook above.

- [x] Hook file created <!-- Completed: 2026-06-06 -->

### 2. Create `frontend/src/pages/KnowledgeGraphPage.tsx`  <!-- agent: general-purpose -->

Write using the `Write` tool with:
- `useState` for query input
- `useKGRecommend()` mutation hook
- Form with textarea and submit button
- Conditional rendering: loading spinner, error banner, recommendation list
- Each exercise in a card with name, sets × reps/duration, reasoning text
- Fallback notice: "Limited options due to injury constraints."

- [x] `KnowledgeGraphPage.tsx` created with form + results display <!-- Completed: 2026-06-06 -->

### 3. Add route to `frontend/src/router.tsx`  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `frontend/src/router.tsx` to see current route structure. Add:
```tsx
{ path: '/knowledge-graph', element: <KnowledgeGraphPage /> }
```

- [x] Route registered <!-- Completed: 2026-06-06 -->

### 4. Add nav link  <!-- agent: general-purpose -->

Find the main navigation component (check `frontend/src/` for `App.tsx`, `Layout.tsx`, or `Navbar.tsx`). Add a link to `/knowledge-graph` labeled "AI Coach".

- [x] Nav link added <!-- Completed: 2026-06-06 -->

### 5. Update `frontend/src/hooks/index.ts` to export the new hook  <!-- agent: general-purpose -->

Add `export * from './useKGRecommend'` if an index file exists.

- [x] Hook exported from index <!-- Completed: 2026-06-06 -->

### 6. Update roadmap  <!-- agent: general-purpose -->

Replace the inline Phase 7 KG dashboard placeholder.

- [x] Roadmap updated <!-- Completed: 2026-06-06 -->

## Acceptance Criteria

- [x] `/knowledge-graph` route registered and renders `KnowledgeGraphPage`
- [x] Page has a query input form that calls `POST /kg/recommend`
- [x] Recommendation displayed with exercise cards (name, sets, reps/duration, reasoning)
- [x] Loading state shown during request
- [x] Error state shown on failure
- [x] Nav link present

---
**UAT**: `.docs/uat/070-kg-chat-dashboard.uat.md`
