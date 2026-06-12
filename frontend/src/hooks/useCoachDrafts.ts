import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
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
    refetchInterval: 10_000,
  })
}
