import { useState } from 'react'
import type { Exercise } from '@/types'

export interface AddDraftSet {
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

const DRAFT_KEY = 'ww_workout_draft'

export function AddExerciseModal({ exercise, onClose, onAdd }: AddExerciseModalProps) {
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
      sets: sets || 1,
      reps: isStrength ? (Number(reps) || null) : null,
      weight_kg: exercise.supports_weight && weightKg !== '' ? (weightKg as number) : null,
      duration_s: isCardio ? (Number(durationS) || null) : null,
      weight_unit: weightUnit,
    }

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
        zIndex: 70,
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
          Confirm the prescription for <strong>{exercise.name}</strong> to add to your workout draft.
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
              background: 'var(--warning-100)',
              border: '1px solid var(--warning-500)',
              fontSize: 'var(--text-sm)',
              color: 'var(--warning-500)',
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
              background: 'var(--success-100)',
              color: 'var(--success-500)',
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
