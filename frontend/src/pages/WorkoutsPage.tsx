import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useWorkouts, useDeleteWorkout } from '@/hooks/useWorkouts'
import type { Workout } from '@/types'
import { DeleteConfirmModal } from '@/components/DeleteConfirmModal'

const EMOJI: Record<number, string> = { 1: '😞', 2: '😟', 3: '😐', 4: '🙂', 5: '😄' }

function dominantType(workout: Workout): 'STRENGTH' | 'CARDIO' | '—' {
  let strength = 0, cardio = 0
  for (const seq of workout.sequences) {
    for (const set of seq.sets) {
      if (set.set_type === 'STRENGTH') strength++
      else if (set.set_type === 'CARDIO') cardio++
    }
  }
  if (strength === 0 && cardio === 0) return '—'
  return strength >= cardio ? 'STRENGTH' : 'CARDIO'
}

export default function WorkoutsPage() {
  const { data: workouts, isLoading, isError } = useWorkouts()
  const deleteWorkout = useDeleteWorkout()
  const [deleteTarget, setDeleteTarget] = useState<string | null>(null)
  const navigate = useNavigate()

  const handleDelete = () => {
    if (!deleteTarget) return
    deleteWorkout.mutate(deleteTarget, {
      onSuccess: () => { setDeleteTarget(null) },
    })
  }

  return (
    <div
      style={{
        padding: 'var(--space-6) var(--space-4)',
        maxWidth: 900,
        margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-5)',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--space-3)' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 'var(--text-2xl)', fontWeight: 'var(--weight-semibold)' }}>
            Workouts
          </h1>
          <p style={{ margin: 'var(--space-1) 0 0', fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>
            Every session you've planned or logged.
          </p>
        </div>
        <Link to="/workouts/new" style={{ textDecoration: 'none' }}>
          <button type="button" className="ww-btn ww-btn--gradient">
            New Workout
          </button>
        </Link>
      </div>

      {isLoading && (
        <p style={{ color: 'var(--muted-foreground)', fontSize: 'var(--text-sm)' }}>Loading workouts…</p>
      )}
      {isError && (
        <p style={{ color: 'var(--destructive)', fontSize: 'var(--text-sm)' }}>Failed to load workouts.</p>
      )}

      {workouts && workouts.length === 0 && (
        <div
          style={{
            textAlign: 'center',
            padding: 'var(--space-12) var(--space-4)',
            color: 'var(--muted-foreground)',
          }}
        >
          <p style={{ marginBottom: 'var(--space-4)', fontSize: 'var(--text-sm)' }}>
            No workouts yet.
          </p>
          <div style={{ display: 'flex', gap: 'var(--space-3)', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link to="/workouts/new" style={{ textDecoration: 'none' }}>
              <button type="button" className="ww-btn ww-btn--gradient">New workout</button>
            </Link>
            <button
              type="button"
              className="ww-btn ww-btn--outline"
              onClick={() => { navigate('/chat') }}
            >
              Ask the coach
            </button>
          </div>
        </div>
      )}

      {workouts && workouts.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)' }}>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)', width: '44%' }}>
                  Date
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Sets
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Type
                </th>
                <th style={{ textAlign: 'left', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Feels
                </th>
                <th style={{ textAlign: 'right', padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)', color: 'var(--muted-foreground)' }}>
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {workouts.map((w) => {
                const totalSets = w.sequences.reduce(
                  (acc, seq) => acc + seq.sets.length,
                  0
                )
                return (
                  <tr
                    key={w.id}
                    style={{ borderBottom: '1px solid var(--border)' }}
                  >
                    <td style={{ padding: 'var(--space-3)', fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-medium)' }}>
                      {new Date(w.started_at).toLocaleString()}
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      <span className="ww-num">{totalSets}</span>
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      {(() => {
                        const dt = dominantType(w)
                        if (dt === '—') return <span>—</span>
                        return (
                          <span className={dt === 'STRENGTH' ? 'ww-badge ww-badge--secondary' : 'ww-badge ww-badge--amber'}>
                            {dt}
                          </span>
                        )
                      })()}
                    </td>
                    <td style={{ padding: 'var(--space-3)' }}>
                      {w.enjoyment != null ? EMOJI[w.enjoyment] ?? '—' : '—'}
                    </td>
                    <td style={{ padding: 'var(--space-3)', textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 'var(--space-2)', justifyContent: 'flex-end', alignItems: 'center' }}>
                        <Link
                          to={`/workouts/${w.id}`}
                          style={{ textDecoration: 'none' }}
                        >
                          <button type="button" className="ww-btn ww-btn--outline ww-btn--sm">
                            View
                          </button>
                        </Link>
                        <button
                          type="button"
                          className="ww-btn ww-btn--destructive ww-btn--sm"
                          disabled={deleteWorkout.isPending}
                          onClick={() => { setDeleteTarget(w.id) }}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}

      <DeleteConfirmModal
        open={!!deleteTarget}
        title="Delete workout"
        description="This will permanently remove this workout and all its sets. This cannot be undone."
        onConfirm={handleDelete}
        onCancel={() => { setDeleteTarget(null) }}
        loading={deleteWorkout.isPending}
      />
    </div>
  )
}
