import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { apiFetch } from '../lib/apiFetch'
import type { CoachBriefResponse } from '../types'

export function useCoachBrief() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['coach', 'brief'],
    queryFn: async () => {
      const res = await apiFetch('/api/coach/brief', {
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
