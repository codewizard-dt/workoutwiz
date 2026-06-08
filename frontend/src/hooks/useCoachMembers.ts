import { useQuery } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
import { apiFetch } from '../lib/apiFetch'
import type { CoachMemberSummary } from '../types'

export function useCoachMembers() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['coach', 'members'],
    queryFn: async () => {
      const res = await apiFetch('/api/coach/members', {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Request failed with status ${res.status}`)
      }
      return res.json() as Promise<CoachMemberSummary[]>
    },
    enabled: !!token,
  })
}
