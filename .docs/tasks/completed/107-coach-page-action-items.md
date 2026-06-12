# 107 — Surface ranked action items + draft nudges in CoachPage morning-brief cards

> **Depends on**: [105-accountability-service](105-accountability-service.md), [106-coach-nudge-endpoint](106-coach-nudge-endpoint.md)
> **Blocks**: [108-accountability-engine-tests](108-accountability-engine-tests.md)
> **Parallel-safe with**: [109-coach-draft-persistence](109-coach-draft-persistence.md), [110-coach-draft-lifecycle-endpoint](110-coach-draft-lifecycle-endpoint.md)

## Objective

Add an "Action Items" card to `CoachPage` that calls `rank_action_items` (via a new frontend hook) against the loaded `CoachBriefResponse` and displays ranked items with a "Draft Nudge" button per item. Clicking "Draft Nudge" calls `POST /coach/nudge` and shows the draft message inline.

## Approach

All data is already available in `brief` (the `CoachBriefResponse`). The ranking runs client-side by calling a new `useCoachActionItems` hook that computes items from `brief.adherence_weeks` and `brief.churn_risk` using the same heuristic logic as the backend service (mirrored in TS). The nudge API call uses a new `useCoachNudge` mutation hook.

The card is inserted between the "Morning Brief" grid section and the "Message Pattern" section. Design follows the existing ember card pattern (same `var(--card)` + `var(--border)` styling).

New TypeScript types: `ActionItem`, `NudgeRequest`, `NudgeResponse` — added to `frontend/src/types/index.ts`.

## Steps

### 1. Add `ActionItem`, `NudgeRequest`, `NudgeResponse` types to `frontend/src/types/index.ts`  <!-- agent: general-purpose -->

Using Serena `insert_after_symbol` after the `CoachBriefResponse` interface:

```typescript
export interface ActionItem {
  priority: 'high' | 'medium' | 'low'
  member_id: string
  member_name: string
  reason: string
  context: Record<string, unknown>
}

export interface NudgeRequest {
  member_id: string
  member_name: string
  action_item: ActionItem
}

export interface NudgeResponse {
  draft_message: string
  grounded_on: string[]
}
```

- [x] `ActionItem`, `NudgeRequest`, `NudgeResponse` types exist in `frontend/src/types/index.ts` <!-- Completed: 2026-06-11 -->

### 2. Create `frontend/src/hooks/useCoachActionItems.ts`  <!-- agent: general-purpose -->

```typescript
import { useMemo } from 'react'
import type { ActionItem, AdherenceWeek, ChurnRisk } from '../types'

export function useCoachActionItems(
  memberId: string,
  memberName: string,
  adherenceWeeks: AdherenceWeek[],
  churnRisk: ChurnRisk,
): ActionItem[] {
  return useMemo(() => {
    const items: ActionItem[] = []

    if (churnRisk.level === 'high') {
      items.push({
        priority: 'high',
        member_id: memberId,
        member_name: memberName,
        reason: `High churn risk: ${churnRisk.reasons.join('; ')}`,
        context: { churn_level: churnRisk.level, churn_reasons: churnRisk.reasons },
      })
    }

    if (adherenceWeeks.length > 0) {
      const latest = adherenceWeeks[adherenceWeeks.length - 1]
      if (latest.pct < 50) {
        items.push({
          priority: 'high',
          member_id: memberId,
          member_name: memberName,
          reason: `Low adherence this week: ${latest.pct}% (week of ${latest.week_of})`,
          context: { week_of: latest.week_of, adherence_pct: latest.pct },
        })
      } else if (latest.pct < 70) {
        items.push({
          priority: 'medium',
          member_id: memberId,
          member_name: memberName,
          reason: `Below-target adherence this week: ${latest.pct}% (week of ${latest.week_of})`,
          context: { week_of: latest.week_of, adherence_pct: latest.pct },
        })
      }
    }

    const order: Record<string, number> = { high: 0, medium: 1, low: 2 }
    return items.sort((a, b) => (order[a.priority] ?? 3) - (order[b.priority] ?? 3))
  }, [memberId, memberName, adherenceWeeks, churnRisk])
}
```

- [x] `frontend/src/hooks/useCoachActionItems.ts` exists <!-- Completed: 2026-06-11 -->
- [x] Hook mirrors the Python ranking heuristic exactly <!-- Completed: 2026-06-11 -->

### 3. Create `frontend/src/hooks/useCoachNudge.ts`  <!-- agent: general-purpose -->

```typescript
import { useState } from 'react'
import { useAuth } from './useAuth'
import { apiFetch } from '../lib/apiFetch'
import type { ActionItem, NudgeResponse } from '../types'

export function useCoachNudge() {
  const { token } = useAuth()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function draftNudge(
    memberId: string,
    memberName: string,
    actionItem: ActionItem,
  ): Promise<NudgeResponse | null> {
    setIsLoading(true)
    setError(null)
    try {
      const res = await apiFetch('/api/coach/nudge', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token ?? ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ member_id: memberId, member_name: memberName, action_item: actionItem }),
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Request failed with status ${res.status}`)
      }
      return res.json() as Promise<NudgeResponse>
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return { draftNudge, isLoading, error }
}
```

- [x] `frontend/src/hooks/useCoachNudge.ts` exists <!-- Completed: 2026-06-11 -->
- [x] `draftNudge` returns `NudgeResponse | null` and manages loading/error state <!-- Completed: 2026-06-11 -->

### 4. Add "Action Items" card to `CoachPage.tsx`  <!-- agent: general-purpose -->

Use Serena `search_for_pattern` to find the JSX comment `{/* ── Message pattern + 4-week comparison ── */}` in `CoachPage.tsx`. Insert the action items card immediately before that comment using `replace_content`.

The card should render between the adherence grid and the message-pattern grid.

```tsx
{/* ── Action Items ── */}
{(() => {
  const actionItems = useCoachActionItems(
    brief.member_id,
    brief.member_name,
    brief.adherence_weeks,
    brief.churn_risk,
  )
  // eslint-disable-next-line react-hooks/rules-of-hooks
  const { draftNudge, isLoading: nudgeLoading } = useCoachNudge()
  const [nudgeDrafts, setNudgeDrafts] = React.useState<Record<number, string>>({})

  if (actionItems.length === 0) return null

  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '0.75rem', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
        Action Items
      </div>
      {actionItems.map((item, i) => (
        <div key={i} style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'flex-start', background: item.priority === 'high' ? 'color-mix(in srgb, var(--destructive) 8%, var(--card))' : 'var(--muted)', borderRadius: '0.5rem', padding: 'var(--space-3)' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: item.priority === 'high' ? 'var(--destructive)' : 'var(--muted-foreground)', marginBottom: '0.2rem' }}>
              {item.priority}
            </div>
            <div style={{ fontSize: '0.85rem', lineHeight: 1.4 }}>{item.reason}</div>
            {nudgeDrafts[i] && (
              <div style={{ marginTop: 'var(--space-2)', fontSize: '0.85rem', background: 'var(--accent)', borderRadius: '0.375rem', padding: 'var(--space-2)', color: 'var(--accent-foreground)', lineHeight: 1.5 }}>
                {nudgeDrafts[i]}
              </div>
            )}
          </div>
          <button
            type="button"
            className="ww-btn ww-btn--sm ww-btn--ghost"
            disabled={nudgeLoading}
            onClick={async () => {
              const result = await draftNudge(brief.member_id, brief.member_name, item)
              if (result) setNudgeDrafts(prev => ({ ...prev, [i]: result.draft_message }))
            }}
            style={{ flexShrink: 0, fontSize: '0.75rem' }}
          >
            Draft Nudge
          </button>
        </div>
      ))}
    </div>
  )
})()}
```

**Note**: Because hooks cannot be called inside `.map()` or IIFEs, refactor this into a standalone `ActionItemsCard` component in the same file if TypeScript/ESLint rejects inline hook usage. The component receives `brief` as a prop and internally calls the hooks.

- [x] "Action Items" card renders in `CoachPage` when action items exist <!-- Completed: 2026-06-11 -->
- [x] Card is hidden when `actionItems.length === 0` <!-- Completed: 2026-06-11 -->
- [x] Each item shows its priority label and reason <!-- Completed: 2026-06-11 -->
- [x] "Draft Nudge" button calls `POST /coach/nudge` and renders the draft inline <!-- Completed: 2026-06-11 -->
- [x] High-priority items have a visually distinct background tint <!-- Completed: 2026-06-11 -->

### 5. Import new hooks in `CoachPage.tsx`  <!-- agent: general-purpose -->

Add to the imports section at the top of `CoachPage.tsx`:

```typescript
import { useCoachActionItems } from '../hooks/useCoachActionItems'
import { useCoachNudge } from '../hooks/useCoachNudge'
```

And add `import React from 'react'` if not already present (for `React.useState` in the IIFE pattern).

- [x] Both hooks are imported in `CoachPage.tsx` <!-- Completed: 2026-06-11 -->

## Acceptance Criteria

- [x] `useCoachActionItems` hook exists and computes items from `brief.adherence_weeks` + `brief.churn_risk` <!-- Completed: 2026-06-11 -->
- [x] `useCoachNudge` hook exists and POSTs to `/api/coach/nudge` <!-- Completed: 2026-06-11 -->
- [x] "Action Items" card appears in `CoachPage` when the demo member has action items <!-- Completed: 2026-06-11 -->
- [x] "Action Items" card is absent when no items are computed (healthy member) <!-- Completed: 2026-06-11 -->
- [x] Clicking "Draft Nudge" on an item fetches and displays the AI-drafted message inline <!-- Completed: 2026-06-11 -->
- [x] `npm run build` in `frontend/` completes with no TypeScript errors <!-- Completed: 2026-06-11 -->

---
**UAT**: [`.docs/uat/completed/107-coach-page-action-items.uat.md`](../uat/completed/107-coach-page-action-items.uat.md)
