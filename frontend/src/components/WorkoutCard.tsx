import { Link } from 'react-router-dom'
import type { Workout } from '@/types'

interface WorkoutCardProps {
  workout: Workout
  to: string
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

export function WorkoutCard({ workout, to }: WorkoutCardProps) {
  const phaseCount = workout.sequences.length
  const setCount = workout.sequences.reduce(
    (acc, seq) => acc + (seq.sets?.length ?? 0),
    0,
  )

  return (
    <Link
      to={to}
      className="ww-card ww-card--interactive"
      style={{ textDecoration: 'none', color: 'inherit' }}
    >
      <div className="ww-card__body">
        <div
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-semibold)',
            marginBottom: 'var(--space-1)',
          }}
        >
          {formatDate(workout.started_at)}
        </div>
        <div
          style={{
            fontSize: 'var(--text-xs)',
            color: 'var(--muted-foreground)',
          }}
        >
          <span className="ww-num">{phaseCount}</span> phase{phaseCount !== 1 ? 's' : ''}
          {' · '}
          <span className="ww-num">{setCount}</span> set{setCount !== 1 ? 's' : ''}
        </div>
      </div>
    </Link>
  )
}
