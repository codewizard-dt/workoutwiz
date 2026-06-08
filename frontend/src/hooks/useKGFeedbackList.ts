import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/context/AuthContext'

interface FeedbackItem {
  exercise_id: string
  rating: number
  workout_set_id: string | null
  context_type: string
}

interface FeedbackListResponse {
  workout_id: string
  items: FeedbackItem[]
}

type Rating = 1 | 2 | 3 | 4 | 5

/**
 * Fetch the member's previously-saved ratings for a workout, keyed by
 * workout_set_id, so the rating widgets can restore them on load.
 */
export function useKGFeedbackList(workoutId?: string) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['kg-feedback', workoutId],
    enabled: workoutId != null && token != null,
    queryFn: async (): Promise<Record<string, Rating>> => {
      const res = await fetch(`/api/kg/feedback?workout_id=${encodeURIComponent(workoutId ?? '')}`, {
        headers: { Authorization: `Bearer ${token ?? ''}` },
      })
      if (!res.ok) throw new Error(`Failed to fetch feedback (status ${res.status})`)
      const body = (await res.json()) as FeedbackListResponse
      const map: Record<string, Rating> = {}
      for (const item of body.items) {
        if (item.workout_set_id != null && item.rating >= 1 && item.rating <= 5) {
          map[item.workout_set_id] = item.rating as Rating
        }
      }
      return map
    },
  })
}
