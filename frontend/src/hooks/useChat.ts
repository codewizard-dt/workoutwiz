import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '@/lib/apiFetch'
import { useAuth } from '../context/AuthContext'
import type { AgentStep, ChatMessage, KGResult, WorkoutDraft } from '@/types'

interface ChatApiResponse {
  reply: string
  route: string
  confidence: number
  session_id: string
  audit_steps?: AgentStep[]
  workout_draft?: WorkoutDraft
  kg_result?: KGResult | null
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
  const [sessionId] = useState<string>(getOrCreateSessionId)

  const mutation = useMutation({
    mutationFn: async (text: string): Promise<ChatApiResponse> => {
      const res = await apiFetch('/api/chat/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token ?? ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      return res.json() as Promise<ChatApiResponse>
    },
    onSuccess: (data) => {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          route: data.route,
          confidence: data.confidence,
          steps: data.audit_steps,
          workout_draft: data.workout_draft,
          kg_result: data.kg_result,
        },
      ])
    },
  })

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmed,
    }
    setMessages((prev) => [...prev, userMsg])

    try {
      await mutation.mutateAsync(trimmed)
    } catch {
      // Drop the optimistic user message on failure. A 401 is handled globally
      // by the QueryClient guard (session cleared + redirect to login).
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    }
  }

  const clearMessages = () => {
    setMessages([])
    mutation.reset()
  }

  const error = mutation.error
    ? (mutation.error instanceof Error ? mutation.error.message : String(mutation.error))
    : null

  return { messages, sendMessage, isLoading: mutation.isPending, error, clearMessages, sessionId }
}