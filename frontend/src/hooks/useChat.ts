import { useState, useCallback } from 'react'
import { useAuth } from '../context/AuthContext'

export interface AgentStep {
  agent: string
  confidence?: number
  latency_ms?: number
  timestamp?: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  route?: string
  confidence?: number
  steps?: AgentStep[]
}

function getOrCreateSessionId(): string {
  const KEY = 'ww_session_id'
  let id = localStorage.getItem(KEY)
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem(KEY, id)
  }
  return id
}

export function useChat() {
  const { token } = useAuth()
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId] = useState<string>(getOrCreateSessionId)

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return

      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content: trimmed,
      }

      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)
      setError(null)

      try {
        const res = await fetch('/api/chat/', {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token ?? ''}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: trimmed, session_id: sessionId }),
        })

        if (!res.ok) {
          const body = await res.text()
          throw new Error(body || `Request failed with status ${res.status}`)
        }

        const data = await res.json() as {
          reply: string
          route: string
          confidence: number
          session_id: string
          audit_steps?: AgentStep[]
          workout_draft?: import('@/types').WorkoutDraft
        }

        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          route: data.route,
          confidence: data.confidence,
          steps: data.audit_steps,
          workout_draft: data.workout_draft,
        }

        setMessages((prev) => [...prev, assistantMsg])
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err))
        // Remove the optimistic user message on failure
        setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      } finally {
        setIsLoading(false)
      }
    },
    [token, sessionId],
  )

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return { messages, sendMessage, isLoading, error, clearMessages, sessionId }
}
