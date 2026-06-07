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

export interface AgentStep {
  agent: string
  confidence?: number
  latency_ms?: number
  timestamp?: string
}

export interface WorkoutDraftExercise {
  id: string
  name: string
  sets: number
  reps: string | null
  duration_s: number | null
  rest_s: number
}

export interface WorkoutDraftPhases {
  warmup: WorkoutDraftExercise[]
  main: WorkoutDraftExercise[]
  cooldown: WorkoutDraftExercise[]
}

export interface WorkoutDraft {
  goal: string
  phases: WorkoutDraftPhases
  total_exercises: number
  invalid_ids_skipped: string[]
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  route?: string
  confidence?: number
  steps?: AgentStep[]
  workout_draft?: WorkoutDraft
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
  enjoyment?: number | null
  note?: string | null
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

// ── Coach copilot types ──────────────────────────────────────────────────────

export interface MorningTask {
  type: string
  text: string
}

export interface ChurnRisk {
  level: string
  reasons: string[]
}

export interface AdherenceWeek {
  week_of: string
  pct: number
}

export interface GoalItem {
  id: string
  text: string
  priority: number
  target_date: string | null
}

export interface InjuryItem {
  name: string
  region: string
  severity: string
  status: string
  notes: string | null
}

export interface CoachBriefResponse {
  member_id: string
  member_name: string
  member_age: number | null
  tier: string | null
  goals: GoalItem[]
  injuries: InjuryItem[]
  morning_tasks: MorningTask[]
  churn_risk: ChurnRisk
  adherence_weeks: AdherenceWeek[]
  equipment: string[]
}

export interface CoachChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  grounded_facts?: string[]
}

export interface CoachChatResponse {
  reply: string
  grounded_facts: string[]
  session_id: string
}

export interface Workout {
  id: string
  user_id: string
  started_at: string
  ended_at: string | null
  sequences: WorkoutSequence[]
  enjoyment?: number | null
  note?: string | null
}

export interface CoachChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  grounded_facts?: string[]
}

export interface CoachChatResponse {
  session_id: string
  reply: string
  grounded_facts: string[]
}

export interface GoalItem {
  id: string
  text: string
  priority: number
  target_date: string | null
}

export interface MorningTask {
  type: string
  text: string
}

export interface ChurnRisk {
  level: string
  reasons: string[]
}

export interface AdherenceWeek {
  week_of: string
  pct: number
}

export interface InjuryItem {
  region: string
  status: string
  notes: string
}

export interface CoachBriefResponse {
  member_id: string
  member_name: string
  member_age: number | null
  tier: string | null
  goals: GoalItem[]
  injuries: InjuryItem[]
  morning_tasks: MorningTask[]
  churn_risk: ChurnRisk
  adherence_weeks: AdherenceWeek[]
  equipment: string[]
}
