import { type SyntheticEvent, useState } from 'react'
import { useKGFeedback } from '@/hooks/useKGFeedback'
import { RatingWidget } from './RatingWidget'

interface FeedbackFormProps {
  exerciseId?: string
  memberId: string
  workoutId?: string
  workoutSetId?: string
  contextType?: 'exercise' | 'workout' | 'set'
  compact?: boolean
  onSuccess?: () => void
}

export function FeedbackForm({ exerciseId, memberId, workoutId, workoutSetId, contextType = 'exercise', compact = false, onSuccess }: FeedbackFormProps) {
  const [rating, setRating] = useState<1 | 2 | 3 | 4 | 5 | null>(null)
  const [text, setText] = useState('')
  const { mutate, isPending, isSuccess, isError, error } = useKGFeedback()

  function submit(v: 1 | 2 | 3 | 4 | 5, extraText?: string) {
    mutate(
      {
        member_id: memberId,
        exercise_id: exerciseId,
        rating: v,
        text: extraText?.trim() || undefined,
        workout_id: workoutId,
        workout_set_id: workoutSetId,
        context_type: contextType,
      },
      { onSuccess: () => { onSuccess?.() } },
    )
  }

  // Compact mode: single face button → popover picker, auto-submits on selection
  if (compact) {
    return (
      <RatingWidget
        value={rating}
        compact
        disabled={isPending || isSuccess}
        onChange={(v) => {
          setRating(v)
          submit(v)
        }}
      />
    )
  }

  // Expanded mode: full form with textarea
  if (isSuccess) {
    return (
      <div
        className="ww-card"
        style={{
          padding: 'var(--space-3)',
          color: 'var(--success)',
          fontSize: 'var(--text-sm)',
          textAlign: 'center',
        }}
      >
        Thank you for your feedback!
      </div>
    )
  }

  function handleSubmit(e: SyntheticEvent) {
    e.preventDefault()
    if (rating === null) return
    submit(rating, text)
  }

  return (
    <form onSubmit={handleSubmit} className="ww-card" style={{ padding: 'var(--space-3)' }}>
      <div
        style={{
          fontSize: 'var(--text-sm)',
          fontWeight: 'var(--weight-semibold)',
          marginBottom: 'var(--space-2)',
        }}
      >
        Rate this exercise
      </div>

      <div style={{ marginBottom: 'var(--space-2)' }}>
        <RatingWidget value={rating} onChange={setRating} disabled={isPending} />
      </div>

      <textarea
        value={text}
        onChange={(e) => { setText(e.target.value) }}
        disabled={isPending}
        placeholder="Optional feedback…"
        rows={3}
        className="ww-input"
        style={{ width: '100%', resize: 'vertical', marginBottom: 'var(--space-2)', fontSize: 'var(--text-sm)' }}
      />

      {isError && (
        <div style={{ color: 'var(--destructive)', fontSize: 'var(--text-xs)', marginBottom: 'var(--space-2)' }}>
          {error instanceof Error ? error.message : 'Submission failed. Please try again.'}
        </div>
      )}

      <button
        type="submit"
        disabled={rating === null || isPending}
        className="ww-btn ww-btn--primary"
        style={{ width: '100%' }}
      >
        {isPending ? 'Submitting…' : 'Submit Feedback'}
      </button>
    </form>
  )
}
