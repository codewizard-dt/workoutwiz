import { useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'
import type { CoachChatMessage, CoachChatResponse } from '../types'

export function useCoachChat() {
  const { token } = useAuth()
  const [messages, setMessages] = useState<CoachChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      const msg = text.trim()
      if (!msg || !token || isLoading) return

      setError(null)
      const userMsg: CoachChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: msg,
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
          body: JSON.stringify({ message: msg, session_id: sessionId ?? '' }),
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
    [token, sessionId, isLoading],
  )

  return { messages, sendMessage, isLoading, error, sessionId }
}
