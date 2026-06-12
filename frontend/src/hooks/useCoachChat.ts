import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { apiFetch } from '../lib/apiFetch'
import { useAuth } from '../context/AuthContext'
import type { CoachChatMessage, CoachChatResponse } from '../types'

export function useCoachChat(memberId?: string | null) {
  const { token } = useAuth()
  // Track the memberId that the current chat session belongs to so we can reset on change.
  const [activeMemberId, setActiveMemberId] = useState<string | null | undefined>(memberId)
  const [messages, setMessages] = useState<CoachChatMessage[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const mutation = useMutation({
    mutationFn: async (vars: { text: string; image?: string }): Promise<CoachChatResponse> => {
      const res = await apiFetch('/api/coach/chat', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token ?? ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: vars.text,
          session_id: sessionId ?? '',
          image: vars.image ?? null,
          member_id: memberId ?? null,
        }),
      })
      return res.json() as Promise<CoachChatResponse>
    },
  })

  // When memberId changes, reset the conversation synchronously during render.
  if (activeMemberId !== memberId) {
    setActiveMemberId(memberId)
    setMessages([])
    setSessionId(null)
    setError(null)
  }

  const sendMessage = async (text: string, image?: string) => {
    const msg = text.trim()
    if ((!msg && !image) || !token || mutation.isPending) return

    setError(null)
    const userMsg: CoachChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: msg,
      image,
    }
    setMessages((prev) => [...prev, userMsg])

    try {
      const data = await mutation.mutateAsync({ text: msg, image })
      if (!sessionId) setSessionId(data.session_id)
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.reply,
          grounded_facts: data.grounded_facts,
          steps: (data.audit_log ?? []).map((e) => ({
            agent: e.event,
            confidence: e.confidence,
            latency_ms: e.latency_ms,
            detail: e.detail,
          })),
        },
      ])
    } catch (err) {
      // A 401 is handled globally by the QueryClient guard (session cleared +
      // redirect). Other failures surface inline.
      setError(err instanceof Error ? err.message : 'Coach chat failed')
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
    }
  }

  return { messages, sendMessage, isLoading: mutation.isPending, error, sessionId }
}