# 071 — Feedback Submission UI: Rate Exercises After Workout

> **Depends on**: [065-kg-fastapi-router](completed/065-kg-fastapi-router.md)
> **Blocks**: none
> **Parallel-safe with**: [070-kg-chat-dashboard](070-kg-chat-dashboard.md), [072-docker-compose-verification](072-docker-compose-verification.md), [073-readme-production-eval](073-readme-production-eval.md)

## Objective

Add a feedback submission component `FeedbackForm` that lets users rate an exercise 1–5 and submit optional text feedback. Wire it into the `KnowledgeGraphPage` so users can submit feedback after viewing their workout recommendation.

## Approach

- `frontend/src/components/FeedbackForm.tsx` — standalone component
- Props: `{ exerciseId: string, memberId: string, onSuccess?: () => void }`
- Star rating (1–5), optional text input, submit button
- Calls `POST /kg/feedback` via a `useKGFeedback` hook
- Shows success/error state after submission

**Hook `useKGFeedback` in `frontend/src/hooks/useKGFeedback.ts`:**
```typescript
export function useKGFeedback() {
  return useMutation({
    mutationFn: async (payload: { member_id: string; exercise_id: string; rating: number; text?: string }) => {
      const { data } = await axios.post('/api/kg/feedback', payload)
      return data
    }
  })
}
```

**Integration**: In `KnowledgeGraphPage.tsx`, after a recommendation is displayed, show a `FeedbackForm` for each exercise in the recommendation list.

## Steps

### 1. Create `frontend/src/hooks/useKGFeedback.ts`  <!-- agent: general-purpose -->

Write using the `Write` tool.

- [ ] Hook created

### 2. Create `frontend/src/components/FeedbackForm.tsx`  <!-- agent: general-purpose -->

Write using the `Write` tool with:
- Star rating: 5 clickable star buttons (1–5), highlights selected and below
- Optional text area for feedback text
- Submit button disabled until a rating is selected
- Loading state during submission
- "Thank you for your feedback!" success message
- Error message on failure

Use Tailwind classes for styling — match the existing component style (check another component for reference).

- [ ] `FeedbackForm.tsx` created with star rating + text input + submit

### 3. Integrate `FeedbackForm` into `KnowledgeGraphPage.tsx`  <!-- agent: general-purpose -->

Use Serena `get_symbols_overview` on `frontend/src/pages/KnowledgeGraphPage.tsx`. Add `FeedbackForm` after each exercise card in the recommendation list. Pass `exerciseId` and `memberId` props.

- [ ] `FeedbackForm` shown per exercise in recommendation results

### 4. Export hook from index  <!-- agent: general-purpose -->

Add `export * from './useKGFeedback'` to `frontend/src/hooks/index.ts`.

- [ ] Hook exported

### 5. Update roadmap  <!-- agent: general-purpose -->

Replace inline Phase 7 feedback UI placeholder.

- [ ] Roadmap updated

## Acceptance Criteria

- [ ] `FeedbackForm` component renders star rating (1–5) + optional text + submit
- [ ] Submit disabled until rating selected
- [ ] Calls `POST /kg/feedback` with `member_id`, `exercise_id`, `rating`, `text`
- [ ] Success/error feedback shown to user
- [ ] `FeedbackForm` integrated into `KnowledgeGraphPage` per exercise

---
**UAT**: `.docs/uat/071-feedback-submission-ui.uat.md`
