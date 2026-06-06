import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useCreateWorkout } from '@/hooks/useWorkouts'
import { useExercises } from '@/hooks/useExercises'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import type { WorkoutPhase, SetType, WorkoutSequenceCreate, WorkoutSetCreate } from '@/types'

const PHASES: WorkoutPhase[] = ['warmup', 'main', 'cooldown']
const SET_TYPES: SetType[] = ['STRENGTH', 'CARDIO']

function toLocalDatetimeString(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}

interface DraftSet {
  exercise_id: string
  set_type: SetType
  reps: string
  weight_kg: string
  duration_s: string
}

interface DraftSequence {
  phase: WorkoutPhase
  sets: DraftSet[]
}

function emptySet(): DraftSet {
  return { exercise_id: '', set_type: 'STRENGTH', reps: '', weight_kg: '', duration_s: '' }
}

export default function WorkoutNewPage() {
  const navigate = useNavigate()
  const createWorkout = useCreateWorkout()
  const { data: exercises } = useExercises()

  const [startedAt, setStartedAt] = useState(() => toLocalDatetimeString(new Date()))
  const [sequences, setSequences] = useState<DraftSequence[]>([])

  const addSequence = () => {
    setSequences((prev) => [...prev, { phase: 'main', sets: [] }])
  }

  const updateSequencePhase = (idx: number, phase: WorkoutPhase) => {
    setSequences((prev) =>
      prev.map((seq, i) => (i === idx ? { ...seq, phase } : seq))
    )
  }

  const removeSequence = (idx: number) => {
    setSequences((prev) => prev.filter((_, i) => i !== idx))
  }

  const addSet = (seqIdx: number) => {
    setSequences((prev) =>
      prev.map((seq, i) =>
        i === seqIdx ? { ...seq, sets: [...seq.sets, emptySet()] } : seq
      )
    )
  }

  const updateSet = (seqIdx: number, setIdx: number, patch: Partial<DraftSet>) => {
    setSequences((prev) =>
      prev.map((seq, i) =>
        i === seqIdx
          ? {
              ...seq,
              sets: seq.sets.map((s, j) => (j === setIdx ? { ...s, ...patch } : s)),
            }
          : seq
      )
    )
  }

  const removeSet = (seqIdx: number, setIdx: number) => {
    setSequences((prev) =>
      prev.map((seq, i) =>
        i === seqIdx
          ? { ...seq, sets: seq.sets.filter((_, j) => j !== setIdx) }
          : seq
      )
    )
  }

  const handleSubmit = (e: React.SyntheticEvent<HTMLFormElement>) => {
    e.preventDefault()

    const payload = {
      started_at: new Date(startedAt).toISOString(),
      sequences: sequences.map((seq, seqPos): WorkoutSequenceCreate => ({
        phase: seq.phase,
        position: seqPos,
        sets: seq.sets.map((s, setPos): WorkoutSetCreate => {
          const base: WorkoutSetCreate = {
            exercise_id: s.exercise_id,
            set_type: s.set_type,
            position: setPos,
          }
          if (s.set_type === 'STRENGTH') {
            if (s.reps) base.reps = parseInt(s.reps)
            if (s.weight_kg) base.weight_kg = parseFloat(s.weight_kg)
          } else {
            if (s.duration_s) base.duration_s = parseInt(s.duration_s)
          }
          return base
        }),
      })),
    }

    createWorkout.mutate(payload, {
      onSuccess: () => { navigate('/workouts'); },
    })
  }

  return (
    <div className="container mx-auto py-8 space-y-6 max-w-2xl">
      <div className="flex items-center gap-4">
        <Link
          to="/workouts"
          className="inline-flex items-center justify-center rounded-md border px-3 py-1.5 text-sm font-medium shadow-sm hover:bg-accent"
        >
          ← Back
        </Link>
        <h1 className="text-3xl font-bold">New Workout</h1>
      </div>

      {createWorkout.isError && (
        <p className="text-sm text-destructive">
          {createWorkout.error instanceof Error
            ? createWorkout.error.message
            : 'Failed to create workout'}
        </p>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="space-y-1">
          <Label htmlFor="started-at">Start time</Label>
          <Input
            id="started-at"
            type="datetime-local"
            value={startedAt}
            onChange={(e) => { setStartedAt(e.target.value); }}
            required
          />
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold">Sequences</h2>
            <Button type="button" variant="outline" onClick={addSequence}>
              + Add Sequence
            </Button>
          </div>

          {sequences.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Add at least one sequence to record your workout.
            </p>
          )}

          {sequences.map((seq, seqIdx) => (
            <div key={seqIdx} className="border rounded-lg p-4 space-y-4">
              <div className="flex items-center justify-between gap-4">
                <div className="flex items-center gap-2">
                  <Label>Phase</Label>
                  <select
                    className="border rounded px-2 py-1 text-sm bg-background"
                    value={seq.phase}
                    onChange={(e) =>
                      { updateSequencePhase(seqIdx, e.target.value as WorkoutPhase); }
                    }
                  >
                    {PHASES.map((p) => (
                      <option key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    onClick={() => { addSet(seqIdx); }}
                  >
                    + Add Set
                  </Button>
                  <Button
                    type="button"
                    variant="destructive"
                    size="sm"
                    onClick={() => { removeSequence(seqIdx); }}
                  >
                    Remove
                  </Button>
                </div>
              </div>

              {seq.sets.map((s, setIdx) => (
                <div
                  key={setIdx}
                  className="grid grid-cols-2 gap-3 border-t pt-3"
                >
                  <div className="space-y-1 col-span-2">
                    <Label>Exercise</Label>
                    <select
                      className="w-full border rounded px-2 py-1 text-sm bg-background"
                      value={s.exercise_id}
                      required
                      onChange={(e) =>
                        { updateSet(seqIdx, setIdx, { exercise_id: e.target.value }); }
                      }
                    >
                      <option value="">Select exercise…</option>
                      {exercises?.map((ex) => (
                        <option key={ex.id} value={ex.id}>
                          {ex.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-1">
                    <Label>Type</Label>
                    <select
                      className="w-full border rounded px-2 py-1 text-sm bg-background"
                      value={s.set_type}
                      onChange={(e) =>
                        { updateSet(seqIdx, setIdx, { set_type: e.target.value as SetType }); }
                      }
                    >
                      {SET_TYPES.map((t) => (
                        <option key={t} value={t}>
                          {t}
                        </option>
                      ))}
                    </select>
                  </div>

                  {s.set_type === 'STRENGTH' ? (
                    <>
                      <div className="space-y-1">
                        <Label>Reps</Label>
                        <Input
                          type="number"
                          min="0"
                          placeholder="e.g. 8"
                          value={s.reps}
                          onChange={(e) =>
                            { updateSet(seqIdx, setIdx, { reps: e.target.value }); }
                          }
                        />
                      </div>
                      <div className="space-y-1">
                        <Label>Weight (kg)</Label>
                        <Input
                          type="number"
                          min="0"
                          step="0.5"
                          placeholder="e.g. 60"
                          value={s.weight_kg}
                          onChange={(e) =>
                            { updateSet(seqIdx, setIdx, { weight_kg: e.target.value }); }
                          }
                        />
                      </div>
                    </>
                  ) : (
                    <div className="space-y-1">
                      <Label>Duration (seconds)</Label>
                      <Input
                        type="number"
                        min="0"
                        placeholder="e.g. 1800"
                        value={s.duration_s}
                        onChange={(e) =>
                          { updateSet(seqIdx, setIdx, { duration_s: e.target.value }); }
                        }
                      />
                    </div>
                  )}

                  <div className="col-span-2 flex justify-end">
                    <Button
                      type="button"
                      variant="destructive"
                      size="sm"
                      onClick={() => { removeSet(seqIdx, setIdx); }}
                    >
                      Remove Set
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>

        <Button
          type="submit"
          className="w-full"
          disabled={createWorkout.isPending || sequences.length === 0}
        >
          {createWorkout.isPending ? 'Saving…' : 'Save Workout'}
        </Button>
      </form>
    </div>
  )
}
