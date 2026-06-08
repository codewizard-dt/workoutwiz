import { useState, useEffect, useCallback } from 'react'
import type { WorkoutSequence, WorkoutSet } from '@/types'

const KEY = 'ww_draft_sequences'

function read(): WorkoutSequence[] {
  try {
    const raw = localStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as WorkoutSequence[]) : []
  } catch {
    return []
  }
}

function persist(sequences: WorkoutSequence[]) {
  if (sequences.length === 0) {
    localStorage.removeItem(KEY)
  } else {
    localStorage.setItem(KEY, JSON.stringify(sequences))
  }
  window.dispatchEvent(new CustomEvent('ww:draft-updated'))
}

export function useDraftWorkout() {
  const [sequences, setLocal] = useState<WorkoutSequence[]>(read)

  // Sync when another page writes to the draft
  useEffect(() => {
    const sync = () => { setLocal(read()) }
    window.addEventListener('ww:draft-updated', sync)
    return () => { window.removeEventListener('ww:draft-updated', sync) }
  }, [])

  const setSequences = useCallback((next: WorkoutSequence[]) => {
    setLocal(next)
    persist(next)
  }, [])

  const addExercise = useCallback((exerciseId: string, isCardio = false) => {
    setLocal((prev) => {
      const mainIdx = prev.findIndex((s) => s.phase === 'main')
      const existingSets = mainIdx >= 0 ? prev[mainIdx].sets : []
      const newSet: WorkoutSet = {
        id: `draft-${Date.now()}`,
        sequence_id: 'draft-main',
        exercise_id: exerciseId,
        set_type: isCardio ? 'CARDIO' : 'STRENGTH',
        position: existingSets.length * 100,
        reps: isCardio ? undefined : 10,
        weight_kg: undefined,
        duration_s: isCardio ? 60 : undefined,
      }
      const next =
        mainIdx >= 0
          ? prev.map((s, i) =>
              i === mainIdx ? { ...s, sets: [...s.sets, newSet] } : s,
            )
          : [
              ...prev,
              {
                id: 'draft-main',
                workout_id: 'draft',
                phase: 'main' as const,
                position: 0,
                sets: [newSet],
              },
            ]
      persist(next)
      return next
    })
  }, [])

  const clear = useCallback(() => {
    setLocal([])
    localStorage.removeItem(KEY)
    localStorage.removeItem('ww_workout_draft')
    window.dispatchEvent(new CustomEvent('ww:draft-updated'))
  }, [])

  return { sequences, setSequences, addExercise, clear }
}
