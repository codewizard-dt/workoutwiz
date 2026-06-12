import { useState } from 'react'
import { useAuth } from '../context/AuthContext'
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
      return await (res.json() as Promise<NudgeResponse>)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      return null
    } finally {
      setIsLoading(false)
    }
  }

  return { draftNudge, isLoading, error }
}
