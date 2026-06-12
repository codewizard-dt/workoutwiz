import { Link } from 'react-router-dom'
import { Frown, Annoyed, Meh, Smile, Laugh, type LucideIcon } from 'lucide-react'
import type { Workout } from '@/types'

interface WorkoutCardProps {
  workout: Workout
  to: string
}

const FACE: Record<number, LucideIcon> = { 1: Frown, 2: Annoyed, 3: Meh, 4: Smile, 5: Laugh }
const FACE_COLOR: Record<number, string> = {
  1: 'var(--danger-500)',
  2: 'color-mix(in srgb, var(--danger-500) 60%, var(--muted-foreground))',
  3: 'var(--muted-foreground)',
  4: 'var(--success-500)',
  5: 'var(--success-500)',
}

function formatDate(iso: string): string {
  const d = new Date(iso)
  const sameYear = d.getFullYear() === new Date().getFullYear()
  return d.toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric',
    ...(sameYear ? {} : { year: 'numeric' }),
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
  const sequences = workout.sequences
  const setCount = sequences.reduce((acc, seq) => acc + seq.sets.length, 0)
  const type = dominantType(workout)
  const exerciseCount = new Set(sequences.flatMap((seq) => seq.sets.map((s) => s.exercise_id))).size
  const durationMin = workout.ended_at
    ? Math.round((new Date(workout.ended_at).getTime() - new Date(workout.started_at).getTime()) / 60000)
    : null
  const hasStats = setCount > 0 || (durationMin != null && durationMin > 0)

  return (
    <Link
      to={to}
      style={{
        textDecoration: 'none',
        color: 'inherit',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-1)',
        padding: 'var(--space-2) var(--space-3)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border)',
        background: 'var(--card)',
        transition: 'background var(--dur-fast) var(--ease-out), border-color var(--dur-fast) var(--ease-out)',
      }}
      onMouseEnter={(e) => {
        const el = e.currentTarget
        el.style.background = 'var(--surface-sunken)'
        el.style.borderColor = 'var(--border-strong)'
      }}
      onMouseLeave={(e) => {
        const el = e.currentTarget
        el.style.background = 'var(--card)'
        el.style.borderColor = 'var(--border)'
      }}
    >
      {/* Date + type badge row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 'var(--space-2)' }}>
        <span style={{ fontSize: 'var(--text-sm)', fontWeight: 'var(--weight-semibold)' }}>
          {formatDate(workout.started_at)}
        </span>
        {type && (
          <span
            className={type === 'STRENGTH' ? 'ww-badge ww-badge--secondary' : 'ww-badge ww-badge--amber'}
            style={{ fontSize: '10px' }}
          >
            {type}
          </span>
        )}
      </div>

      {/* Stats row — only when data is present */}
      {hasStats && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
          {setCount > 0 && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
              <span className="ww-num">{exerciseCount}</span> ex · <span className="ww-num">{setCount}</span> sets
            </span>
          )}
          {durationMin != null && durationMin > 0 && (
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
              <span className="ww-num">{durationMin}</span> min
            </span>
          )}
          {workout.enjoyment != null && (() => {
            const Face = FACE[workout.enjoyment]
            return <Face size={13} color={FACE_COLOR[workout.enjoyment]} aria-hidden />
          })()}
        </div>
      )}

      {/* Note preview */}
      {workout.note && (
        <p style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)', margin: 0, lineHeight: 1.4 }}>
          {workout.note.slice(0, 60)}{workout.note.length > 60 ? '…' : ''}
        </p>
      )}
    </Link>
  )
}
