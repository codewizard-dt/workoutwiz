import { useMutation } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'

interface FeedbackPayload {
  member_id: string
  exercise_id: string
  rating: number
  text?: string
}

interface FeedbackResponse {
  status: string
}

export function useKGFeedback() {
  const { token } = useAuth()
  return useMutation<FeedbackResponse, Error, FeedbackPayload>({
    mutationFn: async (payload: FeedbackPayload) => {
      const res = await fetch('/api/kg/feedback', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token ?? ''}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      if (!res.ok) {
        const body = await res.text()
        throw new Error(body || `Request failed with status ${res.status}`)
      }
      return res.json() as Promise<FeedbackResponse>
    },
  })
}
