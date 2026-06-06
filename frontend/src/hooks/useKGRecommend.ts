import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../lib/apiFetch'

export interface KGRecommendResponse {
  member_id: string
  exercises: unknown[]
  overall_reasoning: string
  skipped_exercise_ids: string[]
  fallback_used: boolean
}

export function useKGRecommend() {
  return useMutation({
    mutationFn: async ({ memberId, query }: { memberId: string; query: string }) => {
      const res = await apiFetch('/api/kg/recommend', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ member_id: memberId, query }),
      })
      return res.json() as Promise<KGRecommendResponse>
    },
  })
}
