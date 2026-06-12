import { useState } from 'react'
import { CheckCircle2, Plus, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { WorkoutSequence, Exercise, WorkoutPhase } from '@/types'
import { useKGFeedbackList } from '@/hooks/useKGFeedbackList'
import { FeedbackForm } from './FeedbackForm'

interface PhaseTableProps {
  sequences: WorkoutSequence[]
  exercises?: Exercise[]
  /** When provided alongside workoutId, renders a compact rating button per set row */
  memberId?: string
  workoutId?: string
  onAddCurrent?: (exerciseId: string) => void
  onRemoveSet?: (setId: string) => void
}

const PHASE_ORDER: WorkoutPhase[] = ['warmup', 'main', 'cooldown']

const PHASE_LABEL: Record<WorkoutPhase, string> = {
  warmup: 'Warm-up',
  main: 'Main',
  cooldown: 'Cool-down',
}

function formatPrescription(set: WorkoutSequence['sets'][number]): string {
  if (set.set_type === 'STRENGTH') {
    const parts: string[] = []
    if (set.reps != null) parts.push(`${set.reps} reps`)
    if (set.weight_kg != null) parts.push(`${set.weight_kg} kg`)
    return parts.join(' × ') || '—'
  }
  if (set.duration_s != null) {
    const mins = Math.floor(set.duration_s / 60)
    const secs = set.duration_s % 60
    return mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
  }
  return '—'
}

export function PhaseTable({ sequences, exercises = [], memberId, workoutId, onAddCurrent, onRemoveSet }: PhaseTableProps) {
  const exerciseById = new Map(exercises.map((ex) => [ex.id, ex]))
  const showFeedback = memberId != null && workoutId != null
  const { data: savedRatings } = useKGFeedbackList(showFeedback ? workoutId : undefined)
  const [added, setAdded] = useState<Set<string>>(new Set())

  const ordered = PHASE_ORDER.flatMap((phase) => {
    const seq = sequences.find((s) => s.phase === phase)
    return seq ? [seq] : []
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
      {ordered.map((seq) => {
        const sortedSets = [...seq.sets].sort(
          (a, b) => (a.position ?? 0) - (b.position ?? 0),
        )

        // Stripe by exercise group: all sets for the same exercise share a color,
        // toggling when the exercise changes.
        let stripeIdx = -1
        let lastExId: string | null = null
        const stripeBySetId = new Map(sortedSets.map((s) => {
          if (s.exercise_id !== lastExId) { stripeIdx++; lastExId = s.exercise_id }
          return [s.id, stripeIdx % 2 === 1]
        }))

        return (
          <div key={seq.phase}>
            <div
              className="ww-eyebrow"
              style={{ marginBottom: 'var(--space-2)', fontSize: 'var(--text-xs)', fontWeight: 'var(--weight-semibold)', textTransform: 'uppercase', letterSpacing: 'var(--tracking-caps)', color: 'var(--muted-foreground)' }}
            >
              {PHASE_LABEL[seq.phase]}
            </div>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border)' }}>
                    <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)', width: '42%' }}>Exercise</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>Type</th>
                    <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>Prescription</th>
                    {showFeedback && (
                      <th style={{ textAlign: 'center', padding: 'var(--space-2) var(--space-3)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>Feel</th>
                    )}
                    {onAddCurrent && (
                      <th style={{ textAlign: 'right', padding: 'var(--space-2) var(--space-3)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>Add to current workout</th>
                    )}
                    {onRemoveSet && <th style={{ width: '2.5rem' }} />}
                  </tr>
                </thead>
                <tbody>
                  {sortedSets.map((set) => {
                    const ex = exerciseById.get(set.exercise_id)
                    const name = ex?.name ?? set.exercise_id

                    return (
                      <tr
                        key={set.id}
                        className="ww-set-row"
                        style={{ borderBottom: '1px solid var(--border)', background: stripeBySetId.get(set.id) ? 'var(--stone-100)' : undefined }}
                      >
                        <td style={{ padding: 'var(--space-2-5) var(--space-3)' }}>
                          <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>{name}</div>
                        </td>
                        <td style={{ padding: 'var(--space-2-5) var(--space-3)' }}>
                          <span
                            className={cn(
                              'ww-badge',
                              set.set_type === 'CARDIO' ? 'ww-badge--amber' : 'ww-badge--soft',
                            )}
                          >
                            {set.set_type}
                          </span>
                          {ex && (
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1)', marginTop: 'var(--space-1)' }}>
                              {ex.category && (
                                <span className="ww-badge ww-badge--outline" style={{ fontSize: '10px' }}>{ex.category}</span>
                              )}
                              {ex.muscle_groups.slice(0, 3).map((mg) => (
                                <span key={mg} className="ww-badge ww-badge--secondary" style={{ fontSize: '10px' }}>{mg}</span>
                              ))}
                            </div>
                          )}
                        </td>
                        <td style={{ padding: 'var(--space-2-5) var(--space-3)' }}>
                          <span className="ww-num">{formatPrescription(set)}</span>
                        </td>
                        {showFeedback && (
                          <td style={{ padding: 'var(--space-2-5) var(--space-3)', textAlign: 'center' }}>
                            <FeedbackForm
                              compact
                              exerciseId={set.exercise_id}
                              memberId={memberId}
                              workoutId={workoutId}
                              workoutSetId={set.id}
                              contextType="exercise"
                              initialRating={savedRatings?.[set.id] ?? null}
                            />
                          </td>
                        )}
                        {onRemoveSet && (
                          <td style={{ padding: 'var(--space-2-5) var(--space-2)', textAlign: 'center' }}>
                            <button
                              type="button"
                              className="ww-btn ww-btn--ghost ww-iconbtn ww-btn--sm"
                              style={{ color: 'var(--muted-foreground)' }}
                              title="Remove set"
                              onClick={() => { onRemoveSet(set.id) }}
                            >
                              <X size={14} aria-hidden />
                            </button>
                          </td>
                        )}
                        {onAddCurrent && (
                          <td style={{ padding: 'var(--space-2-5) var(--space-3)', textAlign: 'right' }}>
                            {added.has(set.exercise_id) ? (
                              <button
                                type="button"
                                className="ww-btn ww-iconbtn"
                                style={{
                                  background: 'var(--success-100)',
                                  border: '1px solid var(--success-500)',
                                  color: 'var(--success-500)',
                                  width: '2.25rem',
                                  height: '2.25rem',
                                }}
                                title="Added to workout"
                                disabled
                              >
                                <CheckCircle2 size={18} aria-hidden />
                              </button>
                            ) : (
                              <button
                                type="button"
                                className="ww-btn ww-btn--primary ww-iconbtn"
                                style={{ width: '2.25rem', height: '2.25rem' }}
                                title="Add to current workout"
                                onClick={() => {
                                  onAddCurrent(set.exercise_id)
                                  setAdded((prev) => new Set(prev).add(set.exercise_id))
                                }}
                              >
                                <Plus size={18} aria-hidden />
                              </button>
                            )}
                          </td>
                        )}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )
      })}
    </div>
  )
}
