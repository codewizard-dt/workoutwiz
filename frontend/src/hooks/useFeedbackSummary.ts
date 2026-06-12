import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import { apiFetch } from '@/lib/apiFetch'
import type { FeedbackSummaryResponse } from '@/types'

/**
 * Fetch the current member's aggregated rating per exercise (average, count,
 * last rated). Surfaces "you rated this" signals on cards and in the drawer.
 */
export function useFeedbackSummary() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['kg-feedback-summary'],
    enabled: !!token,
    queryFn: async () => {
      const res = await apiFetch('/api/kg/feedback/summary', {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      return res.json() as Promise<FeedbackSummaryResponse>
    },
  })
}
