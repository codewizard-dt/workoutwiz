import { Dumbbell, Repeat, Clock, Star, ShieldAlert, Plus } from 'lucide-react'
import type { CSSProperties } from 'react'
import type { Contraindication, Exercise, FeedbackSummaryItem } from '@/types'

const numStyle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontVariantNumeric: 'tabular-nums slashed-zero',
}

interface ExerciseCardProps {
  exercise: Exercise
  feedback?: FeedbackSummaryItem
  contraindication?: Contraindication
  safetyLensOn: boolean
  onOpen: (exercise: Exercise) => void
  onAdd: (exercise: Exercise) => void
}

function ModalityChip({ icon, label }: { icon: React.ReactNode; label: string }) {
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 'var(--space-1)',
        fontSize: 'var(--text-2xs)',
        color: 'var(--muted-foreground)',
      }}
    >
      {icon}
      {label}
    </span>
  )
}

export function ExerciseCard({
  exercise,
  feedback,
  contraindication,
  safetyLensOn,
  onOpen,
  onAdd,
}: ExerciseCardProps) {
  const flagged = safetyLensOn && contraindication != null
  const muscles = exercise.muscle_groups
  const pattern = exercise.movement_patterns.length > 0
    ? exercise.movement_patterns[0]
    : (exercise.category ?? '')

  return (
    <div
      className="ww-card ww-card--interactive"
      role="button"
      tabIndex={0}
      data-testid="exercise-card"
      onClick={() => { onOpen(exercise) }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          onOpen(exercise)
        }
      }}
      style={{
        padding: 'var(--space-4)',
        gap: 'var(--space-3)',
        opacity: flagged ? 0.72 : 1,
        boxShadow: flagged
          ? 'inset 0 0 0 1px var(--danger-300, var(--destructive)), var(--shadow-sm)'
          : undefined,
      }}
    >
      {/* Header: pattern eyebrow + tier / caution */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-2)' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)', minWidth: 0 }}>
          {pattern && (
            <span
              style={{
                fontSize: 'var(--text-2xs)',
                fontWeight: 'var(--weight-semibold)',
                letterSpacing: 'var(--tracking-caps)',
                textTransform: 'uppercase',
                color: 'var(--muted-foreground)',
              }}
            >
              {pattern}
            </span>
          )}
          <h3
            style={{
              margin: 0,
              fontFamily: 'var(--font-heading)',
              fontSize: 'var(--text-md)',
              fontWeight: 'var(--weight-semibold)',
              letterSpacing: 'var(--tracking-tight)',
              lineHeight: 1.2,
            }}
          >
            {exercise.name}
          </h3>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 'var(--space-1)', flexShrink: 0 }}>
          {flagged ? (
            <span className="ww-badge ww-badge--danger">
              <ShieldAlert />
              Caution
            </span>
          ) : (
            <span className={`ww-badge ${exercise.priority_tier === 1 ? 'ww-badge--amber' : 'ww-badge--outline'}`}>
              Tier <span style={numStyle}>{exercise.priority_tier}</span>
            </span>
          )}
        </div>
      </div>

      {/* Muscle groups */}
      {muscles.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>
          {muscles.slice(0, 3).map((m) => (
            <span key={m} className="ww-badge ww-badge--soft">{m}</span>
          ))}
          {muscles.length > 3 && (
            <span className="ww-badge ww-badge--outline">+{muscles.length - 3}</span>
          )}
        </div>
      )}

      {/* Equipment */}
      <div style={{ fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}>
        {exercise.equipment_required.length > 0
          ? exercise.equipment_required.join(' · ')
          : 'No equipment'}
      </div>

      {/* Modality + feedback */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
        {exercise.is_reps && <ModalityChip icon={<Repeat size={13} />} label="Reps" />}
        {exercise.is_duration && <ModalityChip icon={<Clock size={13} />} label="Time" />}
        {exercise.supports_weight && <ModalityChip icon={<Dumbbell size={13} />} label="Weighted" />}
        {feedback && (
          <span
            title={`You rated this ${feedback.count} time${feedback.count === 1 ? '' : 's'}`}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: 'var(--space-1)',
              fontSize: 'var(--text-2xs)',
              color: 'var(--amber-700)',
            }}
          >
            <Star size={13} fill="currentColor" />
            <span style={numStyle}>{feedback.avg_rating.toFixed(1)}</span>
            <span style={{ color: 'var(--muted-foreground)' }}>
              (<span style={numStyle}>{feedback.count}</span>)
            </span>
          </span>
        )}
      </div>

      {/* Footer: id + add */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 'var(--space-2)', marginTop: 'auto' }}>
        <code
          title={exercise.id}
          style={{ ...numStyle, fontSize: 'var(--text-2xs)', color: 'var(--muted-foreground)' }}
        >
          #{exercise.id.slice(0, 8)}
        </code>
        <button
          type="button"
          className="ww-btn ww-btn--gradient ww-btn--sm"
          onClick={(e) => { e.stopPropagation(); onAdd(exercise) }}
        >
          <Plus size={14} />
          Add
        </button>
      </div>
    </div>
  )
}
