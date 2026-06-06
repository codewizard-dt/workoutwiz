import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiFetch } from '@/lib/apiFetch'
import { useAuth } from '@/context/AuthContext'
import type { Workout, WorkoutCreate } from '@/types'

function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' }
}

export function useWorkouts() {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['workouts'],
    queryFn: async () => {
      const res = await apiFetch('/api/workouts/', { headers: authHeaders(token ?? '') })
      if (!res.ok) throw new Error('Failed to fetch workouts')
      return res.json() as Promise<Workout[]>
    },
    enabled: !!token,
  })
}

export function useWorkout(id: string) {
  const { token } = useAuth()
  return useQuery({
    queryKey: ['workouts', id],
    queryFn: async () => {
      const res = await fetch(`/api/workouts/${id}`, { headers: authHeaders(token ?? '') })
      if (!res.ok) throw new Error('Failed to fetch workout')
      return res.json() as Promise<Workout>
    },
    enabled: !!token && !!id,
  })
}

export function useCreateWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (data: WorkoutCreate) => {
      const res = await fetch('/api/workouts/', {
        method: 'POST',
        headers: authHeaders(token ?? ''),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to create workout')
      return res.json() as Promise<Workout>
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  })
}

export function useUpdateWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: WorkoutCreate }) => {
      const res = await fetch(`/api/workouts/${id}`, {
        method: 'PUT',
        headers: authHeaders(token ?? ''),
        body: JSON.stringify(data),
      })
      if (!res.ok) throw new Error('Failed to update workout')
      return res.json() as Promise<Workout>
    },
    onSuccess: (_, { id }) => {
      void qc.invalidateQueries({ queryKey: ['workouts'] })
      void qc.invalidateQueries({ queryKey: ['workouts', id] })
    },
  })
}

export function useDeleteWorkout() {
  const { token } = useAuth()
  const qc = useQueryClient()
  return useMutation({
    mutationFn: async (id: string) => {
      const res = await fetch(`/api/workouts/${id}`, {
        method: 'DELETE',
        headers: authHeaders(token ?? ''),
      })
      if (!res.ok) throw new Error('Failed to delete workout')
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ['workouts'] }),
  })
}
