export interface User {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  is_verified: boolean
}

export interface Exercise {
  id: string
  name: string
  category: string | null
  muscle_groups: string[]
  equipment_required: string[]
  movement_patterns: string[]
  is_reps: boolean
  is_duration: boolean
  supports_weight: boolean
  is_bilateral: boolean
  bilateral_pair_id: string | null
  priority_tier: number
  description: string | null
}

export type WorkoutPhase = 'warmup' | 'main' | 'cooldown'
export type SetType = 'STRENGTH' | 'CARDIO'

export interface WorkoutSetCreate {
  exercise_id: string
  set_type: SetType
  position?: number
  reps?: number | null
  weight_kg?: number | null
  duration_s?: number | null
  speed?: number | null
  distance?: number | null
  calories?: number | null
}

export interface WorkoutSequenceCreate {
  phase: WorkoutPhase
  position?: number
  sets?: WorkoutSetCreate[]
}

export interface WorkoutCreate {
  started_at: string
  ended_at?: string | null
  sequences?: WorkoutSequenceCreate[]
}

export interface WorkoutSet extends WorkoutSetCreate {
  id: string
  sequence_id: string
}

export interface WorkoutSequence extends WorkoutSequenceCreate {
  id: string
  workout_id: string
  sets: WorkoutSet[]
}

export interface Workout {
  id: string
  user_id: string
  started_at: string
  ended_at: string | null
  sequences: WorkoutSequence[]
}
