import { useState, useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useWorkout, useUpdateWorkout } from '../hooks/useWorkouts'
import { useDraftWorkout } from '@/hooks/useDraftWorkout'
import { useExercises } from '../hooks/useExercises'
import { RatingWidget } from '@/components/RatingWidget'
import { PhaseTable } from '@/components/PhaseTable'
import { ArrowLeft } from 'lucide-react'
import { useMe } from '@/hooks'

export default function WorkoutDetailPage() {
  const { workoutId } = useParams<{ workoutId: string }>()

  const {
    data: workout,
    isLoading,
    isError,
    error,
  } = useWorkout(workoutId ?? '')

  const { data: exercises = [] } = useExercises()
  const updateWorkout = useUpdateWorkout()
  const { addExercise: addToDraft } = useDraftWorkout()
  const { data: user } = useMe()

  const [enjoyment, setEnjoyment] = useState<1 | 2 | 3 | 4 | 5>(3)
  const [note, setNote] = useState('')
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (workout) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      if (workout.enjoyment) setEnjoyment(workout.enjoyment as 1 | 2 | 3 | 4 | 5)
      if (workout.note != null) setNote(workout.note)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [workout?.id])

  // Debounced auto-save for enjoyment and note changes
  useEffect(() => {
    if (!workout) return
    const timer = setTimeout(() => {
      // Metadata-only: never resend sequences/sets, or the backend would
      // delete+recreate every set (new PKs) and null out per-set feedback.
      updateWorkout.mutate(
        { id: workout.id, data: { enjoyment, note } },
        { onSuccess: () => { setSaved(true); setTimeout(() => { setSaved(false) }, 2000) } },
      )
    }, 300)
    return () => { clearTimeout(timer) }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enjoyment, note])

  function formatDateTime(iso: string | null) {
    if (!iso) return '—'
    return new Date(iso).toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  // --- Loading state ---
  if (isLoading) {
    return (
      <div
        style={{
          padding: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
        }}
      >
        <Link
          to="/workouts"
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            textDecoration: 'none',
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-1)',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ArrowLeft size={14} aria-hidden /> Workouts</span>
        </Link>
        {/* Skeleton header */}
        <div
          style={{
            height: '2rem',
            width: '40%',
            borderRadius: 'var(--radius-md)',
            background: 'var(--muted)',
            opacity: 0.6,
          }}
        />
        {/* Skeleton table */}
        <div
          style={{
            height: '200px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--muted)',
            opacity: 0.4,
          }}
        />
      </div>
    )
  }

  // --- Error state ---
  if (isError) {
    const is404 =
      error instanceof Error && error.message.toLowerCase().includes('404')

    return (
      <div
        style={{
          padding: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
        }}
      >
        <Link
          to="/workouts"
          style={{
            fontSize: 'var(--text-sm)',
            color: 'var(--muted-foreground)',
            textDecoration: 'none',
          }}
        >
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ArrowLeft size={14} aria-hidden /> Workouts</span>
        </Link>
        <div
          style={{
            padding: 'var(--space-6)',
            borderRadius: 'var(--radius-lg)',
            border: '1px solid var(--border)',
            display: 'flex',
            flexDirection: 'column',
            gap: 'var(--space-3)',
            alignItems: 'flex-start',
          }}
        >
          <h2
            style={{
              fontSize: 'var(--text-xl)',
              fontWeight: 'var(--weight-semibold)',
              margin: 0,
            }}
          >
            {is404 ? 'Workout not found' : 'Failed to load workout'}
          </h2>
          <p style={{ color: 'var(--muted-foreground)', margin: 0, fontSize: 'var(--text-sm)' }}>
            {is404
              ? "We couldn't find that session — it may have been deleted."
              : 'There was a problem loading this workout. Please try again.'}
          </p>
          <Link
            to="/workouts"
            style={{ fontSize: 'var(--text-sm)', color: 'var(--foreground)', textDecoration: 'underline' }}
          >
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ArrowLeft size={14} aria-hidden /> Back to workouts</span>
          </Link>
        </div>
      </div>
    )
  }

  // --- Not found (workout is undefined after load) ---
  if (!workout) {
    return (
      <div style={{ padding: 'var(--space-6)', display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
        <Link to="/workouts" style={{ fontSize: 'var(--text-sm)', color: 'var(--muted-foreground)', textDecoration: 'none' }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ArrowLeft size={14} aria-hidden /> Workouts</span>
        </Link>
        <p style={{ color: 'var(--muted-foreground)', fontSize: 'var(--text-sm)' }}>
          Workout not found.{' '}
          <Link to="/workouts" style={{ color: 'var(--foreground)', textDecoration: 'underline' }}>
            Back to workouts
          </Link>
        </p>
      </div>
    )
  }

  // --- Loaded state ---
  return (
    <div
      style={{
        padding: 'var(--space-6)',
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-5)',
        maxWidth: '1100px',
        width: '100%',
        margin: '0 auto',
      }}
    >
      {/* Back navigation */}
      <Link
        to="/workouts"
        style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--muted-foreground)',
          textDecoration: 'none',
          display: 'inline-flex',
          alignItems: 'center',
          gap: 'var(--space-1)',
          alignSelf: 'flex-start',
        }}
      >
        <span style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}><ArrowLeft size={14} aria-hidden /> Workouts</span>
      </Link>

      {/* Header row: title + Replay All */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 'var(--space-4)',
          flexWrap: 'wrap',
        }}
      >
        <h1
          style={{
            fontSize: 'var(--text-2xl)',
            fontWeight: 'var(--weight-bold)',
            letterSpacing: '-0.025em',
            margin: 0,
          }}
        >
          {workout.started_at
            ? `Workout · ${new Date(workout.started_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}`
            : 'Workout Details'}
        </h1>
      </div>

      {/* Metadata row */}
      <div
        style={{
          display: 'flex',
          gap: 'var(--space-6)',
          flexWrap: 'wrap',
        }}
      >
        <div>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--weight-semibold)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--tracking-caps)',
              color: 'var(--muted-foreground)',
              marginBottom: 'var(--space-1)',
            }}
          >
            Started
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--foreground)' }}>
            {formatDateTime(workout.started_at)}
          </div>
        </div>
        <div>
          <div
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--weight-semibold)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--tracking-caps)',
              color: 'var(--muted-foreground)',
              marginBottom: 'var(--space-1)',
            }}
          >
            Ended
          </div>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--foreground)' }}>
            {formatDateTime(workout.ended_at)}
          </div>
        </div>
      </div>

      {/* Enjoyment + Note card */}
      <div
        className="ww-card"
        style={{
          padding: 'var(--space-4)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-4)',
          border: '1px solid var(--ember-200)',
          boxShadow: 'var(--ring-card), var(--shadow-md), 0 6px 24px oklch(0.645 0.190 38 / 0.10)',
        }}
      >
        {/* Enjoyment */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <label
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--weight-semibold)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--tracking-caps)',
              color: 'var(--ember-600)',
            }}
          >
            Feels
          </label>
          <RatingWidget
            value={enjoyment}
            onChange={(v) => { setEnjoyment(v) }}
          />
        </div>

        {/* Note */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          <label
            htmlFor="workout-note"
            style={{
              fontSize: 'var(--text-xs)',
              fontWeight: 'var(--weight-semibold)',
              textTransform: 'uppercase',
              letterSpacing: 'var(--tracking-caps)',
              color: 'var(--ember-600)',
            }}
          >
            Note
          </label>
          <textarea
            id="workout-note"
            rows={2}
            placeholder="Optional note about how this workout felt..."
            value={note}
            onChange={(e) => { setNote(e.target.value) }}
            style={{
              resize: 'vertical',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              padding: 'var(--space-2) var(--space-3)',
              fontSize: 'var(--text-sm)',
              background: 'var(--surface-sunken)',
              color: 'var(--foreground)',
              fontFamily: 'inherit',
              lineHeight: 1.5,
              outline: 'none',
              width: '100%',
              boxSizing: 'border-box',
            }}
          />
        </div>
        {saved && (
          <p style={{ margin: 0, fontSize: 'var(--text-xs)', color: 'var(--success)', animation: 'fadeIn 0.15s ease' }}>
            ✓ Saved
          </p>
        )}
      </div>

      {/* Phase tables */}
      <PhaseTable
        sequences={workout.sequences}
        exercises={exercises}
        memberId={user?.id}
        workoutId={workout.id}
        onAddCurrent={(exerciseId) => {
          const ex = exercises.find((e) => e.id === exerciseId)
          addToDraft(exerciseId, !!ex?.is_duration && !ex.is_reps)
        }}
      />
    </div>
  )
}
