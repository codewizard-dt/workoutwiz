import { useQuery } from '@tanstack/react-query'
import { apiFetch } from '@/lib/apiFetch'
import type { ExerciseFacets } from '@/types'

/**
 * Fetch the distinct filterable values across the whole exercise catalog
 * (muscle groups, equipment, movement patterns, categories) with counts, for
 * populating the filter rail. The catalog is static, so this is cached long.
 */
export function useExerciseFacets() {
  return useQuery({
    queryKey: ['exercise-facets'],
    staleTime: 5 * 60 * 1000,
    queryFn: async () => {
      const res = await apiFetch('/api/exercises/facets')
      return res.json() as Promise<ExerciseFacets>
    },
  })
}
