import { cn } from '@/lib/utils'
import type { WorkoutSequence, Exercise, WorkoutPhase } from '@/types'
import { FeedbackForm } from './FeedbackForm'

interface PhaseTableProps {
  sequences: WorkoutSequence[]
  exercises?: Exercise[]
  /** When provided alongside workoutId, renders a compact rating button per set row */
  memberId?: string
  workoutId?: string
  onAddCurrent?: (exerciseId: string) => void
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

export function PhaseTable({ sequences, exercises = [], memberId, workoutId, onAddCurrent }: PhaseTableProps) {
  const exerciseById = new Map(exercises.map((ex) => [ex.id, ex]))
  const showFeedback = memberId != null && workoutId != null

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
                        style={{ borderBottom: '1px solid var(--border)' }}
                      >
                        <td style={{ padding: 'var(--space-2-5) var(--space-3)' }}>
                          <div style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>{name}</div>
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
                          <span
                            className={cn(
                              'ww-badge',
                              set.set_type === 'CARDIO' ? 'ww-badge--amber' : 'ww-badge--soft',
                            )}
                          >
                            {set.set_type}
                          </span>
                        </td>
                        <td style={{ padding: 'var(--space-2-5) var(--space-3)' }}>
                          <span className="ww-num">{formatPrescription(set)}</span>
                        </td>
                        {showFeedback && (
                          <td style={{ padding: 'var(--space-2-5) var(--space-3)', textAlign: 'center' }}>
                            <FeedbackForm
                              compact
                              exerciseId={set.exercise_id}
                              memberId={memberId!}
                              workoutId={workoutId}
                              workoutSetId={set.id}
                              contextType="exercise"
                            />
                          </td>
                        )}
                        {onAddCurrent && (
                          <td style={{ padding: 'var(--space-2-5) var(--space-3)', textAlign: 'right' }}>
                            <button
                              type="button"
                              className="ww-btn ww-btn--outline ww-btn--sm ww-iconbtn"
                              title="Add to current workout"
                              onClick={() => { onAddCurrent(set.exercise_id) }}
                            >
                              +
                            </button>
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
