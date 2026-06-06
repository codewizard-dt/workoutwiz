import { useQuery } from '@tanstack/react-query'
import type { Exercise } from '@/types'

export interface ExerciseFilters {
  name?: string
  muscle_groups?: string[]
  equipment?: string[]
  priority_tier?: number
}

export function useExercises(filters?: ExerciseFilters) {
  return useQuery({
    queryKey: ['exercises', filters],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (filters?.name) params.append('name', filters.name)
      filters?.muscle_groups?.forEach((m) => { params.append('muscle_groups', m); })
      filters?.equipment?.forEach((e) => { params.append('equipment', e); })
      if (filters?.priority_tier) params.append('priority_tier', String(filters.priority_tier))
      const res = await fetch(`/api/exercises/?${params}`)
      if (!res.ok) throw new Error('Failed to fetch exercises')
      return res.json() as Promise<Exercise[]>
    },
  })
}
