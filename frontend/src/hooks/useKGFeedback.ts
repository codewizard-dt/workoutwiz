import { useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/apiFetch'
import { useAuth } from '@/context/AuthContext'

interface FeedbackPayload {
  member_id: string
  exercise_id?: string
  rating: number
  text?: string
  workout_id?: string
  workout_set_id?: string
  context_type: 'exercise' | 'workout' | 'set'
}

interface FeedbackResponse {
  feedback_id: string
  message?: string
}

export function useKGFeedback() {
  const { token } = useAuth()
  const queryClient = useQueryClient()
  return useMutation<FeedbackResponse, Error, FeedbackPayload>({
    onSuccess: (_data, payload) => {
      if (payload.workout_id != null) {
        void queryClient.invalidateQueries({ queryKey: ['kg-feedback', payload.workout_id] })
      }
    },
    mutationFn: async (payload: FeedbackPayload) => {
      const res = await apiFetch('/api/kg/feedback', {
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
