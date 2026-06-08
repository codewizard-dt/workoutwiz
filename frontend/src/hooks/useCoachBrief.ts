import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { apiFetch } from '../lib/apiFetch'
import type { CoachBriefResponse } from '../types'

export function useCoachBrief(memberId?: string | null) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['coach', 'brief', memberId ?? null],
    queryFn: async () => {
      const url = memberId
        ? `/api/coach/brief?member_id=${encodeURIComponent(memberId)}`
        : '/api/coach/brief'
      const res = await apiFetch(url, {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Request failed with status ${res.status}`)
      }
      return res.json() as Promise<CoachBriefResponse>
    },
    enabled: !!token,
  })
}
