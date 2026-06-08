import { useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import type { CoachChatMessage, CoachChatResponse } from '../types'

export function useCoachChat(memberId?: string | null) {
  const { token } = useAuth()
  // Track the memberId that the current chat session belongs to so we can reset on change.
  // We store it as state so React re-renders with a clean slate when it changes.
  const [activeMemberId, setActiveMemberId] = useState<string | null | undefined>(memberId)
  const [messages, setMessages] = useState<CoachChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // When memberId changes, reset the conversation synchronously during this render
  // by deriving from state — this avoids the lint errors from useEffect + setState
  // and from reading refs during render.
  if (activeMemberId !== memberId) {
    setActiveMemberId(memberId)
    setMessages([])
    setSessionId(null)
    setError(null)
  }

  const sendMessage = useCallback(
    async (text: string, image?: string) => {
      const msg = text.trim()
      if ((!msg && !image) || !token || isLoading) return

      setError(null)
      const userMsg: CoachChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: msg,
        image,
      }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      try {
        const res = await fetch('/api/coach/chat', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: msg,
            session_id: sessionId ?? '',
            image: image ?? null,
            member_id: memberId ?? null,
          }),
        })

        if (!res.ok) {
          const body = await res.text()
          throw new Error(body || `Request failed with status ${res.status}`)
        }

        const data = (await res.json()) as CoachChatResponse
        if (!sessionId) setSessionId(data.session_id)

        const assistantMsg: CoachChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          grounded_facts: data.grounded_facts,
        }
        setMessages((prev) => [...prev, assistantMsg])
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Coach chat failed')
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      } finally {
        setIsLoading(false)
      }
    },
    [token, sessionId, isLoading, memberId],
  )

  return { messages, sendMessage, isLoading, error, sessionId }
}
