# 111 — CoachPage draft review UI: edit and approve before output reaches a member

> **Depends on**: [110-coach-draft-lifecycle-endpoint](110-coach-draft-lifecycle-endpoint.md)
> **Blocks**: [112-hitl-approval-tests](112-hitl-approval-tests.md)
> **Parallel-safe with**: [108-accountability-engine-tests](108-accountability-engine-tests.md)

## Objective

Add a "Pending Drafts" panel to `CoachPage` that lists all `draft` and `approved` coach drafts for the selected member, allows the coach to edit body text and approve, and blocks sending until the draft is `approved`. This completes the HITL gate for Phase 2 of Roadmap 007.

## Approach

Two new hooks: `useCoachDrafts` (polls `GET /coach/draft?status=draft` + `GET /coach/draft?status=approved`) and `useCoachDraftActions` (PATCH wrapper). The UI panel renders below the Action Items card — one card per draft, with an editable textarea for the body, and Approve / Send buttons with correct state gating. The Send button is disabled unless `status == "approved"`.

New TypeScript types: `CoachDraftSchema` — added to `frontend/src/types/index.ts`.

## Steps

### 1. Add `CoachDraftSchema` type to `frontend/src/types/index.ts`  <!-- agent: general-purpose -->

Using Serena `insert_after_symbol` after `NudgeResponse`:

```typescript
export interface CoachDraftSchema {
  id: string
  member_id: string
  member_name: string
  content_type: string
  body: string
  grounded_on: string[]
  status: 'draft' | 'approved' | 'sent'
  created_by: string | null
  approved_by: string | null
  approved_at: string | null
  sent_at: string | null
  created_at: string
}
```

- [x] `CoachDraftSchema` interface exists in `frontend/src/types/index.ts` <!-- Completed: 2026-06-11 -->

### 2. Create `frontend/src/hooks/useCoachDrafts.ts`  <!-- agent: general-purpose -->

```typescript
import { useQuery } from '@tanstack/react-query'
import { useAuth } from './useAuth'
import { apiFetch } from '../lib/apiFetch'
import type { CoachDraftSchema } from '../types'

export function useCoachDrafts(memberId?: string | null) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['coach', 'drafts', memberId ?? null],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (memberId) params.set('member_id', memberId)
      const res = await apiFetch(`/api/coach/draft?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Request failed with status ${res.status}`)
      }
      const all = await res.json() as CoachDraftSchema[]
      // Show only draft and approved (not sent) for review panel
      return all.filter((d) => d.status !== 'sent')
    },
    enabled: !!token,
    refetchInterval: 10_000,  // Poll for new nudge drafts
  })
}
```

**Note**: the backend `GET /coach/draft` does not yet filter by `member_id`. If needed, filtering can be done client-side in the query function until the backend is updated.

- [x] `frontend/src/hooks/useCoachDrafts.ts` exists <!-- Completed: 2026-06-11 -->
- [x] Hook returns only `draft` and `approved` items (not `sent`) <!-- Completed: 2026-06-11 -->
- [x] Hook polls every 10 seconds to catch new nudge drafts <!-- Completed: 2026-06-11 -->

### 3. Create `frontend/src/hooks/useCoachDraftActions.ts`  <!-- agent: general-purpose -->

```typescript
import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from './useAuth'
import { apiFetch } from '../lib/apiFetch'
import type { CoachDraftSchema } from '../types'

export function useCoachDraftActions() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function patchDraft(
    draftId: string,
    action: 'approve' | 'edit' | 'send',
    body?: string,
  ): Promise<CoachDraftSchema | null> {
    setIsLoading(true)
    setError(null)
    try {
      const res = await apiFetch(`/api/coach/draft/${draftId}`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${token ?? ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ action, ...(body !== undefined ? { body } : {}) }),
      })
      if (!res.ok) {
        const errBody = await res.text()
        throw new Error(errBody || `Request failed with status ${res.status}`)
      }
      const updated = await res.json() as CoachDraftSchema
      await queryClient.invalidateQueries({ queryKey: ['coach', 'drafts'] })
      return updated
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return { patchDraft, isLoading, error }
}
```

- [x] `frontend/src/hooks/useCoachDraftActions.ts` exists <!-- Completed: 2026-06-11 -->
- [x] `patchDraft` invalidates the `['coach', 'drafts']` query cache on success <!-- Completed: 2026-06-11 -->

### 4. Create `PendingDraftsPanel` component and add to `CoachPage.tsx`  <!-- agent: general-purpose -->

Add a `PendingDraftsPanel` component immediately above the `export default function CoachPage()` declaration. Use Serena `insert_before_symbol` targeting `CoachPage`.

```tsx
function PendingDraftsPanel({ memberId }: { memberId: string }) {
  const { data: drafts, isLoading } = useCoachDrafts(memberId)
  const { patchDraft, isLoading: actionLoading } = useCoachDraftActions()
  const [editBodies, setEditBodies] = React.useState<Record<string, string>>({})

  if (isLoading || !drafts || drafts.length === 0) return null

  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', borderRadius: '0.75rem', padding: 'var(--space-4)', display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      <div style={{ fontSize: '0.8rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--muted-foreground)' }}>
        Pending Drafts
      </div>
      {drafts.map((draft) => {
        const currentBody = editBodies[draft.id] ?? draft.body
        const isEdited = currentBody !== draft.body
        const canSend = draft.status === 'approved' && !isEdited
        return (
          <div key={draft.id} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', background: 'var(--muted)', borderRadius: '0.5rem', padding: 'var(--space-3)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ fontSize: '0.7rem', fontWeight: 700, textTransform: 'uppercase', color: draft.status === 'approved' ? '#22c55e' : 'var(--muted-foreground)' }}>
                {draft.status} · {draft.content_type}
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--muted-foreground)' }}>
                {new Date(draft.created_at).toLocaleTimeString()}
              </span>
            </div>
            <textarea
              className="ww-scroll"
              style={{ width: '100%', minHeight: '4rem', borderRadius: '0.375rem', border: '1px solid var(--border)', background: 'var(--background)', padding: '0.5rem 0.75rem', fontSize: '0.85rem', fontFamily: 'inherit', color: 'inherit', resize: 'vertical' }}
              value={currentBody}
              onChange={(e) => setEditBodies((prev) => ({ ...prev, [draft.id]: e.target.value }))}
            />
            {draft.grounded_on.length > 0 && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)' }}>
                {draft.grounded_on.map((fact, i) => (
                  <span key={i} style={{ fontSize: '0.65rem', background: 'var(--accent)', color: 'var(--accent-foreground)', borderRadius: '999px', padding: '0.1rem 0.45rem' }}>{fact}</span>
                ))}
              </div>
            )}
            <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
              {isEdited && (
                <button
                  type="button"
                  className="ww-btn ww-btn--sm ww-btn--ghost"
                  disabled={actionLoading}
                  onClick={async () => {
                    await patchDraft(draft.id, 'edit', currentBody)
                    setEditBodies((prev) => { const n = { ...prev }; delete n[draft.id]; return n })
                  }}
                >
                  Save Edit
                </button>
              )}
              {draft.status === 'draft' && !isEdited && (
                <button
                  type="button"
                  className="ww-btn ww-btn--sm"
                  disabled={actionLoading}
                  onClick={() => patchDraft(draft.id, 'approve')}
                >
                  Approve
                </button>
              )}
              <button
                type="button"
                className="ww-btn ww-btn--sm ww-btn--gradient"
                disabled={!canSend || actionLoading}
                title={!canSend ? 'Draft must be approved before sending' : undefined}
                onClick={() => patchDraft(draft.id, 'send')}
              >
                Send
              </button>
            </div>
          </div>
        )
      })}
    </div>
  )
}
```

Then in the `CoachPage` JSX, add the panel below the Action Items card and above the message pattern section (look for `{/* ── Message pattern + 4-week comparison ── */}` comment):

```tsx
{brief && selectedMemberId && (
  <PendingDraftsPanel memberId={selectedMemberId} />
)}
```

- [x] `PendingDraftsPanel` component exists in `CoachPage.tsx` <!-- Completed: 2026-06-11 -->
- [x] Panel renders below Action Items / above message pattern section <!-- Completed: 2026-06-11 -->
- [x] Panel hidden when no pending drafts exist <!-- Completed: 2026-06-11 -->
- [x] Each draft shows status badge, content type, and editable body textarea <!-- Completed: 2026-06-11 -->
- [x] Send button is disabled when `status === 'draft'` <!-- Completed: 2026-06-11 -->
- [x] Send button enabled after `approve` action <!-- Completed: 2026-06-11 -->
- [x] Editing body triggers "Save Edit" button; saving resets status to `draft` <!-- Completed: 2026-06-11 -->

### 5. Import new hooks in `CoachPage.tsx`  <!-- agent: general-purpose -->

Add to imports:

```typescript
import { useCoachDrafts } from '../hooks/useCoachDrafts'
import { useCoachDraftActions } from '../hooks/useCoachDraftActions'
```

- [x] Both hooks imported in `CoachPage.tsx` <!-- Completed: 2026-06-11 -->

### 6. TypeScript build check  <!-- agent: general-purpose -->

```bash
cd frontend && npm run build 2>&1 | tail -20
```

Fix any TypeScript errors before marking complete.

- [x] `npm run build` passes with zero TypeScript errors <!-- Completed: 2026-06-11 -->

## Acceptance Criteria

- [x] "Pending Drafts" panel appears in `CoachPage` when drafts with `status != sent` exist
- [x] Panel is absent when no pending drafts exist
- [x] Each draft card shows: status badge, content type, editable body, grounded-on tags, action buttons
- [x] "Send" button is disabled when draft `status === 'draft'`
- [x] "Approve" button transitions draft to `approved` and enables "Send"
- [x] Editing body text shows "Save Edit" button; saving resets status from `approved` to `draft`
- [x] "Send" succeeds only after re-approval, consistent with the HITL gate
- [x] `npm run build` in `frontend/` completes with no TypeScript errors

---
**UAT**: [`.docs/uat/111-coach-draft-review-ui.uat.md`](../uat/111-coach-draft-review-ui.uat.md)
