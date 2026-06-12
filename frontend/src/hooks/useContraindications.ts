import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'
import { apiFetch } from '@/lib/apiFetch'
import type { ContraindicationListResponse } from '@/types'

/**
 * Fetch every exercise contraindicated for the current member (or `memberId`),
 * each with a graph-grounded reason + confidence. Powers the "Safe for me"
 * lens. Only runs when `enabled` (the lens is on) and a token is present.
 */
export function useContraindications(enabled = true, memberId?: string | null) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['kg-contraindications', memberId ?? null],
    enabled: enabled && !!token,
    queryFn: async () => {
      const url = memberId
        ? `/api/kg/contraindications?member_id=${encodeURIComponent(memberId)}`
        : '/api/kg/contraindications'
      const res = await apiFetch(url, {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      return res.json() as Promise<ContraindicationListResponse>
    },
  })
}
