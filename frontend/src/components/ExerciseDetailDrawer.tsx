import { useEffect, useState } from 'react'
import type { CSSProperties } from 'react'
import { X, Plus, ShieldAlert, Star, Link2, Repeat, Clock, Dumbbell } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { apiFetch } from '@/lib/apiFetch'
import type { Contraindication, Exercise, FeedbackSummaryItem } from '@/types'

const numStyle: CSSProperties = {
  fontFamily: 'var(--font-mono)',
  fontVariantNumeric: 'tabular-nums slashed-zero',
}

interface Props {
  exercise: Exercise | null
  allExercises: Exercise[]
  feedback?: FeedbackSummaryItem
  contraindication?: Contraindication
  safetyLensOn: boolean
  memberId?: string | null
  onClose: () => void
  onAdd: (exercise: Exercise) => void
  onSelectExercise: (exercise: Exercise) => void
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
      <span
        style={{
          fontSize: 'var(--text-2xs)',
          fontWeight: 'var(--weight-semibold)',
          letterSpacing: 'var(--tracking-caps)',
          textTransform: 'uppercase',
          color: 'var(--muted-foreground)',
        }}
      >
        {title}
      </span>
      {children}
    </div>
  )
}

function BadgeRow({ items, variant }: { items: string[]; variant: string }) {
  if (items.length === 0) return <span style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)' }}>—</span>
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-1-5)' }}>
      {items.map((i) => (
        <span key={i} className={`ww-badge ${variant}`}>{i}</span>
      ))}
    </div>
  )
}

export function ExerciseDetailDrawer({
  exercise,
  allExercises,
  feedback,
  contraindication,
  safetyLensOn,
  memberId,
  onClose,
  onAdd,
  onSelectExercise,
}: Props) {
  const { token } = useAuth()
  const [explanation, setExplanation] = useState<string | null>(null)
  const [loadingWhy, setLoadingWhy] = useState(false)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => { window.removeEventListener('keydown', onKey) }
  }, [onClose])

  if (!exercise) return null

  const flagged = safetyLensOn && contraindication != null
  const pair = exercise.bilateral_pair_id
    ? allExercises.find((e) => e.id === exercise.bilateral_pair_id)
    : undefined

  const handleWhy = async () => {
    if (!memberId) return
    setLoadingWhy(true)
    try {
      const res = await apiFetch('/api/kg/explain', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token ?? ''}` },
        body: JSON.stringify({ member_id: memberId, exercise_id: exercise.id }),
      })
      const data = (await res.json()) as { explanation: string }
      setExplanation(data.explanation)
    } catch {
      setExplanation('Could not load the full explanation right now.')
    } finally {
      setLoadingWhy(false)
    }
  }

  return (
    <div
      onClick={onClose}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 60,
        background: 'oklch(0 0 0 / 0.45)',
        display: 'flex',
        justifyContent: 'flex-end',
      }}
    >
      <div
        role="dialog"
        aria-label={`Exercise details: ${exercise.name}`}
        onClick={(e) => { e.stopPropagation() }}
        className="ww-card"
        style={{
          width: 460,
          maxWidth: '94vw',
          height: '100%',
          borderRadius: 'var(--radius-2xl) 0 0 var(--radius-2xl)',
          boxShadow: 'var(--shadow-xl)',
          overflowY: 'auto',
          animation: 'ww-drawer-in var(--dur-base) var(--ease-out)',
          gap: 'var(--space-5)',
          padding: 'var(--space-5)',
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 'var(--space-3)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
            <h2
              style={{
                margin: 0,
                fontFamily: 'var(--font-heading)',
                fontSize: 'var(--text-xl, var(--text-2xl))',
                fontWeight: 'var(--weight-semibold)',
                letterSpacing: 'var(--tracking-tight)',
              }}
            >
              {exercise.name}
            </h2>
            <code style={{ ...numStyle, fontSize: 'var(--text-2xs)', color: 'var(--muted-foreground)' }}>
              {exercise.id}
            </code>
          </div>
          <button type="button" className="ww-btn ww-btn--ghost ww-iconbtn" aria-label="Close" onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        {/* Tier + modality */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          <span className={`ww-badge ${exercise.priority_tier === 1 ? 'ww-badge--amber' : 'ww-badge--outline'}`}>
            Priority tier <span style={numStyle}>{exercise.priority_tier}</span>
          </span>
          {exercise.is_reps && <span style={{ display: 'inline-flex', gap: 'var(--space-1)', alignItems: 'center', fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}><Repeat size={13} /> Reps</span>}
          {exercise.is_duration && <span style={{ display: 'inline-flex', gap: 'var(--space-1)', alignItems: 'center', fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}><Clock size={13} /> Time</span>}
          {exercise.supports_weight && <span style={{ display: 'inline-flex', gap: 'var(--space-1)', alignItems: 'center', fontSize: 'var(--text-xs)', color: 'var(--muted-foreground)' }}><Dumbbell size={13} /> Weighted</span>}
        </div>

        {/* Safety lens */}
        {flagged && (
          <div
            style={{
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--danger-100)',
              color: 'var(--destructive)',
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-2)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', fontWeight: 'var(--weight-semibold)', fontSize: 'var(--text-sm)' }}>
              <ShieldAlert size={16} />
              Caution for you
            </div>
            <div style={{ fontSize: 'var(--text-sm)' }}>{contraindication.reason}</div>
            <div style={{ fontSize: 'var(--text-2xs)', opacity: 0.8 }}>
              Confidence <span style={numStyle}>{Math.round(contraindication.confidence * 100)}%</span>
            </div>
            {explanation ? (
              <div style={{ fontSize: 'var(--text-sm)', borderTop: '1px solid currentColor', paddingTop: 'var(--space-2)' }}>
                {explanation}
              </div>
            ) : (
              memberId && (
                <button
                  type="button"
                  className="ww-btn ww-btn--outline ww-btn--sm"
                  onClick={() => { void handleWhy() }}
                  disabled={loadingWhy}
                  style={{ alignSelf: 'flex-start' }}
                >
                  {loadingWhy ? 'Tracing graph…' : 'Why? (trace the graph)'}
                </button>
              )
            )}
          </div>
        )}

        {/* Coaching context */}
        {feedback && (
          <div
            style={{
              padding: 'var(--space-3)',
              borderRadius: 'var(--radius-md)',
              background: 'var(--amber-100)',
              color: 'var(--amber-800)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-sm)',
            }}
          >
            <Star size={16} fill="currentColor" />
            <span>
              You rated this <span style={{ ...numStyle, fontWeight: 'var(--weight-semibold)' }}>{feedback.avg_rating.toFixed(1)}</span>
              {' '}on average across <span style={numStyle}>{feedback.count}</span> rating{feedback.count === 1 ? '' : 's'}.
            </span>
          </div>
        )}

        {/* Description */}
        {exercise.description && (
          <Section title="About">
            <p style={{ margin: 0, fontSize: 'var(--text-sm)', lineHeight: 1.55, color: 'var(--foreground)' }}>
              {exercise.description}
            </p>
          </Section>
        )}

        <Section title="Muscle groups">
          <BadgeRow items={exercise.muscle_groups} variant="ww-badge--soft" />
        </Section>

        <Section title="Equipment">
          <BadgeRow items={exercise.equipment_required} variant="ww-badge--outline" />
        </Section>

        {exercise.joints_loaded.length > 0 && (
          <Section title="Joints loaded">
            <BadgeRow items={exercise.joints_loaded} variant="ww-badge--secondary" />
          </Section>
        )}

        <Section title="Movement pattern">
          <BadgeRow items={exercise.movement_patterns} variant="ww-badge--outline" />
        </Section>

        {pair && (
          <Section title="Bilateral pair">
            <button
              type="button"
              className="ww-btn ww-btn--outline ww-btn--sm"
              onClick={() => { onSelectExercise(pair) }}
              style={{ alignSelf: 'flex-start' }}
            >
              <Link2 size={14} />
              {pair.name}
            </button>
          </Section>
        )}

        {/* Footer action */}
        <button
          type="button"
          className="ww-btn ww-btn--gradient ww-btn--block"
          onClick={() => { onAdd(exercise) }}
          style={{ marginTop: 'var(--space-2)' }}
        >
          <Plus size={16} />
          Add to workout
        </button>
      </div>
    </div>
  )
}
