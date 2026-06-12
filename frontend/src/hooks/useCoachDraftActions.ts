import { useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../context/AuthContext'
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
