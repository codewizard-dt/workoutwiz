import { Link } from 'react-router-dom'
import { Frown, Annoyed, Meh, Smile, Laugh, type LucideIcon } from 'lucide-react'
import type { Workout } from '@/types'

interface WorkoutCardProps {
  workout: Workout
  to: string
}

const FACE: Record<number, LucideIcon> = { 1: Frown, 2: Annoyed, 3: Meh, 4: Smile, 5: Laugh }
// Sentiment scale: red (poor) → grey (neutral) → green (great)
const FACE_COLOR: Record<number, string> = { 1: '#b91c1c', 2: '#82383f', 3: '#4b5563', 4: '#306a50', 5: '#15803d' }

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function dominantType(workout: Workout): 'STRENGTH' | 'CARDIO' | null {
  let strength = 0, cardio = 0
  for (const seq of workout.sequences) {
    for (const set of seq.sets) {
      if (set.set_type === 'STRENGTH') strength++
      else cardio++
    }
  }
  if (strength === 0 && cardio === 0) return null
  return strength >= cardio ? 'STRENGTH' : 'CARDIO'
}

export function WorkoutCard({ workout, to }: WorkoutCardProps) {
  const setCount = workout.sequences.reduce((acc, seq) => acc + seq.sets.length, 0)
  const type = dominantType(workout)

  const exerciseCount = new Set(
    workout.sequences.flatMap((seq) => seq.sets.map((s) => s.exercise_id))
  ).size

  const durationMin =
    workout.ended_at
      ? Math.round((new Date(workout.ended_at).getTime() - new Date(workout.started_at).getTime()) / 60000)
      : null

  return (
    <Link
      to={to}
      className="ww-card ww-card--interactive"
      style={{ textDecoration: 'none', color: 'inherit', margin: "var(--space-2) var(--space-1)" }}
    >
      <div className="ww-card__body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
        <div
          style={{
            fontSize: 'var(--text-sm)',
            fontWeight: 'var(--weight-semibold)',
            marginBottom: 'var(--space-0-5)',
          }}
        >
          {formatDate(workout.started_at)}
        </div>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            flexWrap: 'wrap',
          }}
        >
          {type && (
            <span
              className={type === 'STRENGTH' ? 'ww-badge ww-badge--secondary' : 'ww-badge ww-badge--amber'}
              style={{ fontSize: '10px' }}
            >
              {type}
            </span>
          )}
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
            <span className="ww-num">{exerciseCount}</span> ex · <span className="ww-num">{setCount}</span> set{setCount !== 1 ? 's' : ''}
          </span>
          {durationMin != null && durationMin > 0 && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
              <span className="ww-num">{durationMin}</span> min
            </span>
          )}
          {workout.enjoyment != null && (() => {
            const Face = FACE[workout.enjoyment]
            return (
              <span style={{ display: 'inline-flex' }} title="Feels">
                <Face size={16} color={FACE_COLOR[workout.enjoyment]} aria-hidden />
              </span>
            )
          })()}
        </div>
        {workout.note && (
          <p
            style={{
              fontSize: 'var(--text-xs)',
              color: 'var(--muted-foreground)',
              margin: 0,
              lineHeight: 1.4,
            }}
          >
            {workout.note}
          </p>
        )}
      </div>
    </Link>
  )
}
