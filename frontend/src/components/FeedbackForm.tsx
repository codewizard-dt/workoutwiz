import { useState } from 'react'
import { cn } from '@/lib/utils'
import { useKGFeedback } from '@/hooks/useKGFeedback'

interface FeedbackFormProps {
  exerciseId: string
  memberId: string
  onSuccess?: () => void
}

export function FeedbackForm({ exerciseId, memberId, onSuccess }: FeedbackFormProps) {
  const [rating, setRating] = useState<number | null>(null)
  const [hovered, setHovered] = useState<number | null>(null)
  const [text, setText] = useState('')
  const { mutate, isPending, isSuccess, isError, error } = useKGFeedback()

  function handleSubmit(e: React.SyntheticEvent) {
    e.preventDefault()
    if (rating === null) return
    mutate(
      { member_id: memberId, exercise_id: exerciseId, rating, text: text.trim() || undefined },
      {
        onSuccess: () => {
          onSuccess?.()
        },
      },
    )
  }

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

  const displayRating = hovered ?? rating

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

      {/* Star rating */}
      <div
        role="group"
        aria-label="Star rating"
        style={{ display: 'flex', gap: 'var(--space-1)', marginBottom: 'var(--space-2)' }}
      >
        {([1, 2, 3, 4, 5] as const).map((n) => (
          <button
            key={n}
            type="button"
            aria-label={`Rate ${n} out of 5`}
            aria-pressed={rating === n}
            disabled={isPending}
            onClick={() => { setRating(n) }}
            onMouseEnter={() => { setHovered(n) }}
            onMouseLeave={() => { setHovered(null) }}
            className={cn(
              'ww-btn ww-btn--ghost ww-iconbtn',
              displayRating !== null && n <= displayRating && 'ww-btn--accent',
            )}
            style={{
              fontSize: '1.5rem',
              opacity: isPending ? 0.5 : displayRating !== null && n <= displayRating ? 1 : 0.4,
              transition: 'opacity var(--dur-fast) var(--ease-out)',
            }}
          >
            ★
          </button>
        ))}
      </div>

      {/* Optional text */}
      <textarea
        value={text}
        onChange={(e) => { setText(e.target.value) }}
        disabled={isPending}
        placeholder="Optional feedback…"
        rows={3}
        className="ww-input"
        style={{
          width: '100%',
          resize: 'vertical',
          marginBottom: 'var(--space-2)',
          fontSize: 'var(--text-sm)',
        }}
      />

      {/* Error */}
      {isError && (
        <div
          style={{
            color: 'var(--destructive)',
            fontSize: 'var(--text-xs)',
            marginBottom: 'var(--space-2)',
          }}
        >
          {error instanceof Error ? error.message : 'Submission failed. Please try again.'}
        </div>
      )}

      {/* Submit */}
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
