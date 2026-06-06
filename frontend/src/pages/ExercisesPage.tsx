import { useState, useEffect } from 'react'
import { useExercises } from '@/hooks/useExercises'
import type { Exercise } from '@/types'

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => { setDebounced(value); }, delay)
    return () => { clearTimeout(t); }
  }, [value, delay])
  return debounced
}

interface AddDraftSet {
  exercise_id: string
  sets: number
  reps: number | null
  weight_kg: number | null
  duration_s: number | null
  weight_unit: 'kg' | 'lb'
}

interface AddExerciseModalProps {
  exercise: Exercise
  onClose: () => void
  onAdd: (draft: AddDraftSet) => void
}

function AddExerciseModal({ exercise, onClose, onAdd }: AddExerciseModalProps) {
  const isCardio = !exercise.is_reps && exercise.is_duration
  const isStrength = exercise.is_reps

  const [sets, setSets] = useState(isCardio ? 1 : 3)
  const [reps, setReps] = useState<number | ''>(isStrength ? 10 : '')
  const [weightKg, setWeightKg] = useState<number | ''>('')
  const [durationS, setDurationS] = useState<number | ''>(isCardio ? 300 : '')
  const [weightUnit, setWeightUnit] = useState<'kg' | 'lb'>('kg')
  const [added, setAdded] = useState(false)

  const warnings: string[] = []
  if (exercise.equipment_required.length > 0) {
    warnings.push(`This exercise requires ${exercise.equipment_required.join(', ')} equipment.`)
  }

  const handleAdd = () => {
    const draft: AddDraftSet = {
      exercise_id: exercise.id,
      sets: Number(sets) || 1,
      reps: isStrength ? (Number(reps) || null) : null,
      weight_kg: exercise.supports_weight && weightKg !== '' ? Number(weightKg) : null,
      duration_s: isCardio ? (Number(durationS) || null) : null,
      weight_unit: weightUnit,
    }

    // Persist to localStorage draft
    const DRAFT_KEY = 'ww_workout_draft'
    const existing = JSON.parse(localStorage.getItem(DRAFT_KEY) ?? '[]') as AddDraftSet[]
    localStorage.setItem(DRAFT_KEY, JSON.stringify([...existing, draft]))
    window.dispatchEvent(new CustomEvent('ww:draft-updated'))

    onAdd(draft)
    setAdded(true)
    setTimeout(onClose, 800)
  }

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 50,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'oklch(0 0 0 / 0.45)',
      }}
      onClick={onClose}
    >
      <div
        className="ww-card"
        style={{ width: 420, maxWidth: '90vw', padding: 'var(--space-5)' }}
        onClick={(e) => { e.stopPropagation() }}
      >
        <h3
          style={{
            margin: '0 0 var(--space-1)',
            fontSize: 'var(--text-md)',
            fontWeight: 'var(--weight-semibold)',
          }}
        >
          Add {exercise.name}
        </h3>
        <p
          style={{
            margin: '0 0 var(--space-4)',
            fontSize: 'var(--text-xs)',
            color: 'var(--muted-foreground)',
          }}
        >
          {exercise.id} · Confirm the prescription to add to your workout draft.
        </p>

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: 'auto 1fr',
            gap: 'var(--space-2) var(--space-4)',
            alignItems: 'center',
            marginBottom: 'var(--space-4)',
          }}
        >
          <label style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>Sets</label>
          <input
            type="number"
            className="ww-input"
            style={{ maxWidth: 110 }}
            min={1}
            value={sets}
            onChange={(e) => { setSets(Number(e.target.value)) }}
          />

          {isStrength && (
            <>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>Reps</label>
              <input
                type="number"
                className="ww-input"
                style={{ maxWidth: 110 }}
                min={1}
                placeholder="10"
                value={reps}
                onChange={(e) => { setReps(e.target.value === '' ? '' : Number(e.target.value)) }}
              />
            </>
          )}

          {isCardio && (
            <>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>Duration (sec)</label>
              <input
                type="number"
                className="ww-input"
                style={{ maxWidth: 110 }}
                min={1}
                placeholder="300"
                value={durationS}
                onChange={(e) => { setDurationS(e.target.value === '' ? '' : Number(e.target.value)) }}
              />
            </>
          )}

          {exercise.supports_weight && (
            <>
              <label style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>Weight</label>
              <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                <input
                  type="number"
                  className="ww-input"
                  style={{ maxWidth: 110 }}
                  min={0}
                  step={2.5}
                  placeholder="0"
                  value={weightKg}
                  onChange={(e) => { setWeightKg(e.target.value === '' ? '' : Number(e.target.value)) }}
                />
                <select
                  className="ww-input"
                  style={{ maxWidth: 70 }}
                  value={weightUnit}
                  onChange={(e) => { setWeightUnit(e.target.value as 'kg' | 'lb') }}
                >
                  <option value="kg">kg</option>
                  <option value="lb">lb</option>
                </select>
              </div>
            </>
          )}
        </div>

        {warnings.length > 0 && (
          <div
            style={{
              marginBottom: 'var(--space-4)',
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              background: 'oklch(0.97 0.08 85)',
              border: '1px solid oklch(0.88 0.10 85)',
              fontSize: 'var(--text-sm)',
              color: 'oklch(0.45 0.10 60)',
            }}
          >
            <div style={{ fontWeight: 'var(--weight-semibold)', marginBottom: 'var(--space-1)' }}>Warnings</div>
            {warnings.map((w, i) => (
              <div key={i}>{w}</div>
            ))}
          </div>
        )}

        {added && (
          <div
            style={{
              marginBottom: 'var(--space-3)',
              padding: 'var(--space-2) var(--space-3)',
              borderRadius: 'var(--radius-md)',
              background: 'oklch(0.96 0.06 145)',
              color: 'oklch(0.38 0.12 145)',
              fontSize: 'var(--text-sm)',
              fontWeight: 'var(--weight-medium)',
            }}
          >
            Added to workout draft!
          </div>
        )}

        <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end' }}>
          <button type="button" className="ww-btn ww-btn--outline" onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            className="ww-btn ww-btn--gradient"
            onClick={handleAdd}
            disabled={added}
          >
            Add to workout
          </button>
        </div>
      </div>
    </div>
  )
}

export default function ExercisesPage() {
  const [nameInput, setNameInput] = useState('')
  const [muscleInput, setMuscleInput] = useState('')
  const [equipmentInput, setEquipmentInput] = useState('')
  const [addTarget, setAddTarget] = useState<Exercise | null>(null)

  const debouncedName = useDebounce(nameInput, 300)
  const debouncedMuscle = useDebounce(muscleInput, 300)
  const debouncedEquipment = useDebounce(equipmentInput, 300)

  const filters = {
    name: debouncedName || undefined,
    muscle_groups: debouncedMuscle
      ? debouncedMuscle.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined,
    equipment: debouncedEquipment
      ? debouncedEquipment.split(',').map((s) => s.trim()).filter(Boolean)
      : undefined,
  }

  const { data: exercises, isLoading, isError } = useExercises(filters)

  return (
    <div
      style={{
        padding: 'var(--space-6) var(--space-4)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-5)',
      }}
    >
      <div>
        <h1 style={{ margin: '0 0 var(--space-1)', fontSize: 'var(--text-2xl)', fontWeight: 'var(--weight-semibold)' }}>
          Exercises
        </h1>
        <p style={{ margin: 0, fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
          The movement dataset used to ground every plan and log.
        </p>
      </div>

      {/* Filters */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
          gap: 'var(--space-3)',
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
          <label
            htmlFor="name-filter"
            style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
          >
            Name
          </label>
          <input
            id="name-filter"
            className="ww-input"
            placeholder="Search by name…"
            value={nameInput}
            onChange={(e) => { setNameInput(e.target.value) }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
          <label
            htmlFor="muscle-filter"
            style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
          >
            Muscle groups
          </label>
          <input
            id="muscle-filter"
            className="ww-input"
            placeholder="e.g. chest, triceps"
            value={muscleInput}
            onChange={(e) => { setMuscleInput(e.target.value) }}
          />
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
          <label
            htmlFor="equipment-filter"
            style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}
          >
            Equipment
          </label>
          <input
            id="equipment-filter"
            className="ww-input"
            placeholder="e.g. barbell, dumbbell"
            value={equipmentInput}
            onChange={(e) => { setEquipmentInput(e.target.value) }}
          />
        </div>
      </div>

      {isLoading && (
        <p style={{ color: 'var(--muted-foreground)', fontSize: 'var(--text-sm)' }}>Loading exercises…</p>
      )}
      {isError && (
        <p style={{ color: 'var(--destructive)', fontSize: 'var(--text-sm)' }}>Failed to load exercises.</p>
      )}

      {exercises && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)', width: '36%' }}>
                  Name
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Category
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Muscle Groups
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Equipment
                </th>
                <th style={{ textAlign: 'right', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {exercises.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    style={{
                      textAlign: 'center',
                      padding: 'var(--space-8)',
                      color: 'var(--muted-foreground)',
                      fontSize: 'var(--text-sm)',
                    }}
                  >
                    No exercises found.
                  </td>
                </tr>
              ) : (
                exercises.map((ex) => (
                  <tr
                    key={ex.id}
                    className="ww-set-row"
                    style={{ borderBottom: '1px solid var(--border)' }}
                  >
                    <td style={{ padding: 'var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>
                      {ex.name}
                    </td>
                    <td style={{ padding: 'var(--space-3)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
                      {ex.category ?? '—'}
                    </td>
                    <td style={{ padding: 'var(--space-3)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
                      {ex.muscle_groups.join(', ') || '—'}
                    </td>
                    <td style={{ padding: 'var(--space-3)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
                      {ex.equipment_required.join(', ') || '—'}
                    </td>
                    <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                      <button
                        type="button"
                        className="ww-btn ww-btn--outline ww-btn--sm"
                        onClick={() => { setAddTarget(ex) }}
                      >
                        Add
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}

      {addTarget && (
        <AddExerciseModal
          exercise={addTarget}
          onClose={() => { setAddTarget(null) }}
          onAdd={() => { /* draft is stored in localStorage inside modal */ }}
        />
      )}
    </div>
  )
}
