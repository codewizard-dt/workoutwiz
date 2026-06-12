export type ModalityKey = 'reps' | 'duration' | 'weight'

export interface ExerciseFilterState {
  name: string
  muscles: string[]
  equipment: string[]
  patterns: string[]
  modality: ModalityKey[]
  tier: number | null
}

export const EMPTY_FILTERS: ExerciseFilterState = {
  name: '',
  muscles: [],
  equipment: [],
  patterns: [],
  modality: [],
  tier: null,
}
